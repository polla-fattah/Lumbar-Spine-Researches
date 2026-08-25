#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
E0 baseline ROI classifier -- reference implementation of the SMOKE / REAL modes.

This is the pattern the other stages should follow. It replaces
train_and_evaluate_e0_baselines.py, which fitted torch.randn noise in its only
code path and then reported metrics obtained by multiplying accuracy by a
constant.

WHAT MAKES THE SMOKE MODE MEANINGFUL
------------------------------------
Both modes call the identical train_one_epoch() and evaluate(). The only
differences are where tensors come from and how many there are:

    smoke : SyntheticROIDataset  -- random tensors, 64 samples, 2 epochs
    real  : RSNAROIDataset       -- DICOM pixels cropped at annotated keypoints

So the smoke path exercises the real forward pass, the real loss, the real
backward pass, the real optimizer step, the real checkpoint round-trip and the
real metric functions. If any of those is broken, smoke mode fails -- which is
the entire point of running it first.

A smoke run scores near chance (about 33% on three classes). That is a PASS.
Accuracy is not what is being tested.

DATA (real mode)
----------------
RSNA 2024 Lumbar Spine Degenerative Classification:
  train.csv                      study_id + 25 severity columns
  train_label_coordinates.csv    study_id, series_id, instance_number,
                                 condition, level, x, y
  train_series_descriptions.csv  study_id, series_id, series_description
  train_images/<study>/<series>/<instance>.dcm

One ROI = a 2.5D stack of three neighbouring slices, cropped around the
annotated (x, y) keypoint, labelled by the matching severity column.

USAGE
-----
    python train_e0_twomode.py --mode smoke
    python train_e0_twomode.py --mode real --rsna_dir <path> --epochs 50
    python train_e0_twomode.py --mode real --max_samples 2000   # partial run
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_modes import (  # noqa: E402
    add_mode_args, resolve_mode, compute_metrics,
    CLASS_NAMES, N_CLASSES, PROJECT_ROOT,
)
from dataset_config import resolve_dataset_dir, DEFAULT_HINTS_RSNA  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CROP = 128
SEVERITY_TO_INDEX = {"Normal/Mild": 0, "Moderate": 1, "Severe": 2}


# --------------------------------------------------------------------------- #
#  datasets
# --------------------------------------------------------------------------- #
class SyntheticROIDataset(Dataset):
    """Random tensors with the shape and label space of the real thing.

    Used only by smoke mode. Deliberately labelled so that any artefact derived
    from it is traceable back to synthetic input.
    """

    is_synthetic = True

    def __init__(self, n: int = 64, seed: int = 0):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.randn(n, 3, CROP, CROP, generator=g)
        self.y = torch.randint(0, N_CLASSES, (n,), generator=g)

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        return self.x[i], self.y[i]


class RSNAROIDataset(Dataset):
    """Real 2.5D ROI crops from RSNA DICOM at annotated keypoints."""

    is_synthetic = False

    def __init__(self, rsna_dir: str, index: pd.DataFrame, crop: int = CROP):
        self.rsna_dir = rsna_dir
        self.rows = index.reset_index(drop=True)
        self.crop = crop
        self._images = os.path.join(rsna_dir, "train_images")

    def __len__(self):
        return len(self.rows)

    def _load_slice(self, study, series, instance):
        path = os.path.join(self._images, str(study), str(series), "{}.dcm".format(instance))
        if not os.path.exists(path):
            return None
        try:
            import pydicom
            dcm = pydicom.dcmread(path)
            arr = dcm.pixel_array.astype(np.float32)
        except Exception:
            return None
        lo, hi = np.percentile(arr, [1, 99])
        if hi <= lo:
            hi = lo + 1.0
        return np.clip((arr - lo) / (hi - lo), 0.0, 1.0)

    def __getitem__(self, i):
        r = self.rows.iloc[i]
        study, series, inst = int(r.study_id), int(r.series_id), int(r.instance_number)

        # 2.5D: the annotated slice plus its two neighbours, falling back to a
        # repeat of the centre slice at the ends of a stack.
        planes = []
        centre = self._load_slice(study, series, inst)
        if centre is None:
            return torch.zeros(3, self.crop, self.crop), torch.tensor(int(r.label))
        for off in (-1, 0, 1):
            s = centre if off == 0 else self._load_slice(study, series, inst + off)
            planes.append(centre if s is None or s.shape != centre.shape else s)

        h, w = centre.shape
        cx = int(round(float(r.x)))
        cy = int(round(float(r.y)))
        half = self.crop // 2
        x0, y0 = max(0, cx - half), max(0, cy - half)
        x1, y1 = min(w, x0 + self.crop), min(h, y0 + self.crop)
        x0, y0 = max(0, x1 - self.crop), max(0, y1 - self.crop)

        out = np.zeros((3, self.crop, self.crop), dtype=np.float32)
        for c, p in enumerate(planes):
            patch = p[y0:y1, x0:x1]
            out[c, : patch.shape[0], : patch.shape[1]] = patch

        return torch.from_numpy(out), torch.tensor(int(r.label))


