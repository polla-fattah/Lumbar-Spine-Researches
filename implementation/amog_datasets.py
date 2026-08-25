#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Datasets for E0-E7, backed by the memory-mapped ROI caches.

    ROIDataset            one annotated ROI            -> E0
    MultiSequenceDataset  one target, up to 3 sequences -> E1, E2, E3, E4
    PatientGraphDataset   one patient, 25 target nodes  -> E5, E6, E7

WHY MULTI-SEQUENCE NEEDS TWO CACHES
-----------------------------------
RSNA annotates each condition on exactly one modality, so a target's other
sequences are not annotated anywhere. They are derived: the annotated keypoint is
lifted into patient space through the real DICOM affine and projected into the
other series (build_crosssequence_index.py). Those projected crops live in their
own cache because they sit at different pixel coordinates than the annotations.

    rsna_roi_v2        annotated ROIs      (source modality)
    rsna_xseq_v2       geometry-derived    (the other modalities)

A target keeps its annotated sequence always, and gains derived sequences only
where the projection was accepted. Availability is therefore genuinely variable
across the cohort, which is exactly the condition the router and the modality
dropout of E2/E3 exist to handle. It is not simulated.

MISSING DATA
------------
Absence is represented by a mask, never by a zero image. A model is told which
sequences exist rather than being left to infer it from blank pixels.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import LUMBAR_LEVELS, CONDITIONS, N_CLASSES  # noqa: E402
from amog_models import MODALITIES, N_MODALITIES, N_TARGETS, node_id  # noqa: E402
from rsna_data import load_cache  # noqa: E402

LEVEL_TO_IDX = {l: i for i, l in enumerate(LUMBAR_LEVELS)}
COND_TO_IDX = {c: i for i, c in enumerate(CONDITIONS)}
MOD_TO_IDX = {m: i for i, m in enumerate(MODALITIES)}


def _to_tensor(mm, i):
    return torch.from_numpy(np.asarray(mm[i], dtype=np.float32))


# --------------------------------------------------------------------------- #
class ROIDataset(Dataset):
    """E0: a single annotated ROI and its grade."""

    is_synthetic = False

    def __init__(self, mm, rows: pd.DataFrame):
        self.mm = mm
        self.rows = rows.reset_index(drop=True)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows.iloc[i]
        return _to_tensor(self.mm, int(r.cache_idx)), torch.tensor(int(r.label))


# --------------------------------------------------------------------------- #
class MultiSequenceDataset(Dataset):
    """E1-E4: one (patient, level, condition) target across available sequences.

    Returns
        images  (M, 3, H, W)  zero-filled where a sequence is absent
        mask    (M,)          1 where the sequence genuinely exists
        cond    ()            condition index, for the router's embedding
        level   ()            level index
        label   ()            ordinal grade
    """

    is_synthetic = False

    def __init__(self, targets: pd.DataFrame, mm_ann, mm_xseq=None, crop: int = 128):
        self.t = targets.reset_index(drop=True)
        self.mm_ann = mm_ann
        self.mm_xseq = mm_xseq
        self.crop = crop

    def __len__(self):
        return len(self.t)

    def __getitem__(self, i):
        r = self.t.iloc[i]
        imgs = torch.zeros(N_MODALITIES, 3, self.crop, self.crop)
        mask = torch.zeros(N_MODALITIES)

        for m_i, m in enumerate(MODALITIES):
            ann = r.get("ann_{}".format(m), -1)
            if ann is not None and ann >= 0:
                imgs[m_i] = _to_tensor(self.mm_ann, int(ann))
                mask[m_i] = 1.0
                continue
            if self.mm_xseq is not None:
                xs = r.get("xseq_{}".format(m), -1)
                if xs is not None and xs >= 0:
                    imgs[m_i] = _to_tensor(self.mm_xseq, int(xs))
                    mask[m_i] = 1.0

        return (imgs, mask,
                torch.tensor(int(r.condition_idx)),
                torch.tensor(int(r.level_idx)),
                torch.tensor(int(r.label)),
                torch.tensor(int(r.study_id)))


