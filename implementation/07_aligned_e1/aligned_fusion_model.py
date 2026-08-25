#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 8 (Track A): E1 Geometry-Aligned Multi-Sequence Fusion Model."""

from __future__ import annotations

import os
import sys
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_models import SequenceEncoder, FixedFusion, N_CLASSES, N_MODALITIES


class GeometryAlignedMultiSeqFusion(nn.Module):
    """Real multi-sequence fusion network over T1, Sagittal T2, and Axial T2."""

    def __init__(self, backbone: str = "resnet18", dim: int = 256, num_classes: int = N_CLASSES):
        super().__init__()
        self.encoders = nn.ModuleList([SequenceEncoder(backbone, dim) for _ in range(N_MODALITIES)])
        self.fusion = FixedFusion(dim, mode="mean")
        self.classifier = nn.Linear(dim, num_classes)

    def forward(self, x_seqs: list[torch.Tensor], mask: torch.Tensor | None = None) -> torch.Tensor:
        # x_seqs: list of (B, 3, H, W) tensors for each modality
        feats = [enc(x) for enc, x in zip(self.encoders, x_seqs)]
        fused = self.fusion(feats, mask=mask)
        return self.classifier(fused)