def build_rsna_index(rsna_dir: str, max_samples: int | None = None) -> pd.DataFrame:
    """Join keypoint coordinates to their severity labels."""
    coords = pd.read_csv(os.path.join(rsna_dir, "train_label_coordinates.csv"))
    labels = pd.read_csv(os.path.join(rsna_dir, "train.csv"))

    def column_for(row):
        cond = str(row["condition"]).strip().lower().replace(" ", "_")
        lvl = str(row["level"]).strip().lower().replace("/", "_")
        return "{}_{}".format(cond, lvl)

    coords["target_col"] = coords.apply(column_for, axis=1)
    label_long = labels.set_index("study_id")

    keep = []
    for _, r in coords.iterrows():
        col = r["target_col"]
        if col not in label_long.columns:
            continue
        try:
            sev = label_long.at[int(r["study_id"]), col]
        except KeyError:
            continue
        if not isinstance(sev, str) or sev not in SEVERITY_TO_INDEX:
            continue
        keep.append({
            "study_id": int(r["study_id"]), "series_id": int(r["series_id"]),
            "instance_number": int(r["instance_number"]),
            "x": float(r["x"]), "y": float(r["y"]),
            "condition": r["condition"], "level": r["level"],
            "label": SEVERITY_TO_INDEX[sev],
        })

    idx = pd.DataFrame(keep)
    if max_samples and len(idx) > max_samples:
        idx = idx.sample(n=max_samples, random_state=42).reset_index(drop=True)
    return idx


def patient_level_split(index: pd.DataFrame, seed: int = 42):
    """Split on study_id so no patient appears on both sides (Chapter 3)."""
    rng = np.random.default_rng(seed)
    patients = np.array(sorted(index["study_id"].unique()))
    rng.shuffle(patients)
    n = len(patients)
    tr, va = int(0.70 * n), int(0.85 * n)
    sets = (set(patients[:tr]), set(patients[tr:va]), set(patients[va:]))
    assert not (sets[0] & sets[1]) and not (sets[0] & sets[2]) and not (sets[1] & sets[2])
    return [index[index.study_id.isin(s)].reset_index(drop=True) for s in sets]


# --------------------------------------------------------------------------- #
#  model
# --------------------------------------------------------------------------- #
def build_model(name: str, n_classes: int = N_CLASSES) -> nn.Module:
    """Real torchvision backbones. If a name is unavailable, fail loudly.

    The previous implementation listed four architectures and built the same
    five-layer CNN for all of them, then reported a hardcoded parameter count.
    """
    import torchvision.models as tvm

    name = name.lower()
    if name == "resnet50":
        m = tvm.resnet50(weights=None)
        m.fc = nn.Linear(m.fc.in_features, n_classes)
    elif name == "convnext_tiny":
        m = tvm.convnext_tiny(weights=None)
        m.classifier[2] = nn.Linear(m.classifier[2].in_features, n_classes)
    elif name == "swin_t":
        m = tvm.swin_t(weights=None)
        m.head = nn.Linear(m.head.in_features, n_classes)
    elif name == "smallcnn":
        m = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, n_classes),
        )
    else:
        raise ValueError("unknown backbone '{}'".format(name))
    return m