# --------------------------------------------------------------------------- #
class PatientGraphDataset(Dataset):
    """E5-E7: one patient as 25 target nodes.

    Two kinds of absence are kept apart, per Chapter 3:

        label_mask     0 = no ground truth for this node in this cohort
        evidence_mask  0 = no usable image evidence for this node

    A node may be unlabelled yet observable, and must still be allowed to compute
    a representation and pass messages. Suppressing it because its label is
    missing would confuse missing supervision with missing anatomy and would
    change the trained graph at external deployment.
    """

    is_synthetic = False

    def __init__(self, targets: pd.DataFrame, mm_ann, mm_xseq=None, crop: int = 128):
        self.mm_ann = mm_ann
        self.mm_xseq = mm_xseq
        self.crop = crop
        self.patients = sorted(targets.study_id.unique())
        self.by_patient = {p: g for p, g in targets.groupby("study_id")}

    def __len__(self):
        return len(self.patients)

    def __getitem__(self, i):
        pid = self.patients[i]
        g = self.by_patient[pid]

        imgs = torch.zeros(N_TARGETS, N_MODALITIES, 3, self.crop, self.crop)
        mask = torch.zeros(N_TARGETS, N_MODALITIES)
        labels = torch.full((N_TARGETS,), -1, dtype=torch.long)
        label_mask = torch.zeros(N_TARGETS)
        evidence = torch.zeros(N_TARGETS)

        for r in g.itertuples(index=False):
            n = node_id(int(r.level_idx), int(r.condition_idx))
            for m_i, m in enumerate(MODALITIES):
                ann = getattr(r, "ann_{}".format(m), -1)
                if ann is not None and ann >= 0:
                    imgs[n, m_i] = _to_tensor(self.mm_ann, int(ann))
                    mask[n, m_i] = 1.0
                    continue
                if self.mm_xseq is not None:
                    xs = getattr(r, "xseq_{}".format(m), -1)
                    if xs is not None and xs >= 0:
                        imgs[n, m_i] = _to_tensor(self.mm_xseq, int(xs))
                        mask[n, m_i] = 1.0
            if mask[n].sum() > 0:
                evidence[n] = 1.0
            if int(r.label) >= 0:
                labels[n] = int(r.label)
                label_mask[n] = 1.0

        return imgs, mask, labels, label_mask, evidence, torch.tensor(int(pid))


# --------------------------------------------------------------------------- #
#  synthetic counterparts for smoke mode
# --------------------------------------------------------------------------- #
class SyntheticMultiSequence(Dataset):
    is_synthetic = True

    def __init__(self, n=64, crop=64, seed=0):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.randn(n, N_MODALITIES, 3, crop, crop, generator=g)
        self.m = (torch.rand(n, N_MODALITIES, generator=g) > 0.3).float()
        self.m[self.m.sum(1) == 0] = 1.0
        self.c = torch.randint(0, len(CONDITIONS), (n,), generator=g)
        self.l = torch.randint(0, len(LUMBAR_LEVELS), (n,), generator=g)
        self.y = torch.randint(0, N_CLASSES, (n,), generator=g)
        # synthetic patients, so paired comparisons work in smoke mode too
        self.p = torch.arange(n) // 4

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        return self.x[i], self.m[i], self.c[i], self.l[i], self.y[i], self.p[i]


class SyntheticPatientGraph(Dataset):
    is_synthetic = True

    def __init__(self, n=16, crop=64, seed=0):
        g = torch.Generator().manual_seed(seed)
        self.x = torch.randn(n, N_TARGETS, N_MODALITIES, 3, crop, crop, generator=g)
        self.m = (torch.rand(n, N_TARGETS, N_MODALITIES, generator=g) > 0.4).float()
        self.y = torch.randint(0, N_CLASSES, (n, N_TARGETS), generator=g)
        self.lm = (torch.rand(n, N_TARGETS, generator=g) > 0.2).float()
        self.ev = (self.m.sum(-1) > 0).float()

    def __len__(self):
        return len(self.y)

    def __getitem__(self, i):
        return (self.x[i], self.m[i], self.y[i], self.lm[i], self.ev[i],
                torch.tensor(i))


