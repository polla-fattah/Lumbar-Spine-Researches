#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 9 (Track A): E2/E3 Disease-Conditioned Router and Modality Dropout."""

from __future__ import annotations

import os
import sys
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_models import DiseaseConditionedRouter, apply_modality_dropout, N_CLASSES


class RoutedMultiSeqModel(nn.Module):
    """Real model combining per-sequence embeddings with disease-conditioned routing."""

    def __init__(self, dim: int = 256, num_classes: int = N_CLASSES):
        super().__init__()
        self.router = DiseaseConditionedRouter(dim=dim)
        self.classifier = nn.Linear(dim, num_classes)

    def forward(self, features: torch.Tensor, cond_idx: torch.Tensor,
                level_idx: torch.Tensor, mask: torch.Tensor | None = None,
                p_drop: float = 0.0, training: bool = True):
        if mask is None:
            mask = torch.ones(features.size(0), features.size(1), device=features.device)
        if training and p_drop > 0.0:
            mask = apply_modality_dropout(mask, p_drop=p_drop, training=training)
        fused, gates = self.router(features, mask, cond_idx, level_idx)
        logits = self.classifier(fused)
        return logits, gates
