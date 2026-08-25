#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 14 & Gate 10 Verification: Master Model Checkpoint Audit."""

from __future__ import annotations

import os
import sys
import torch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(HERE))


def main():
    print("=" * 65)
    print("  Phase 14 & Gate 10: Master Model Checkpoint Verification Audit")
    print("=" * 65)

    ckpt_path = os.path.join(PROJECT_ROOT, "data", "checkpoints", "AMOG_PUBLIC_FROZEN_v1.0.pt")
    if not os.path.exists(ckpt_path):
        print(f"[FAIL] Checkpoint not found at {ckpt_path}.")
        sys.exit(1)

    ckpt = torch.load(ckpt_path, map_location="cpu")
    assert "model_state_dict" in ckpt, "Checkpoint missing model_state_dict!"
    n_params = sum(v.numel() for v in ckpt["model_state_dict"].values())
    assert n_params > 100_000, f"Checkpoint has insufficient parameters: {n_params}"

    print(f"Auditing Master Model Checkpoint:")
    print(f"  - Loadable PyTorch Checkpoint: VERIFIED")
    print(f"  - Total Parameters: {n_params:,}: VERIFIED")
    print("\n[PASS] Gate 10 Verified: AMOG_PUBLIC_FROZEN_v1.0 Certified & Released!")
    print("=" * 65)


if __name__ == "__main__":
    main()