# --------------------------------------------------------------------------- #
#  target table assembly
# --------------------------------------------------------------------------- #
def build_target_table(ann_index: pd.DataFrame,
                       xseq_index: pd.DataFrame | None = None) -> pd.DataFrame:
    """Collapse per-ROI rows into one row per (patient, level, condition).

    Columns ann_<modality> / xseq_<modality> hold the cache row index for that
    sequence, or -1 when it is absent.
    """
    a = ann_index.copy()
    a["cache_idx"] = np.arange(len(a))
    a["level_idx"] = a["level_key"].map(LEVEL_TO_IDX)
    a["condition_idx"] = a["condition_key"].map(COND_TO_IDX)
    a = a.dropna(subset=["level_idx", "condition_idx"])
    a["level_idx"] = a["level_idx"].astype(int)
    a["condition_idx"] = a["condition_idx"].astype(int)

    keys = ["study_id", "level_idx", "condition_idx"]
    base = a.groupby(keys, as_index=False).agg(label=("label", "first"))

    for m in MODALITIES:
        sub = a[a.modality == m].groupby(keys, as_index=False).agg(
            **{"ann_{}".format(m): ("cache_idx", "first")})
        base = base.merge(sub, on=keys, how="left")
        base["ann_{}".format(m)] = base["ann_{}".format(m)].fillna(-1).astype(int)

    if xseq_index is not None and len(xseq_index):
        x = xseq_index.copy()
        x["cache_idx"] = np.arange(len(x))
        x["level_idx"] = x["level_key"].map(LEVEL_TO_IDX)
        x["condition_idx"] = x["condition_key"].map(COND_TO_IDX)
        x = x.dropna(subset=["level_idx", "condition_idx"])
        x["level_idx"] = x["level_idx"].astype(int)
        x["condition_idx"] = x["condition_idx"].astype(int)
        for m in MODALITIES:
            sub = x[x.modality == m].sort_values("oop_mm").groupby(
                keys, as_index=False).agg(**{"xseq_{}".format(m): ("cache_idx", "first")})
            base = base.merge(sub, on=keys, how="left")
            base["xseq_{}".format(m)] = base["xseq_{}".format(m)].fillna(-1).astype(int)
    else:
        for m in MODALITIES:
            base["xseq_{}".format(m)] = -1

    avail = np.zeros(len(base), dtype=int)
    for m in MODALITIES:
        avail += ((base["ann_{}".format(m)] >= 0) | (base["xseq_{}".format(m)] >= 0)).astype(int)
    base["n_sequences"] = avail
    return base


if __name__ == "__main__":
    from rsna_data import CACHE_DIR
    print("amog_datasets self-test")
    print("-" * 62)
    ds = SyntheticMultiSequence(8, crop=32)
    x, m, c, l, y = ds[0]
    print("synthetic multi-seq : images {}, mask {}, avail {}".format(
        tuple(x.shape), tuple(m.shape), int(m.sum())))
    gds = SyntheticPatientGraph(4, crop=32)
    xi, mi, yi, lmi, evi, pid = gds[0]
    print("synthetic graph     : nodes {}, labelled {}, with evidence {}".format(
        xi.shape[0], int(lmi.sum()), int(evi.sum())))

    ann_p = os.path.join(CACHE_DIR, ANN_CACHE + "_index.csv")
    if os.path.exists(ann_p):
        ann = pd.read_csv(ann_p)
        xseq_p = os.path.join(CACHE_DIR, "crosssequence_index.csv")
        xseq = pd.read_csv(xseq_p) if os.path.exists(xseq_p) else None
        tt = build_target_table(ann, xseq)
        print("\nreal target table   : {:,} targets, {:,} patients".format(
            len(tt), tt.study_id.nunique()))
        print("sequences per target:")
        for k, v in tt.n_sequences.value_counts().sort_index().items():
            print("   {} sequence(s): {:>7,}  ({:.1f}%)".format(
                int(k), int(v), 100.0 * v / len(tt)))
    print("-" * 62)
