#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 11 & 12 (Track A): Heterogeneous Disease-Anatomy Graph Module."""

from __future__ import annotations

import os
import sys
import torch
import torch.nn as nn

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_models import (
    HeterogeneousRGCN, HomogeneousGNN, build_edges,
    N_TARGETS, N_CLASSES, EDGE_TYPES
)


class AMOGGraphEngine(nn.Module):
    """Real 25-Node Relational Graph Neural Network for Lumbar Degenerative Disease Grading."""

    def __init__(self, dim: int = 256, num_classes: int = N_CLASSES, shuffled: bool = False, ungated: bool = False):
        super().__init__()
        edge_index, edge_type = build_edges(shuffled=shuffled)
        self.register_buffer("edge_index", edge_index)
        self.register_buffer("edge_type", edge_type)
        self.gnn = HeterogeneousRGCN(dim=dim, gated=not ungated)
        self.classifier = nn.Linear(self.gnn.out_dim, num_classes)

    def forward(self, node_features: torch.Tensor) -> torch.Tensor:
        # node_features: (B, 25, D)
        h = self.gnn(node_features, self.edge_index, self.edge_type)
        return self.classifier(h)