# --------------------------------------------------------------------------- #
#  train / evaluate -- shared by both modes
# --------------------------------------------------------------------------- #
def train_one_epoch(model, loader, optimizer, criterion, device):
    model.train()
    total_loss, n = 0.0, 0
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        optimizer.zero_grad()
        out = model(x)
        loss = criterion(out, y)
        loss.backward()
        optimizer.step()
        total_loss += float(loss.item()) * y.size(0)
        n += y.size(0)
    return total_loss / max(n, 1)


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss, n = 0.0, 0
    preds, targets, probs = [], [], []
    for x, y in loader:
        x, y = x.to(device), y.to(device)
        out = model(x)
        total_loss += float(criterion(out, y).item()) * y.size(0)
        n += y.size(0)
        p = torch.softmax(out, dim=1)
        probs.append(p.cpu().numpy())
        preds.append(p.argmax(1).cpu().numpy())
        targets.append(y.cpu().numpy())
    if n == 0:
        raise RuntimeError("evaluation loader was empty")
    return (total_loss / n,
            np.concatenate(targets), np.concatenate(preds), np.concatenate(probs))


# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(description="E0 baseline, SMOKE/REAL modes")
    add_mode_args(ap)
    ap.add_argument("--rsna_dir", type=str, default=None)
    ap.add_argument("--backbone", type=str, default=None,
                    help="resnet50 | convnext_tiny | swin_t | smallcnn")
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()

    ctx = resolve_mode(args)
    device = torch.device(ctx.device)
    backbone = args.backbone or ("smallcnn" if ctx.is_smoke else "resnet50")

    # ---- data -------------------------------------------------------------
    if ctx.is_smoke:
        print("Building synthetic ROI tensors (smoke mode)...")
        n = ctx.max_samples or 64
        train_ds = SyntheticROIDataset(n, seed=0)
        val_ds = SyntheticROIDataset(max(n // 4, 8), seed=1)
        test_ds = SyntheticROIDataset(max(n // 4, 8), seed=2)
        n_patients = None
    else:
        rsna_dir, ok = resolve_dataset_dir(args.rsna_dir, "RSNA_DATASET_DIR",
                                           DEFAULT_HINTS_RSNA, "RSNA")
        if not ok:
            print("[FAIL] real mode needs the RSNA dataset. Pass --rsna_dir.")
            return 2
        print("Indexing RSNA keypoints and labels...")
        index = build_rsna_index(rsna_dir, ctx.max_samples)
        if index.empty:
            print("[FAIL] no labelled ROIs could be indexed.")
            return 2
        n_patients = index.study_id.nunique()
        print("  {} labelled ROIs across {} patients".format(len(index), n_patients))
        counts = index.label.value_counts().sort_index()
        for k, v in counts.items():
            print("    {:<12} {:>7} ({:.1f}%)".format(
                CLASS_NAMES[k], v, 100.0 * v / len(index)))
        tr, va, te = patient_level_split(index)
        print("  patient-level split: {} / {} / {} ROIs".format(len(tr), len(va), len(te)))
        train_ds = RSNAROIDataset(rsna_dir, tr)
        val_ds = RSNAROIDataset(rsna_dir, va)
        test_ds = RSNAROIDataset(rsna_dir, te)

    dl = lambda ds, sh: DataLoader(ds, batch_size=ctx.batch_size, shuffle=sh,
                                   num_workers=args.workers)
    train_loader, val_loader, test_loader = dl(train_ds, True), dl(val_ds, False), dl(test_ds, False)

    # ---- model ------------------------------------------------------------
    model = build_model(backbone).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print("\nBackbone: {}  ({:.2f}M parameters, counted not asserted)"
          .format(backbone, n_params / 1e6))

    optimizer = torch.optim.AdamW(model.parameters(), lr=ctx.lr)
    criterion = nn.CrossEntropyLoss()

    # ---- STAGE 1: training -----------------------------------------------
    print("\n[STAGE 1] training for {} epochs".format(ctx.epochs))
    hist_path = os.path.join(ctx.log_dir, "E0_{}_{}_history.csv".format(backbone, ctx.mode))
    with open(hist_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["mode", "epoch", "train_loss", "val_loss", "val_acc",
                    "val_macro_f1", "val_qwk", "val_ece", "seconds"])

        best = -1.0
        ckpt_path = os.path.join(
            ctx.checkpoint_dir, "E0_{}_{}_best.pt".format(backbone, ctx.mode))

        for epoch in range(1, ctx.epochs + 1):
            t0 = time.time()
            tr_loss = train_one_epoch(model, train_loader, optimizer, criterion, device)
            va_loss, yt, yp, pr = evaluate(model, val_loader, criterion, device)
            m = compute_metrics(yt, yp, pr)
            secs = time.time() - t0

            w.writerow([ctx.mode, epoch, round(tr_loss, 6), round(va_loss, 6),
                        round(m["accuracy"], 6), round(m["macro_f1"], 6),
                        round(m["qwk"], 6), round(m["ece"], 6), round(secs, 2)])
            fh.flush()
            print("  epoch {:>3}/{}  train {:.4f}  val {:.4f}  acc {:.3f}  "
                  "F1 {:.3f}  QWK {:.3f}  [{:.1f}s]".format(
                      epoch, ctx.epochs, tr_loss, va_loss,
                      m["accuracy"], m["macro_f1"], m["qwk"], secs))

            if m["macro_f1"] > best:
                best = m["macro_f1"]
                torch.save({"model_state_dict": model.state_dict(),
                            "optimizer_state_dict": optimizer.state_dict(),
                            "epoch": epoch, "val_macro_f1": best,
                            "backbone": backbone, "provenance": ctx.stamp()},
                           ckpt_path)

    # verify the checkpoint actually round-trips -- part of what smoke tests
    reloaded = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    assert "model_state_dict" in reloaded and reloaded["model_state_dict"], \
        "checkpoint did not round-trip"
    print("  checkpoint verified: {}".format(os.path.relpath(ckpt_path, PROJECT_ROOT)))

    # ---- STAGE 2: held-out test ------------------------------------------
    print("\n[STAGE 2] held-out test evaluation")
    te_loss, yt, yp, pr = evaluate(model, test_loader, criterion, device)
    test_metrics = compute_metrics(yt, yp, pr)
    test_metrics["test_loss"] = te_loss
    test_metrics["backbone"] = backbone
    test_metrics["n_parameters"] = int(n_params)
    test_metrics["n_patients"] = n_patients

    print("  loss {:.4f}   accuracy {:.4f}   macro-F1 {:.4f}   QWK {:.4f}   ECE {:.4f}"
          .format(te_loss, test_metrics["accuracy"], test_metrics["macro_f1"],
                  test_metrics["qwk"], test_metrics["ece"]))
    print("  grade distance  d0 {:.3f}  d1 {:.3f}  d>=2 {:.3f}".format(
        test_metrics["grade_distance"]["d0"],
        test_metrics["grade_distance"]["d1"],
        test_metrics["grade_distance"]["d2_or_more"]))

    out = ctx.write_json("E0_{}_{}_test_metrics.json".format(backbone, ctx.mode), test_metrics)
    print("  metrics: {}".format(os.path.relpath(out, PROJECT_ROOT)))

    if ctx.is_smoke:
        print("\n" + "=" * 74)
        print("  SMOKE PASS -- the pipeline runs end to end.")
        print("  These numbers are near chance by construction and are NOT results.")
        print("  Re-run with --mode real to produce citable output.")
        print("=" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
