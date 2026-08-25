#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 17 & Gate 12: Track B LoRA Domain Adaptation Engine."""

from __future__ import annotations

import math
import os
import sys
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_models import N_CLASSES


class LoRALinear(nn.Module):
    """Parameter-efficient Low-Rank Adaptation (LoRA) Linear Layer."""

    def __init__(self, in_features: int, out_features: int, rank: int = 8, alpha: float = 16.0):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.rank = rank
        self.scaling = alpha / rank

        self.linear = nn.Linear(in_features, out_features, bias=True)
        # Freeze base linear layer weights
        self.linear.weight.requires_grad = False
        if self.linear.bias is not None:
            self.linear.bias.requires_grad = False

        self.lora_A = nn.Parameter(torch.zeros(rank, in_features))
        self.lora_B = nn.Parameter(torch.zeros(out_features, rank))
        nn.init.kaiming_uniform_(self.lora_A, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        base_out = self.linear(x)
        lora_out = (x @ self.lora_A.T @ self.lora_B.T) * self.scaling
        return base_out + lora_out


class LoRAAdaptedClassifier(nn.Module):
    """Classifier head adapted with LoRA for local clinical transfer."""

    def __init__(self, in_dim: int = 256, n_classes: int = N_CLASSES, rank: int = 8):
        super().__init__()
        self.adapted_head = LoRALinear(in_dim, n_classes, rank=rank)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.adapted_head(x)
