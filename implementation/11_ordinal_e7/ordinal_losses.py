#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 13 (Track A): E7 Ordinal Loss and Calibration Engine."""

from __future__ import annotations

import os
import sys
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_models import (
    OrdinalCORNHead, clinical_cost_matrix, expected_cost_loss,
    TemperatureScaler, N_CLASSES
)


class AMOGOrdinalCalibrationEngine(nn.Module):
    """Real Ordinal Classification (CORN) and Probability Calibration module."""

    def __init__(self, dim: int = 256, n_classes: int = N_CLASSES, cost_weight: float = 0.5):
        super().__init__()
        self.head = OrdinalCORNHead(dim=dim, n_classes=n_classes)
        self.scaler = TemperatureScaler()
        self.cost_weight = cost_weight
        self.register_buffer("cost_matrix", clinical_cost_matrix(device="cpu"))

    def compute_loss(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        loss = self.head.loss(logits, targets)
        if self.cost_weight > 0.0:
            probs = self.head.to_probs(logits)
            c_loss = expected_cost_loss(probs, targets, self.cost_matrix.to(logits.device))
            loss = loss + self.cost_weight * c_loss
        return loss
