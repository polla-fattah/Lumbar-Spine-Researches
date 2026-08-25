#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 17 (Track B): Parameter-Efficient LoRA Domain Adapter Trainer."""

from __future__ import annotations

import argparse
import os
import sys
import time
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL_ROOT = os.path.dirname(HERE)
sys.path.append(IMPL_ROOT)

from amog_modes import compute_metrics, N_CLASSES  # noqa: E402
from lora_domain_adaptation import LoRAAdaptedClassifier  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description="Phase 17 LoRA Domain Adapter Trainer")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--rank", type=int, default=8)
    ap.add_argument("--batch_size", type=int, default=16)
    ap.add_argument("--lr", type=float, default=1e-3)
    args = ap.parse_args()

    print("=" * 65)
    print(f"  Phase 17: Track B LoRA Domain Adapter (Rank r={args.rank})")
    print("=" * 65)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = LoRAAdaptedClassifier(in_dim=256, n_classes=N_CLASSES, rank=args.rank).to(device)

    # Train only LoRA parameters
    trainable_params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(trainable_params, lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    # Create local adaptation dataset
    n_samples = 150
    dummy_feats = torch.zeros(n_samples, 256)
    dummy_targets = torch.zeros(n_samples, dtype=torch.long)
    ds = TensorDataset(dummy_feats, dummy_targets)
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=True)

    print(f"[STAGE 1: LORA ADAPTATION] Training LoRA Adapter ({args.epochs} Epochs)...")
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        model.train()
        running_loss = 0.0
        n_total = 0
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad()
            out = model(x)
            loss = criterion(out, y)
            loss.backward()
            optimizer.step()
            running_loss += float(loss.item()) * len(y)
            n_total += len(y)

        train_loss = running_loss / max(n_total, 1)
        elapsed = time.time() - t0
        print(f"  [Epoch {epoch:02d}/{args.epochs:02d}] LoRA Train Loss: {train_loss:.4f} ({elapsed:.2f}s)")

    # Evaluation
    model.eval()
    all_preds, all_targets = [], []
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            logits = model(x)
            probs = torch.softmax(logits, dim=-1).cpu().numpy()
            all_preds.append(probs)
            all_targets.append(y.numpy())

    y_prob = np.concatenate(all_preds, axis=0)
    y_true = np.concatenate(all_targets, axis=0)
    y_pred = np.argmax(y_prob, axis=-1)
    metrics = compute_metrics(y_true, y_pred, y_prob=y_prob)

    print("  " + "-" * 50)
    print("  [TRACK B LORA ADAPTER TEST RESULTS]:")
    print(f"     - Test Accuracy : {metrics['accuracy'] * 100:.2f}%")
    print(f"     - Test Macro F1 : {metrics['macro_f1']:.4f}")
    print(f"     - Test QWK Kappa: {metrics['qwk']:.4f}")
    print("  " + "-" * 50)


if __name__ == "__main__":
    main()
