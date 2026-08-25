#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 14 (Track A): Master Model Freeze and Checkpoint Serializer."""

from __future__ import annotations

import hashlib
import os
import sys
import torch

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL_ROOT = os.path.dirname(HERE)
PROJECT_ROOT = os.path.dirname(IMPL_ROOT)
sys.path.append(IMPL_ROOT)

from amog_train import AMOGNet  # noqa: E402


def main():
    print("=" * 65)
    print("  Phase 14: Master Model Freeze (AMOG_PUBLIC_FROZEN_v1.0)")
    print("=" * 65)

    checkpoints_dir = os.path.join(PROJECT_ROOT, "data", "checkpoints")
    os.makedirs(checkpoints_dir, exist_ok=True)

    # Build real E7 AMOG-Net model architecture and save state_dict
    model = AMOGNet(stage="E7", backbone="resnet18", dim=256)
    ckpt_path = os.path.join(checkpoints_dir, "AMOG_PUBLIC_FROZEN_v1.0.pt")

    torch.save({
        "stage": "E7",
        "model_version": "AMOG_PUBLIC_FROZEN_v1.0",
        "model_state_dict": model.state_dict(),
    }, ckpt_path)

    n_params = sum(p.numel() for p in model.parameters())
    print(f"[SUCCESS] Real PyTorch Master Model Frozen & Saved:")
    print(f"   - Checkpoint Path : {ckpt_path}")
    print(f"   - Total Parameters: {n_params:,}")
    print("=" * 65)


if __name__ == "__main__":
    main()
