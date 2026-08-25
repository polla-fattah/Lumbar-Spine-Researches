#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Run-mode infrastructure for AMOG-Net: SMOKE and REAL.

WHY TWO MODES
-------------
The intent is to verify the pipeline works on a modest machine before committing
a real run to a larger one. That is sound practice, and this module implements it.

THE ONE RULE THAT MAKES A SMOKE TEST WORTH ANYTHING
---------------------------------------------------
Both modes execute the *same training step*. Only two things differ:

    - where the tensors come from (synthetic vs real ROI pixels)
    - how much work is done (2 epochs on 64 samples vs the full schedule)

A smoke test exists to prove the machinery runs: that the forward pass shapes
line up, the loss is finite, gradients flow, the optimizer steps, the checkpoint
saves and reloads, and the metric functions accept real predictions. If the smoke
path skips the training step, or writes results it did not compute, it proves
none of that — it becomes a program that prints a number, and it will report
success on a pipeline that is completely broken.

So in this module:

    - metrics are ALWAYS computed from predictions, in both modes. There is no
      code path that assigns a result a literal.
    - a smoke run scoring 33% on three random classes is a PASS. That is the
      correct outcome and it is not a defect. What is being tested is the
      plumbing, not the accuracy.
    - smoke output is written to data/smoke/ and never to data/reports/, and
      every artefact carries a provenance stamp naming the mode that produced it.
      A smoke number cannot be mistaken later for a result.

USAGE
-----
    from amog_modes import add_mode_args, resolve_mode, compute_metrics

    ap = argparse.ArgumentParser()
    add_mode_args(ap)
    ctx = resolve_mode(ap.parse_args())

    ctx.log_dir / ctx.report_dir / ctx.checkpoint_dir   # already created
    ctx.is_smoke                                        # bool
    metrics = compute_metrics(y_true, y_pred, y_prob)   # real, always
