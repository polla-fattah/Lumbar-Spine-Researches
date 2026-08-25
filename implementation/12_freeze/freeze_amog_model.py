#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 14 (Track A): freeze the trained E7 model as the public release.

WHAT THIS SCRIPT USED TO DO
    model = AMOGNet(stage="E7", backbone="resnet18", dim=256)
    torch.save({"model_state_dict": model.state_dict()}, "AMOG_PUBLIC_FROZEN_v1.0.pt")

    It constructed a fresh model, loaded nothing, and serialised randomly
    initialised weights under the project's official release name. Anything
    downstream -- zero-shot transfer, LoRA adaptation, the clinical report
    generator -- would have been evaluating noise while reporting it as the
    frozen public model.

WHAT IT DOES NOW
    Finds the trained E7 checkpoints produced by amog_train.py, selects one by
    validation macro-F1 (Chapter 3 sec:method-model-selection: selection is a
    validation decision, never a test one), loads it, verifies the weights
    actually changed, and records the provenance needed to prove afterwards
    which run this release came from.

    If no trained checkpoint exists it refuses. A release model that cannot be
    traced to a training run is not a release model.
"""

from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import sys
from datetime import datetime

import torch

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL_ROOT = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(IMPL_ROOT)
sys.path.append(IMPL_ROOT)

from amog_train import AMOGNet  # noqa: E402
from amog_modes import _git_commit  # noqa: E402

RELEASE = "AMOG_PUBLIC_FROZEN_v1.0"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_candidates(ckpt_dir: str, stage: str, mode: str):
    """Trained checkpoints for this stage, newest metadata first."""
    out = []
    for p in sorted(glob.glob(os.path.join(
            ckpt_dir, "{}_{}_seed*_best.pt".format(stage, mode)))):
        try:
            ck = torch.load(p, map_location="cpu", weights_only=False)
        except Exception as e:
            print("  [skip] {} ({})".format(os.path.basename(p), e))
            continue
        if "model_state_dict" not in ck:
            print("  [skip] {} (no model_state_dict)".format(os.path.basename(p)))
            continue
        out.append((p, ck))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Freeze the trained E7 public model")
    ap.add_argument("--stage", default="E7")
    ap.add_argument("--mode", choices=["real", "smoke"], default="real")
    ap.add_argument("--backbone", default="resnet18")
    ap.add_argument("--dim", type=int, default=256)
    ap.add_argument("--checkpoint", default=None,
                    help="freeze this exact checkpoint instead of selecting one")
    ap.add_argument("--allow_smoke", action="store_true",
                    help="permit freezing a smoke-mode checkpoint (never a result)")
    args = ap.parse_args()

    print("=" * 68)
    print("  Phase 14: freeze the trained {} model as {}".format(args.stage, RELEASE))
    print("=" * 68)

    ckpt_dir = os.path.join(PROJECT_ROOT, "data",
                            "smoke" if args.mode == "smoke" else "", "checkpoints")
    ckpt_dir = ckpt_dir.replace(os.sep + os.sep, os.sep)
    os.makedirs(ckpt_dir, exist_ok=True)

    if args.checkpoint:
        if not os.path.exists(args.checkpoint):
            print("[FAIL] no such checkpoint: {}".format(args.checkpoint))
            return 2
        src = args.checkpoint
        ck = torch.load(src, map_location="cpu", weights_only=False)
    else:
        cands = find_candidates(ckpt_dir, args.stage, args.mode)
        if not cands:
            print("[FAIL] no trained {} checkpoint found in".format(args.stage))
            print("       {}".format(ckpt_dir))
            print("")
            print("       Freezing an untrained model would publish random weights")
            print("       under the project's release name, and every downstream")
            print("       Track B number would be measuring noise.")
            print("")
            print("       Train first:")
            print("         python implementation/amog_train.py --stage {} --mode {}"
                  .format(args.stage, args.mode))
            return 2
        # Chapter 3 sec:method-model-selection: choose on validation, never test.
        cands.sort(key=lambda t: t[1].get("val_macro_f1", -1.0), reverse=True)
        print("  candidates ({}):".format(len(cands)))
        for p, c in cands:
            print("    {:<38}  val macro-F1 {:.4f}  epoch {}".format(
                os.path.basename(p), c.get("val_macro_f1", float("nan")),
                c.get("epoch", "?")))
        src, ck = cands[0]

    prov = ck.get("provenance") or {}
    if prov.get("amog_mode") == "smoke" and not args.allow_smoke:
        print("\n[FAIL] {} was produced in SMOKE mode, which trains on synthetic"
              .format(os.path.basename(src)))
        print("       tensors and is never a result. Pass --allow_smoke only if")
        print("       you are deliberately rehearsing the release procedure.")
        return 2

    print("\n  selected : {}".format(os.path.basename(src)))
    print("  val macro-F1 {:.4f} at epoch {}".format(
        ck.get("val_macro_f1", float("nan")), ck.get("epoch", "?")))

    # Rebuild the architecture the checkpoint was TRAINED with, rather than
    # whatever this invocation happens to default to. Requiring the caller to
    # re-specify --backbone and --dim means a mismatch shows up as a wall of
    # size-mismatch errors, or -- with strict=False -- as a partial load that
    # leaves part of the release random.
    sd = ck["model_state_dict"]
    backbone = ck.get("backbone") or args.backbone
    dim = args.dim
    for key in ("encoders.0.proj.weight", "head.weight", "head.fc.weight"):
        if key in sd:
            dim = int(sd[key].shape[0] if key.startswith("encoders") else sd[key].shape[1])
            break
    stage = ck.get("stage") or args.stage
    if (backbone, dim, stage) != (args.backbone, args.dim, args.stage):
        print("  architecture from checkpoint: stage {}, backbone {}, dim {}"
              .format(stage, backbone, dim))

    model = AMOGNet(stage=stage, backbone=backbone, dim=dim)
    args.stage, args.backbone, args.dim = stage, backbone, dim
    before = {k: v.detach().clone() for k, v in model.state_dict().items()}
    missing, unexpected = model.load_state_dict(sd, strict=False)
    after = model.state_dict()
    changed = sum(1 for k in before if not torch.equal(before[k], after[k]))

    if changed == 0:
        print("\n[FAIL] loading the checkpoint changed no weight. The release")
        print("       would contain the random initialisation.")
        return 3
    if missing:
        print("\n[FAIL] {} parameter(s) absent from the checkpoint, e.g. {}."
              .format(len(missing), list(missing)[:3]))
        print("       A partially loaded release is partly random. Refusing.")
        return 3

    print("  loaded   : {} of {} tensors changed, {} unexpected key(s)".format(
        changed, len(before), len(unexpected)))

    model.eval()
    out = os.path.join(ckpt_dir, RELEASE + ".pt")
    torch.save({
        "model_version": RELEASE,
        "stage": args.stage,
        "backbone": args.backbone,
        "dim": args.dim,
        "model_state_dict": model.state_dict(),
        "source_checkpoint": os.path.relpath(src, PROJECT_ROOT),
        "source_val_macro_f1": ck.get("val_macro_f1"),
        "source_epoch": ck.get("epoch"),
        "source_provenance": prov,
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
    }, out)

    digest = sha256_file(out)
    sidecar = {
        "model_version": RELEASE,
        "sha256": digest,
        "bytes": os.path.getsize(out),
        "source_checkpoint": os.path.relpath(src, PROJECT_ROOT),
        "source_val_macro_f1": ck.get("val_macro_f1"),
        "source_epoch": ck.get("epoch"),
        "stage": args.stage, "backbone": args.backbone, "dim": args.dim,
        "n_parameters": int(sum(p.numel() for p in model.parameters())),
        "tensors_loaded": changed,
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "git_commit": _git_commit(),
        "mode": args.mode,
        "is_citable": args.mode == "real",
    }
    with open(os.path.splitext(out)[0] + "_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(sidecar, fh, indent=2)

    print("\n[OK] frozen release written")
    print("  path      : {}".format(os.path.relpath(out, PROJECT_ROOT)))
    print("  parameters: {:,}".format(sidecar["n_parameters"]))
    print("  sha256    : {}".format(digest))
    if args.mode != "real":
        print("  [!] SMOKE provenance -- not a result, not citable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
