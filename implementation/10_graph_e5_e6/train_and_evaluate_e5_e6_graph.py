#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 11 & 12 (Track A): E5/E6 Graph Learning Runner."""

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
    ap = argparse.ArgumentParser(description="E5/E6 Graph Trainer")
    ap.add_argument("--mode", choices=["real", "smoke"], default="smoke")
    ap.add_argument("--stage", choices=["E5", "E6"], default="E6")
    ap.add_argument("--shuffled", action="store_true", help="Run shuffled control")
    ap.add_argument("--ungated", action="store_true", help="Run ungated control")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch_size", type=int, default=8)
    ap.add_argument("--backbone", type=str, default="resnet18")
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()

    cmd = [
        sys.executable, TRAINER,
        "--stage", args.stage,
        "--mode", args.mode,
        "--epochs", str(args.epochs),
        "--batch_size", str(args.batch_size),
        "--backbone", args.backbone,
        "--lr", str(args.lr),
    ]
    if args.shuffled:
        cmd.append("--shuffled")
    if args.ungated:
        cmd.append("--ungated")

    tag = f"{args.stage}{'_shuffled' if args.shuffled else ''}{'_ungated' if args.ungated else ''}"
    print("=" * 65)
    print(f"  Phase 11 & 12: Running {tag} Relational Graph GNN via unified AMOG engine")
    print("=" * 65)
    ret = subprocess.run(cmd, cwd=IMPL_ROOT)
    sys.exit(ret.returncode)


if __name__ == "__main__":
    main()