"""

from __future__ import annotations

import json
import os
import platform
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime

import numpy as np

SMOKE = "smoke"
REAL = "real"

_HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(_HERE)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Chapter 3: severity is three ordinal grades, Normal/Mild < Moderate < Severe.
CLASS_NAMES = ["Normal/Mild", "Moderate", "Severe"]
N_CLASSES = len(CLASS_NAMES)

# Chapter 3: 5 lumbar levels x 5 conditions.
LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]
CONDITIONS = ["left_foraminal", "left_subarticular", "central_canal",
              "right_subarticular", "right_foraminal"]
N_TARGETS = len(LUMBAR_LEVELS) * len(CONDITIONS)   # 25


# --------------------------------------------------------------------------- #
#  mode context
# --------------------------------------------------------------------------- #
@dataclass
class ModeContext:
    mode: str
    epochs: int
    batch_size: int
    lr: float
    max_samples: int | None          # cap on dataset size; None means all
    device: str
    log_dir: str
    report_dir: str
    checkpoint_dir: str
    derived_dir: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_smoke(self) -> bool:
        return self.mode == SMOKE

    @property
    def is_real(self) -> bool:
        return self.mode == REAL

    def banner(self) -> str:
        if self.is_smoke:
            return (
                "  MODE: SMOKE  --  pipeline self-test on synthetic tensors.\n"
                "  Numbers produced here are NOT results and must never be cited.\n"
                "  A low score is expected and is a PASS: what is under test is\n"
                "  whether the machinery runs, not how well the model performs."
            )
        return (
            "  MODE: REAL  --  training on the actual cohort.\n"
            "  Outputs land in data/reports/ and are citable only if\n"
            "  99_audit/verify_integrity.py passes on this tree."
        )

    def stamp(self) -> dict:
        """Provenance recorded inside every artefact this run writes."""
        return {
            "amog_mode": self.mode,
            "is_citable": self.is_real,
            "warning": None if self.is_real else
                       "SMOKE RUN - synthetic data - NOT A RESULT",
            "started_at": self.started_at,
            "device": self.device,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "max_samples": self.max_samples,
            "git_commit": _git_commit(),
            "host": platform.node(),
            "python": platform.python_version(),
        }

    def write_json(self, name: str, payload: dict) -> str:
        """Write a JSON artefact with the provenance stamp merged in."""
        out = {"_provenance": self.stamp()}
        out.update(payload)
        path = os.path.join(self.derived_dir, name)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=2)
        return path


def _git_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=PROJECT_ROOT, stderr=subprocess.DEVNULL,
        ).decode().strip()
    except Exception:
        return "unknown"


def add_mode_args(parser) -> None:
    """Attach the standard mode flags to any stage script."""
    parser.add_argument(
        "--mode", choices=[SMOKE, REAL], default=os.environ.get("AMOG_MODE", SMOKE),
        help="smoke = synthetic self-test (default, safe); real = train on the cohort")
    parser.add_argument("--epochs", type=int, default=None,
                        help="override the per-mode default epoch count")
    parser.add_argument("--batch_size", type=int, default=None)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--max_samples", type=int, default=None,
                        help="cap dataset size; useful for a fast partial real run")
    parser.add_argument("--device", type=str, default=None,
                        help="cuda | cpu (default: cuda when available)")


def resolve_mode(args) -> ModeContext:
    """Build the run context and create its output directories."""
    try:
        import torch
        default_device = "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        default_device = "cpu"

    mode = args.mode
    if mode == SMOKE:
        epochs = args.epochs if args.epochs is not None else 2
        batch = args.batch_size if args.batch_size is not None else 8
        cap = args.max_samples if args.max_samples is not None else 64
        root = os.path.join(DATA_DIR, "smoke")
        log_dir = os.path.join(root, "logs")
        report_dir = os.path.join(root, "reports")
        ckpt_dir = os.path.join(root, "checkpoints")
        derived_dir = os.path.join(root, "derived")
    else:
        epochs = args.epochs if args.epochs is not None else 50
        batch = args.batch_size if args.batch_size is not None else 32
        cap = args.max_samples
        log_dir = os.path.join(DATA_DIR, "logs")
        report_dir = os.path.join(DATA_DIR, "reports")
        ckpt_dir = os.path.join(DATA_DIR, "checkpoints")
        derived_dir = os.path.join(DATA_DIR, "derived")

    for d in (log_dir, report_dir, ckpt_dir, derived_dir):
        os.makedirs(d, exist_ok=True)

    ctx = ModeContext(
        mode=mode, epochs=epochs, batch_size=batch, lr=args.lr,
        max_samples=cap, device=args.device or default_device,
        log_dir=log_dir, report_dir=report_dir,
        checkpoint_dir=ckpt_dir, derived_dir=derived_dir,
    )

    print("=" * 74)
    print(ctx.banner())
    print("=" * 74)
    print("  device       : {}".format(ctx.device))
    print("  epochs       : {}   batch: {}   lr: {}".format(ctx.epochs, ctx.batch_size, ctx.lr))
    print("  outputs      : {}".format(os.path.relpath(report_dir, PROJECT_ROOT)))
    print()
    return ctx


# --------------------------------------------------------------------------- #
#  metrics -- always computed, never assigned
# --------------------------------------------------------------------------- #
def compute_metrics(y_true, y_pred, y_prob=None, n_classes: int = N_CLASSES) -> dict:
    """Real metrics from real predictions.

    Nothing here is derived by scaling another metric. Quadratic weighted kappa
    comes from the weighted confusion matrix, because the grades are ordinal and
    a Severe->Normal/Mild confusion must not cost the same as an adjacent-grade
    one. Expected Calibration Error is binned from the predicted probabilities.
    """
    y_true = np.asarray(y_true).ravel()
    y_pred = np.asarray(y_pred).ravel()
    if y_true.size == 0:
        raise ValueError("compute_metrics called with no predictions")

    out: dict = {"n_samples": int(y_true.size)}
    out["accuracy"] = float((y_true == y_pred).mean())

    # confusion matrix
    cm = np.zeros((n_classes, n_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        if 0 <= t < n_classes and 0 <= p < n_classes:
            cm[t, p] += 1
    out["confusion_matrix"] = cm.tolist()

    # per-class precision / recall / F1, then macro
    f1s, per_class = [], {}
    for k in range(n_classes):
        tp = int(cm[k, k])
        fp = int(cm[:, k].sum() - tp)
        fn = int(cm[k, :].sum() - tp)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        f1s.append(f1)
        per_class[CLASS_NAMES[k] if k < len(CLASS_NAMES) else str(k)] = {
            "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(f1, 4), "support": int(cm[k, :].sum()),
        }
    out["macro_f1"] = float(np.mean(f1s))
    out["per_class"] = per_class

    # quadratic weighted kappa
    out["qwk"] = float(_quadratic_weighted_kappa(cm, n_classes))

    # ordinal error distances -- Chapter 3 reports d=0,1,2 separately
    dist = np.abs(y_true - y_pred)
    out["grade_distance"] = {
        "d0": float((dist == 0).mean()),
        "d1": float((dist == 1).mean()),
        "d2_or_more": float((dist >= 2).mean()),
    }

    # the clinically decisive error: Severe graded as Normal/Mild
    severe = n_classes - 1
    n_severe = int((y_true == severe).sum())
    if n_severe:
        out["severe_recall"] = float((y_pred[y_true == severe] == severe).mean())
        out["severe_to_normal_rate"] = float((y_pred[y_true == severe] == 0).mean())
    else:
        out["severe_recall"] = None
        out["severe_to_normal_rate"] = None

    if y_prob is not None:
        y_prob = np.asarray(y_prob)
        out["ece"] = float(_expected_calibration_error(y_true, y_prob))
        out["brier"] = float(_brier(y_true, y_prob, n_classes))
    else:
        out["ece"] = None
        out["brier"] = None

    return out


def _quadratic_weighted_kappa(cm: np.ndarray, k: int) -> float:
    if cm.sum() == 0:
        return 0.0
    w = np.zeros((k, k), dtype=np.float64)
    for i in range(k):
        for j in range(k):
            w[i, j] = ((i - j) ** 2) / ((k - 1) ** 2) if k > 1 else 0.0
    obs = cm.astype(np.float64) / cm.sum()
    row = obs.sum(axis=1, keepdims=True)
    col = obs.sum(axis=0, keepdims=True)
    exp = row @ col
    denom = float((w * exp).sum())
    if denom == 0:
        return 0.0
    return 1.0 - float((w * obs).sum()) / denom


def _expected_calibration_error(y_true, y_prob, n_bins: int = 15) -> float:
    conf = y_prob.max(axis=1)
    pred = y_prob.argmax(axis=1)
    correct = (pred == y_true).astype(np.float64)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.sum():
            ece += (m.sum() / n) * abs(correct[m].mean() - conf[m].mean())
    return ece


def _brier(y_true, y_prob, k: int) -> float:
    onehot = np.zeros_like(y_prob)
    onehot[np.arange(len(y_true)), y_true] = 1.0
    return float(((y_prob - onehot) ** 2).sum(axis=1).mean())


# --------------------------------------------------------------------------- #
#  guard
# --------------------------------------------------------------------------- #
def assert_not_smoke(ctx: ModeContext, action: str) -> None:
    """Refuse an action that would present smoke output as a result."""
    if ctx.is_smoke:
        raise RuntimeError(
            "refusing to {} during a SMOKE run.\n"
            "Smoke output is a self-test, not a result. Re-run with --mode real."
            .format(action))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Inspect the resolved run mode")
    add_mode_args(ap)
    ctx = resolve_mode(ap.parse_args())
    print(json.dumps(ctx.stamp(), indent=2))
    print()
    rng = np.random.default_rng(0)
    yt = rng.integers(0, 3, 300)
    yp = np.where(rng.random(300) < 0.6, yt, rng.integers(0, 3, 300))
    pr = rng.dirichlet(np.ones(3), 300)
    m = compute_metrics(yt, yp, pr)
    print("self-test of the metric functions on synthetic predictions:")
    print("  accuracy {:.3f}  macro_f1 {:.3f}  qwk {:.3f}  ece {:.3f}"
          .format(m["accuracy"], m["macro_f1"], m["qwk"], m["ece"]))
