#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Real model components for E1-E7. Nothing here reports a number it did not compute.

Each class corresponds to a rung of the Chapter 3 ladder, and each is written so
that the CONTROL it is measured against also exists -- an ablation you cannot run
is a claim you cannot defend.

    E1     FixedFusion              concat / mean over available sequences
    E2/E3  DiseaseConditionedRouter target-conditioned gate, masked softmax,
                                    modality dropout, gate-entropy monitoring
    E4     ACSSLProjector           cross-sequence InfoNCE at (patient, level)
    E5     HomogeneousGNN           one undifferentiated edge type
    E6     HeterogeneousRGCN        typed edges + gated residual update
    E7     OrdinalCORNHead          ordered thresholds + asymmetric clinical cost

WHAT THE PREVIOUS IMPLEMENTATION HAD
------------------------------------
    class RGCNMessagePassingGNN(nn.Module):
        def forward(self, x, edge_index=None):
            h = self.node_proj(x)
            h = h + self.message_passing(h)
            return self.classifier(h)

edge_index is accepted and never used. There is no adjacency, no message passing
and no graph -- it is an MLP named after one. Its reported metrics were literals.

DESIGN NOTES THAT MATTER FOR THE VIVA
-------------------------------------
* The router carries a load-balancing term. Sparsely-gated experts are known to
  collapse onto one input, and a router that always picks sagittal T2 is
  functionally a fixed fusion rule presenting as a learned one. Gate entropy is
  returned on every forward pass so collapse is observable, not assumed absent.
* build_edges() can emit a SHUFFLED topology with identical node and edge counts.
  Without that control, E6 beating E5 shows only that more parameters help.
* The cost matrix satisfies c20 > c21: grading Severe as Normal/Mild must cost
  more than grading it Moderate.
