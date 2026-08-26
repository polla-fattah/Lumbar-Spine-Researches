#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MRI-safe training augmentation (Chapter 3 sec:method-augmentation).

Chapter 3: "Training augmentation is designed to simulate plausible MRI
variability without altering disease anatomy. Candidate transforms include
modest intensity scaling, gamma/contrast change, bias-field simulation, noise,
small translation/rotation and limited elastic deformation. Aggressive
transformations that distort the canal or foraminal morphology beyond plausible
acquisition variation are excluded."

WHERE THIS RUNS, AND WHY IT MATTERS
-----------------------------------
On the batch, on the GPU, inside the training loop -- not per sample in the
dataset. Measured on this machine before the change:

    1 crop fetch + float32 conversion   0.053 ms
    3 crops for a multi-sequence target 0.264 ms
    augmentation                        1.789 ms   <- 87% of the data cost

    34,034 samples/epoch = ~70 s of CPU work against an observed ~78 s epoch.

PyTorch on Windows spawns rather than forks, so `loader_kwargs` pins
num_workers to 0 and every sample was prepared serially in the main process
while a 32 GB card idled at 2-3% utilisation. affine_grid/grid_sample is pure
tensor arithmetic and belongs on the device that was already sitting empty.

Parameters are drawn PER SAMPLE, not per batch, so a batch still contains B
different transforms and augmentation diversity is unchanged by the move.

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
    valid across a target's own channels.

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
import torch.nn.functional as F

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
    """Label-preserving intensity and small-geometry augmentation, batched.

    Call with a tensor whose FIRST dimension is the sample: (B, ..., H, W).
    Leading dimensions between B and H are preserved, so it accepts both the
    (B, M, C, H, W) of a multi-sequence target and the (B, N, M, C, H, W) of a
    patient graph.

    One parameter set is drawn per SAMPLE and shared across everything inside
    that sample. That is deliberate: the 2.5D slices and the sequences of one
    target must undergo the same geometric transform, or the stack acquires
    through-plane structure the scanner never produced -- and the graph rungs
    read exactly that kind of structure.

    Noise is the exception, sampled per voxel, because MRI thermal noise
    genuinely is independent per voxel. A noise field shared across a stack
    would be an artefact rather than a simulation.
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

    def __call__(self, x):
        if self.p <= 0:
            return x
        B = x.shape[0]
        dev, dt = x.device, x.dtype
        lead = (B,) + (1,) * (x.dim() - 1)          # broadcast over everything
        H, W = x.shape[-2], x.shape[-1]

        # which samples get augmented at all
        active = (torch.rand(B, device=dev) < self.p).view(lead).to(dt)

        def per_sample(scale):
            return ((torch.rand(B, device=dev, dtype=dt) * 2 - 1) * scale).view(lead)

        out = x
        if self.intensity > 0:
            out = out * (1.0 + per_sample(self.intensity) * active)
        if self.gamma > 0:
            g = torch.exp(per_sample(self.gamma) * active)
            out = out.clamp(min=0).pow(g)
        if self.bias > 0:
            yy = torch.linspace(-1, 1, H, device=dev, dtype=dt).view(1, H, 1)
            xx = torch.linspace(-1, 1, W, device=dev, dtype=dt).view(1, 1, W)
            a0, a1, a2 = (per_sample(self.bias).reshape(B, 1, 1) for _ in range(3))
            field = 1.0 + a0 * xx + a1 * yy + a2 * xx * yy       # (B, H, W)
            out = out * field.reshape((B,) + (1,) * (x.dim() - 3) + (H, W))
        if self.rotate_deg > 0 or self.translate > 0:
            out = self._affine(out, active.reshape(B))
        if self.noise > 0:
            sig = (torch.rand(B, device=dev, dtype=dt) * self.noise).view(lead)
            out = out + torch.randn_like(out) * sig * active
        return out.clamp(0.0, 1.0)

    def _affine(self, x, active):
        """One batched grid_sample for the whole batch.

        Small rotation and translation only: sec:method-augmentation excludes
        transforms that distort canal or foraminal morphology beyond plausible
        acquisition variation, and these crops are already tight on the target.
        """
        B = x.shape[0]
        dev, dt = x.device, x.dtype
        H, W = x.shape[-2], x.shape[-1]
        flat = x.reshape(-1, 1, H, W)
        rep = flat.shape[0] // B                    # planes per sample

        ang = (torch.rand(B, device=dev, dtype=dt) * 2 - 1) \
            * (self.rotate_deg * 3.141592653589793 / 180.0) * active
        tx = (torch.rand(B, device=dev, dtype=dt) * 2 - 1) * self.translate * active
        ty = (torch.rand(B, device=dev, dtype=dt) * 2 - 1) * self.translate * active

        cos, sin = torch.cos(ang), torch.sin(ang)
        theta = torch.zeros(B, 2, 3, device=dev, dtype=dt)
        theta[:, 0, 0] = cos; theta[:, 0, 1] = -sin; theta[:, 0, 2] = tx
        theta[:, 1, 0] = sin; theta[:, 1, 1] = cos;  theta[:, 1, 2] = ty
        # every plane of a sample shares that sample's transform
        theta = theta.repeat_interleave(rep, dim=0)

        grid = F.affine_grid(theta, flat.shape, align_corners=False)
        out = F.grid_sample(flat, grid, mode="bilinear",
                            padding_mode="border", align_corners=False)
        return out.reshape(x.shape)


def describe(a: "MRIAugment") -> dict:
    """What was applied, for the run's provenance record."""
    return {
        "intensity_scale": a.intensity, "gamma": a.gamma, "noise_sigma": a.noise,
        "bias_field": a.bias, "translate_frac": a.translate,
        "rotate_deg": a.rotate_deg, "apply_prob": a.p,
        "applied": "batched on device, per-sample parameters",
        "horizontal_flip": False,
        "flip_excluded_because": (
            "a target carries sagittal and axial channels together; a horizontal "
            "flip mirrors anterior-posterior in sagittal and left-right in axial, "
            "so no single flip is valid across one target's own channels"),
    }
