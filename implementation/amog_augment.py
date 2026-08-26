#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MRI-safe training augmentation (Chapter 3 sec:method-augmentation).

Chapter 3: "Training augmentation is designed to simulate plausible MRI
variability without altering disease anatomy. Candidate transforms include
modest intensity scaling, gamma/contrast change, bias-field simulation, noise,
small translation/rotation and limited elastic deformation. Aggressive
transformations that distort the canal or foraminal morphology beyond plausible
acquisition variation are excluded."

WHY THERE ARE NO FLIPS, DESPITE CHAPTER 3 DESCRIBING ONE
--------------------------------------------------------
sec:method-augmentation provides for a laterality-aware horizontal flip that
swaps left/right labels and graph node identity. That provision assumes a
representation in which a horizontal flip corresponds to a left-right mirror.
For the per-target 2.5D crops this pipeline uses, it does not:

  * In a SAGITTAL image the in-plane axes are anterior-posterior and
    superior-inferior. Left-right is THROUGH plane. A horizontal flip therefore
    mirrors anterior against posterior -- placing the vertebral body behind the
    spinal canal. That is anatomically impossible, and no label swap repairs it.

  * In an AXIAL image left-right IS in-plane, so a horizontal flip is a genuine
    mirror and would require swapping left_foraminal <-> right_foraminal,
    left_subarticular <-> right_subarticular, and the corresponding graph nodes.

  * Every target carries BOTH planes at once: (M, 3, H, W) over
    [sag_t1, sag_t2, ax_t2]. So no single horizontal flip is simultaneously
    valid across a target's own channels. Flipping the axial channel alone would
    swap the laterality the label describes while the two sagittal channels
    continue to depict the original side.

Rather than apply a transform that is valid for one third of each input and
invalid for the rest, flips are excluded and the reason recorded. Every
transform kept below is label-preserving by construction, which is what
sec:method-augmentation actually requires -- "without altering disease anatomy".

If a future representation separates the planes, the swap is
CONDITION_MIRROR / mirror_node_ids below, already implemented and tested.
"""
from __future__ import annotations

import os
import sys

import torch

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import CONDITIONS, LUMBAR_LEVELS  # noqa: E402

N_CONDITIONS = len(CONDITIONS)
N_LEVELS = len(LUMBAR_LEVELS)

# CONDITIONS order is left_foraminal, left_subarticular, central_canal,
# right_subarticular, right_foraminal -- symmetric about the midline, so the
# laterality mirror is a reversal. Kept and tested even though no current
# transform triggers it, because a wrong mirror is silent and expensive.
CONDITION_MIRROR = [N_CONDITIONS - 1 - i for i in range(N_CONDITIONS)]


def mirror_node_ids() -> torch.Tensor:
    """Graph node permutation under a left-right mirror.

    node_id = level * N_CONDITIONS + condition, so mirroring maps
    (level, c) -> (level, CONDITION_MIRROR[c]).
    """
    idx = []
    for lv in range(N_LEVELS):
        for c in range(N_CONDITIONS):
            idx.append(lv * N_CONDITIONS + CONDITION_MIRROR[c])
    return torch.tensor(idx, dtype=torch.long)


class MRIAugment:
    """Label-preserving intensity and small-geometry augmentation.

    Operates on a (..., H, W) float tensor in roughly [0, 1].

    The intensity, gamma, bias-field and affine transforms draw ONE parameter
    per call and apply it to every slice, so the 2.5D stack of a crop stays
    mutually consistent. Independently rotating or re-scaling neighbouring
    slices would manufacture through-plane variation the scanner never produced,
    and the graph rungs read exactly that kind of structure.

    Noise is the deliberate exception: it is sampled per voxel, including across
    slices, because MRI thermal noise genuinely is independent per voxel. A
    noise field shared across a stack would be an artefact, not a simulation.
    """

    def __init__(self, intensity=0.15, gamma=0.20, noise=0.02, bias=0.15,
                 translate=0.05, rotate_deg=7.0, p=0.8):
        self.intensity = intensity
        self.gamma = gamma
        self.noise = noise
        self.bias = bias
        self.translate = translate
        self.rotate_deg = rotate_deg
        self.p = p

    # -- intensity ------------------------------------------------------- #
    def _scale(self, x):
        f = 1.0 + (torch.rand(1, device=x.device) * 2 - 1) * self.intensity
        return x * f

    def _gamma(self, x):
        g = torch.exp((torch.rand(1, device=x.device) * 2 - 1) * self.gamma)
        return x.clamp(min=0).pow(g)

    def _noise(self, x):
        return x + torch.randn_like(x) * (torch.rand(1, device=x.device) * self.noise)

    def _bias_field(self, x):
        """Smooth multiplicative field, the dominant MRI intensity artefact."""
        h, w = x.shape[-2:]
        yy = torch.linspace(-1, 1, h, device=x.device).view(-1, 1)
        xx = torch.linspace(-1, 1, w, device=x.device).view(1, -1)
        a = (torch.rand(3, device=x.device) * 2 - 1) * self.bias
        field = 1.0 + a[0] * xx + a[1] * yy + a[2] * xx * yy
        return x * field

    # -- small geometry -------------------------------------------------- #
    def _affine(self, x):
        """Small rotation and translation only.

        Simulates patient positioning and localiser jitter. Deliberately small:
        sec:method-augmentation excludes transforms that distort canal or
        foraminal morphology beyond plausible acquisition variation, and these
        crops are already tight around the target.
        """
        import torch.nn.functional as F
        shape = x.shape
        v = x.reshape(-1, 1, shape[-2], shape[-1])
        ang = (torch.rand(1, device=x.device) * 2 - 1) * self.rotate_deg * 3.14159 / 180.0
        tx = (torch.rand(1, device=x.device) * 2 - 1) * self.translate
        ty = (torch.rand(1, device=x.device) * 2 - 1) * self.translate
        cos, sin = torch.cos(ang), torch.sin(ang)
        theta = torch.zeros(v.size(0), 2, 3, device=x.device, dtype=v.dtype)
        theta[:, 0, 0] = cos; theta[:, 0, 1] = -sin; theta[:, 0, 2] = tx
        theta[:, 1, 0] = sin; theta[:, 1, 1] = cos;  theta[:, 1, 2] = ty
        grid = F.affine_grid(theta, v.shape, align_corners=False)
        v = F.grid_sample(v, grid, mode="bilinear", padding_mode="border",
                          align_corners=False)
        return v.reshape(shape)

    def __call__(self, x):
        if self.p <= 0 or float(torch.rand(1)) > self.p:
            return x
        if self.intensity > 0:
            x = self._scale(x)
        if self.gamma > 0:
            x = self._gamma(x)
        if self.bias > 0:
            x = self._bias_field(x)
        if self.rotate_deg > 0 or self.translate > 0:
            x = self._affine(x)
        if self.noise > 0:
            x = self._noise(x)
        return x.clamp(0.0, 1.0)


def describe(a: "MRIAugment") -> dict:
    """What was applied, for the run's provenance record."""
    return {
        "intensity_scale": a.intensity, "gamma": a.gamma, "noise_sigma": a.noise,
        "bias_field": a.bias, "translate_frac": a.translate,
        "rotate_deg": a.rotate_deg, "apply_prob": a.p,
        "horizontal_flip": False,
        "flip_excluded_because": (
            "a target carries sagittal and axial channels together; a horizontal "
            "flip mirrors anterior-posterior in sagittal and left-right in axial, "
            "so no single flip is valid across one target's own channels"),
    }
