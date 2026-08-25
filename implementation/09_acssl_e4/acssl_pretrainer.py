#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 10 (Track A): E4 ACSSL Contrastive Pretraining Module."""

from __future__ import annotations

import os
import sys
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_models import ACSSLProjector, info_nce


class ACSSLFramework(nn.Module):
    """Anatomically Constrained Cross-Sequence Self-Supervised Learning Module."""

    def __init__(self, dim: int = 256, out_dim: int = 128, temperature: float = 0.1):
        super().__init__()
        self.projector = ACSSLProjector(dim=dim, out=out_dim)
        self.temperature = temperature

    def forward(self, z1: torch.Tensor, z2: torch.Tensor) -> torch.Tensor:
        p1 = self.projector(z1)
        p2 = self.projector(z2)
        return info_nce(p1, p2, temperature=self.temperature)