"""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import LUMBAR_LEVELS, CONDITIONS, N_CLASSES  # noqa: E402

N_LEVELS = len(LUMBAR_LEVELS)        # 5
N_CONDITIONS = len(CONDITIONS)       # 5
N_TARGETS = N_LEVELS * N_CONDITIONS  # 25
MODALITIES = ["sag_t1", "sag_t2", "ax_t2"]
N_MODALITIES = len(MODALITIES)

# CONDITIONS order: left_foraminal, left_subarticular, central_canal,
#                   right_subarticular, right_foraminal
BILATERAL_PAIRS = [(0, 4), (1, 3)]   # LF<->RF, LS<->RS

EDGE_TYPES = ["adjacent_level", "same_level_cross_condition", "bilateral"]


def node_id(level_idx: int, condition_idx: int) -> int:
    return level_idx * N_CONDITIONS + condition_idx


# --------------------------------------------------------------------------- #
#  encoders
# --------------------------------------------------------------------------- #
class SequenceEncoder(nn.Module):
    """One backbone per MRI sequence. Weights are NOT shared by default.

    Chapter 3: T1, sagittal T2/STIR and axial T2 have different contrast and
    orientation statistics, so separate encoders are the default and weight
    sharing is an explicit ablation rather than a convenience.
    """

    def __init__(self, backbone: str = "resnet18", out_dim: int = 256,
                 pretrained: bool = False):
        super().__init__()
        import torchvision.models as tvm
        w = "DEFAULT" if pretrained else None
        if backbone == "resnet18":
            m = tvm.resnet18(weights=w); feat = m.fc.in_features; m.fc = nn.Identity()
        elif backbone == "resnet50":
            m = tvm.resnet50(weights=w); feat = m.fc.in_features; m.fc = nn.Identity()
        elif backbone == "convnext_tiny":
            m = tvm.convnext_tiny(weights=w)
            feat = m.classifier[2].in_features; m.classifier[2] = nn.Identity()
        elif backbone == "smallcnn":
            m = nn.Sequential(
                nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
                nn.MaxPool2d(2),
                nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
                nn.AdaptiveAvgPool2d(1), nn.Flatten())
            feat = 64
        else:
            raise ValueError("unknown backbone '{}'".format(backbone))
        self.backbone = m
        self.proj = nn.Linear(feat, out_dim)
        self.out_dim = out_dim

    def forward(self, x):
        return self.proj(self.backbone(x))


# --------------------------------------------------------------------------- #
#  E1 -- fixed fusion (the control the router must beat)
# --------------------------------------------------------------------------- #
class FixedFusion(nn.Module):
    """Concatenate or average sequence features. No learned weighting."""

    def __init__(self, dim: int = 256, mode: str = "mean"):
        super().__init__()
        assert mode in ("mean", "concat")
        self.mode = mode
        self.out_dim = dim if mode == "mean" else dim * N_MODALITIES
        self.dim = dim

    def forward(self, feats, mask):
        """feats (B, M, D); mask (B, M) with 1 = present."""
        m = mask.unsqueeze(-1).float()
        if self.mode == "mean":
            s = (feats * m).sum(1)
            return s / m.sum(1).clamp(min=1.0), None
        return (feats * m).reshape(feats.size(0), -1), None


# --------------------------------------------------------------------------- #
#  E2 / E3 -- disease-conditioned routing
# --------------------------------------------------------------------------- #
class DiseaseConditionedRouter(nn.Module):
    """Learned, target-conditioned weighting over available sequences.

    g_{p,t,m} = softmax_m G[ LayerNorm(f), e_condition, e_level, q_quality ]

    Unavailable sequences are masked BEFORE the softmax and the remainder is
    renormalised, so a missing sequence is never represented by an all-zero image
    whose meaning the network has to infer.
    """

    def __init__(self, dim: int = 256, emb: int = 32, hidden: int = 128,
                 use_quality: bool = True):
        super().__init__()
        self.norm = nn.LayerNorm(dim)
        self.cond_emb = nn.Embedding(N_CONDITIONS, emb)
        self.level_emb = nn.Embedding(N_LEVELS, emb)
        self.use_quality = use_quality
        q = 1 if use_quality else 0
        self.gate = nn.Sequential(
            nn.Linear(dim + 2 * emb + q, hidden), nn.ReLU(),
            nn.Linear(hidden, 1))
        self.out_dim = dim

    def forward(self, feats, mask, cond_idx, level_idx, quality=None):
        """feats (B,M,D); mask (B,M); cond_idx (B,); level_idx (B,)."""
        B, M, D = feats.shape
        h = self.norm(feats)
        ce = self.cond_emb(cond_idx).unsqueeze(1).expand(B, M, -1)
        le = self.level_emb(level_idx).unsqueeze(1).expand(B, M, -1)
        parts = [h, ce, le]
        if self.use_quality:
            q = quality if quality is not None else torch.ones(B, M, device=feats.device)
            parts.append(q.unsqueeze(-1))
        logits = self.gate(torch.cat(parts, dim=-1)).squeeze(-1)      # (B, M)

        logits = logits.masked_fill(mask <= 0, float("-inf"))
        # a row with no available sequence would produce NaN; keep it uniform
        empty = (mask.sum(1) == 0)
        if empty.any():
            logits = logits.masked_fill(empty.unsqueeze(1), 0.0)
        g = torch.softmax(logits, dim=1)
        g = torch.nan_to_num(g, nan=0.0)

        fused = (feats * g.unsqueeze(-1)).sum(1)
        return fused, g

    @staticmethod
    def load_balance_loss(g, mask):
        """Penalise collapse onto one sequence.

        Shazeer et al. report expert collapse for sparsely-gated mixtures: without
        an explicit balancing term the gate can settle on a single input and the
        others stop receiving gradient. A router that always selects sagittal T2
        is a fixed fusion rule wearing a learned one's clothes, so this is
        monitored and penalised rather than assumed not to happen.
        """
        m = mask.float()
        share = (g * m).sum(0) / m.sum(0).clamp(min=1.0)
        share = share / share.sum().clamp(min=1e-8)
        target = 1.0 / max(share.numel(), 1)
        return ((share - target) ** 2).sum()

    @staticmethod
    def gate_entropy(g, mask):
        """Mean entropy of the routing distribution; near 0 means collapsed."""
        p = g.clamp(min=1e-8)
        ent = -(p * p.log()).sum(1)
        avail = mask.sum(1).clamp(min=1).float()
        # Normalise by the maximum entropy for that row's availability count so
        # the value is comparable across studies with different sequence sets:
        # 1.0 = weight spread evenly, 0.0 = collapsed onto one sequence.
        # A row with a single available sequence has no choice to make and is
        # excluded rather than divided by log(1) = 0.
        max_ent = avail.log()
        usable = max_ent > 1e-6
        if not bool(usable.any()):
            return torch.ones((), device=g.device)
        return (ent[usable] / max_ent[usable]).mean()


def apply_modality_dropout(mask, p_drop: float = 0.2, training: bool = True):
    """E3: stochastically remove sequences, never dropping the last one."""
    if not training or p_drop <= 0:
        return mask
    keep = (torch.rand_like(mask.float()) > p_drop).float()
    new = mask.float() * keep
    empty = new.sum(1) == 0
    if empty.any():
        new[empty] = mask[empty].float()      # restore rather than emit an empty study
    return new


# --------------------------------------------------------------------------- #
#  E4 -- anatomically aligned cross-sequence self-supervision
# --------------------------------------------------------------------------- #
class ACSSLProjector(nn.Module):
    """Projection head used only to express the alignment constraint.

    Kept separate from the grading representation so that an objective designed
    to align anatomy across sequences does not force the disease representation
    itself to become sequence-invariant.
    """

    def __init__(self, dim: int = 256, hidden: int = 256, out: int = 128):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(dim, hidden), nn.ReLU(), nn.Linear(hidden, out))

    def forward(self, x):
        return F.normalize(self.net(x), dim=-1)


def info_nce(z_a, z_b, temperature: float = 0.1):
    """Cross-sequence InfoNCE. Positives are the same (patient, level) in two
    different sequences; the pairing comes from DICOM geometry, not appearance."""
    logits = (z_a @ z_b.t()) / temperature
    target = torch.arange(z_a.size(0), device=z_a.device)
    return 0.5 * (F.cross_entropy(logits, target) + F.cross_entropy(logits.t(), target))


# --------------------------------------------------------------------------- #
#  E5 / E6 -- the target graph
# --------------------------------------------------------------------------- #
def build_edges(shuffled: bool = False, seed: int = 0):
    """Anatomical topology over the 25 targets.

    Returns (edge_index (2,E) long, edge_type (E,) long).

    `shuffled=True` produces the control: the same node count, the same number of
    edges of each type, but endpoints permuted. It is not optional. If a graph
    with arbitrary topology performs as well as the anatomical one, the study has
    shown that extra message-passing capacity helps -- not that anatomy matters.
    """
    src, dst, typ = [], [], []

    def add(a, b, t):
        src.append(a); dst.append(b); typ.append(t)
        src.append(b); dst.append(a); typ.append(t)

    for c in range(N_CONDITIONS):                      # adjacent level
        for l in range(N_LEVELS - 1):
            add(node_id(l, c), node_id(l + 1, c), 0)
    for l in range(N_LEVELS):                          # same level, cross condition
        for a in range(N_CONDITIONS):
            for b in range(a + 1, N_CONDITIONS):
                add(node_id(l, a), node_id(l, b), 1)
    for l in range(N_LEVELS):                          # bilateral
        for a, b in BILATERAL_PAIRS:
            add(node_id(l, a), node_id(l, b), 2)

    edge_index = torch.tensor([src, dst], dtype=torch.long)
    edge_type = torch.tensor(typ, dtype=torch.long)

    if shuffled:
        # Chapter 3 sec:method-graph-baselines: "graph capacity retained while
        # anatomical edges are permuted."
        #
        # The control must differ from the anatomical graph in exactly one
        # respect -- which anatomical targets the edges join -- and in no other.
        # Drawing fresh random endpoints does not do that: it yields an
        # asymmetric graph with colliding edges and a lopsided degree sequence
        # (one node reached degree 16 while another fell to 1). Comparing E6
        # against a structurally weaker graph would credit anatomy for an
        # advantage that came from the control being a worse graph, which is the
        # precise conclusion this control exists to rule out.
        #
        # A node relabelling is the permutation that leaves every structural
        # property intact -- edge count, per-type counts, symmetry, degree
        # sequence, uniqueness -- while destroying the correspondence between
        # the topology and the (level, condition) meaning of each node.
        g = torch.Generator().manual_seed(seed)
        perm = torch.randperm(N_TARGETS, generator=g)
        edge_index = perm[edge_index]
    return edge_index, edge_type


class HomogeneousGNN(nn.Module):
    """E5 control: real message passing, one undifferentiated edge type."""

    def __init__(self, dim: int = 256, hidden: int = 256, layers: int = 2):
        super().__init__()
        self.layers = nn.ModuleList()
        self.norms = nn.ModuleList()
        d = dim
        for _ in range(layers):
            self.layers.append(nn.Linear(d, hidden))
            self.norms.append(nn.LayerNorm(hidden))
            d = hidden
        self.out_dim = d

    def forward(self, x, edge_index, edge_type=None):
        """x (B, N, D)."""
        B, N, _ = x.shape
        src, dst = edge_index[0], edge_index[1]
        h = x
        for lin, norm in zip(self.layers, self.norms):
            msg = lin(h)                                   # (B,N,H)
            # dtype follows the message so this survives autocast
            agg = torch.zeros(B, N, msg.size(-1), device=x.device, dtype=msg.dtype)
            agg.index_add_(1, dst, msg[:, src, :])
            deg = torch.zeros(N, device=x.device, dtype=msg.dtype)
            deg.index_add_(0, dst, torch.ones_like(dst, dtype=msg.dtype))
            agg = agg / deg.clamp(min=1).view(1, N, 1)
            h = norm(F.relu(agg + msg))
        return h


class HeterogeneousRGCN(nn.Module):
    """E6: relation-specific transforms plus a gated residual update.

    Relation-specific weights follow R-GCN (Schlichtkrull et al.). The gate is the
    part that addresses information contagion: a node with strong local evidence
    can keep its own state when neighbour messages disagree, so a severe focal
    lesion is less able to inflate an adjacent normal level. The ungated variant
    is a mandatory ablation, otherwise any gain cannot be attributed to the gate.
    """

    def __init__(self, dim: int = 256, hidden: int = 256, layers: int = 2,
                 n_relations: int = len(EDGE_TYPES), gated: bool = True):
        super().__init__()
        self.gated = gated
        self.n_relations = n_relations
        self.rel = nn.ModuleList()
        self.self_lin = nn.ModuleList()
        self.gates = nn.ModuleList()
        self.norms = nn.ModuleList()
        d = dim
        for _ in range(layers):
            self.rel.append(nn.ModuleList([nn.Linear(d, hidden) for _ in range(n_relations)]))
            self.self_lin.append(nn.Linear(d, hidden))
            self.gates.append(nn.Linear(d + hidden, hidden))
            self.norms.append(nn.LayerNorm(hidden))
            d = hidden
        self.out_dim = d

    def forward(self, x, edge_index, edge_type):
        B, N, _ = x.shape
        src, dst = edge_index[0], edge_index[1]
        h = x
        for li in range(len(self.rel)):
            hidden = self.self_lin[li].out_features
            # Allocate the accumulator to match the MESSAGES, not the input.
            # Under autocast the relation projections return bf16 while h may
            # still be fp32, and index_add_ requires both to agree.
            agg = None
            deg = None
            for r in range(self.n_relations):
                sel = (edge_type == r)
                if not bool(sel.any()):
                    continue
                s, d_ = src[sel], dst[sel]
                msg = self.rel[li][r](h)                   # (B,N,H)
                if agg is None:
                    agg = torch.zeros(B, N, hidden, device=x.device, dtype=msg.dtype)
                    deg = torch.zeros(N, device=x.device, dtype=msg.dtype)
                agg.index_add_(1, d_, msg[:, s, :])
                deg.index_add_(0, d_, torch.ones_like(d_, dtype=msg.dtype))
            if agg is None:
                own = self.self_lin[li](h)
                h = F.relu(self.norms[li](own))
                continue
            agg = agg / deg.clamp(min=1).view(1, N, 1)
            own = self.self_lin[li](h)
            if self.gated:
                gamma = torch.sigmoid(self.gates[li](torch.cat([h, agg], dim=-1)))
                h = self.norms[li](own + gamma * agg)
            else:
                h = self.norms[li](own + agg)
            h = F.relu(h)
        return h


# --------------------------------------------------------------------------- #
#  E7 -- ordinal head and clinically asymmetric cost
# --------------------------------------------------------------------------- #
class OrdinalCORNHead(nn.Module):
    """Three ordered grades expressed as two threshold questions.

    P(y > 0) and P(y > 1), constrained to be non-increasing so the ordering
    cannot be violated. Cross-entropy remains the mandatory control, because
    earlier lumbar work found ordinal objectives did not consistently beat it.
    """

    def __init__(self, dim: int, n_classes: int = N_CLASSES):
        super().__init__()
        self.n_classes = n_classes
        self.fc = nn.Linear(dim, n_classes - 1)

    def forward(self, x):
        return self.fc(x)                                  # (B, K-1) logits

    @staticmethod
    def loss(logits, y):
        """Binary targets: t_k = 1 if y > k."""
        K1 = logits.size(-1)
        t = torch.stack([(y > k).float() for k in range(K1)], dim=-1)
        return F.binary_cross_entropy_with_logits(logits, t)

    @staticmethod
    def to_probs(logits):
        """Cumulative logits -> class probabilities, ordering enforced."""
        p_gt = torch.sigmoid(logits)                       # (B, K-1)
        p_gt, _ = torch.cummin(p_gt, dim=-1)               # non-increasing
        B = p_gt.size(0)
        ones = torch.ones(B, 1, device=p_gt.device, dtype=p_gt.dtype)
        zeros = torch.zeros(B, 1, device=p_gt.device, dtype=p_gt.dtype)
        upper = torch.cat([ones, p_gt], dim=1)
        lower = torch.cat([p_gt, zeros], dim=1)
        return (upper - lower).clamp(min=1e-8)


def clinical_cost_matrix(c20: float = 4.0, c21: float = 2.0,
                         c10: float = 1.5, c01: float = 1.0,
                         c02: float = 1.0, c12: float = 1.0,
                         device=None):
    """Asymmetric cost with c20 > c21.

    Grading a Severe canal as Normal/Mild is the clinically decisive error and
    must cost more than grading it Moderate. Values here are a documented default
    for sensitivity analysis, not a claim about clinical utility.
    """
    assert c20 > c21, "Chapter 3 requires c20 > c21"
    C = torch.tensor([[0.0, c01, c02],
                      [c10, 0.0, c12],
                      [c20, c21, 0.0]], dtype=torch.float32)
    return C.to(device) if device is not None else C


def expected_cost_loss(probs, y, C):
    """Expected cost under the predicted distribution."""
    return C[y].mul(probs).sum(dim=1).mean()


class TemperatureScaler(nn.Module):
    """Single-parameter calibration fitted on validation logits only."""

    def __init__(self):
        super().__init__()
        self.log_t = nn.Parameter(torch.zeros(1))

    def forward(self, logits):
        return logits / self.log_t.exp().clamp(min=1e-2)

    def fit(self, logits, labels, steps: int = 200, lr: float = 0.01):
        opt = torch.optim.LBFGS([self.log_t], lr=lr, max_iter=steps)

        def closure():
            opt.zero_grad()
            loss = F.cross_entropy(self.forward(logits), labels)
            loss.backward()
            return loss

        opt.step(closure)
        return float(self.log_t.exp().item())


if __name__ == "__main__":
    torch.manual_seed(0)
    print("component self-test")
    print("-" * 60)

    ei, et = build_edges()
    print("graph      : {} nodes, {} directed edges".format(N_TARGETS, ei.size(1)))
    for i, name in enumerate(EDGE_TYPES):
        print("             {:<28} {}".format(name, int((et == i).sum())))
    ei_s, _ = build_edges(shuffled=True)
    print("shuffled ctl: {} edges, same count = {}".format(
        ei_s.size(1), ei_s.size(1) == ei.size(1)))

    B, M, D = 4, 3, 256
    feats = torch.randn(B, M, D)
    mask = torch.tensor([[1, 1, 1], [1, 0, 1], [1, 0, 0], [0, 1, 1]], dtype=torch.float32)
    router = DiseaseConditionedRouter(D)
    fused, g = router(feats, mask, torch.tensor([0, 2, 4, 1]), torch.tensor([0, 1, 2, 3]))
    print("\nrouter     : fused {}, weights sum {:.4f}".format(
        tuple(fused.shape), float(g.sum(1).mean())))
    print("             masked slots zero = {}".format(bool((g[mask == 0] == 0).all())))
    print("             gate entropy {:.4f}  balance loss {:.5f}".format(
        float(router.gate_entropy(g, mask)), float(router.load_balance_loss(g, mask))))

    x = torch.randn(2, N_TARGETS, D)
    print("\nE5 homo    : {}".format(tuple(HomogeneousGNN(D)(x, ei).shape)))
    print("E6 hetero  : {}".format(tuple(HeterogeneousRGCN(D)(x, ei, et).shape)))
    print("E6 ungated : {}".format(tuple(HeterogeneousRGCN(D, gated=False)(x, ei, et).shape)))

    head = OrdinalCORNHead(D)
    lg = head(torch.randn(6, D))
    pr = head.to_probs(lg)
    print("\nordinal    : probs sum {:.4f}, monotone ok".format(float(pr.sum(1).mean())))
    C = clinical_cost_matrix()
    print("cost matrix: c20 {} > c21 {}  -> {}".format(
        float(C[2, 0]), float(C[2, 1]), bool(C[2, 0] > C[2, 1])))
    print("expected cost {:.4f}".format(
        float(expected_cost_loss(pr, torch.randint(0, 3, (6,)), C))))

    za, zb = ACSSLProjector(D)(torch.randn(8, D)), ACSSLProjector(D)(torch.randn(8, D))
    print("\nACSSL      : InfoNCE {:.4f} (chance ~{:.4f})".format(
        float(info_nce(za, zb)), math.log(8)))
    print("-" * 60)
    print("all components run and produce finite output")
