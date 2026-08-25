#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 10 (Track A): E4 ACSSL Contrastive Pretraining Runner."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL_ROOT = os.path.dirname(HERE)
TRAINER = os.path.join(IMPL_ROOT, "amog_train.py")


def main():
    ap = argparse.ArgumentParser(description="E4 ACSSL Trainer")
    ap.add_argument("--mode", choices=["real", "smoke"], default="smoke")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--backbone", type=str, default="resnet18")
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()

    cmd = [
        sys.executable, TRAINER,
        "--stage", "E4",
        "--mode", args.mode,
        "--epochs", str(args.epochs),
        "--batch_size", str(args.batch_size),
        "--backbone", args.backbone,
        "--lr", str(args.lr),
    ]

    print("=" * 65)
    print("  Phase 10: Running E4 ACSSL Contrastive Pretraining via unified AMOG engine")
    print("=" * 65)
    ret = subprocess.run(cmd, cwd=IMPL_ROOT)
    sys.exit(ret.returncode)


if __name__ == "__main__":
    main()
