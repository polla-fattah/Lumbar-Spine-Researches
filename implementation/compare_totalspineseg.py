#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Measure TotalSpineSeg's disc landmarks against RSNA's annotated coordinates.

THE QUESTION
------------
TotalSpineSeg reports 99% labelling accuracy. That is its own published figure on
its own benchmark, and it says nothing about how it performs on LumbarDISC or on
the Rizgary cohort. Before any localisation pipeline is built on it, the error
has to be measured on data where ground truth exists. RSNA is that data: it
carries a human-annotated coordinate for every one of 48,657 targets.

WHAT IS COMPARED
----------------
TotalSpineSeg segments intervertebral discs and labels them (L1-L2 ... L5-S). Its
disc centroid for a level is compared against RSNA's annotated CENTRAL CANAL
coordinate for that same level, which is annotated on sagittal T2.

Those two points are not the same anatomical structure and are not expected to
coincide exactly. The canal annotation sits posterior to the disc centre, in the
thecal sac. A systematic posterior offset of a few millimetres is the correct
result, not an error. What matters for a localisation pipeline is:

  * whether the LEVEL LABELS agree -- does TotalSpineSeg's "L4-L5" correspond to
    RSNA's "L4-L5", or is the enumeration shifted by one, which is the failure
    mode that matters and the one its landmark-based labelling is designed to
    prevent;
  * whether the offset is CONSISTENT, since a consistent offset can be corrected
    by a learned constant while a variable one cannot.

So the report separates the systematic component (the mean offset vector, which
is correctable) from the scatter about it (which is the irreducible error).

WHY THIS IS THE RIGHT TEST TO RUN FIRST
---------------------------------------
If the level labels are right and the scatter is small, a localisation pipeline
becomes a matter of applying a fixed offset per condition, learnable from RSNA.
If the labels are shifted or the scatter is large, no offset helps and the
localisation problem needs a trained detector instead. One measurement decides
between a day of work and a separate research project.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import PROJECT_ROOT  # noqa: E402
from geometry import pixel_to_patient  # noqa: E402
from roi_qc import load_series_headers  # noqa: E402

# TotalSpineSeg disc label values for the five lumbar levels.
#
# These are not documented in a table shipped with the package; they are derived
# from its own labelling command, which sets
#     --disc-landmark-output-labels 63 71 91 100
# for the landmark discs C2-C3, C7-T1, T12-L1 and L5-S, numbering the discs
# between them sequentially. That puts T12-L1 at 91 and L5-S at 100, so the five
# lumbar discs are 92-95 and 100.
#
# The inference was then VERIFIED against the segmentation rather than trusted:
# world-space z decreases monotonically from 91 through 95 to 100 (superior to
# inferior), and vertebra label 41 (L1) sits between discs 91 and 92, which is
# where L1 belongs. A silently shifted enumeration is the failure mode this
# whole comparison exists to detect, so the mapping it depends on is checked.
DISC_LABELS = {"L1-L2": 92, "L2-L3": 93, "L3-L4": 94, "L4-L5": 95, "L5-S1": 100}


def disc_centroids_ras(seg_path):
    """Centroid of each lumbar disc label, in the segmentation's world space."""
    import nibabel as nib
    img = nib.load(seg_path)
    data = np.asarray(img.dataobj)
    aff = img.affine
    out = {}
    for level, lab in DISC_LABELS.items():
        idx = np.argwhere(data == lab)
        if idx.size == 0:
            continue
        c = idx.mean(axis=0)
        h = np.array([c[0], c[1], c[2], 1.0])
        out[level] = (aff @ h)[:3]
    return out, sorted(int(v) for v in np.unique(data) if v > 0)


def rsna_canal_ras(study_id, index):
    """RSNA central-canal annotation per level, converted to RAS world space."""
    sub = index[(index.study_id == study_id) &
                (index.condition_key == "central_canal")]
    out = {}
    for _, r in sub.iterrows():
        heads = load_series_headers(study_id, int(r.series_id))
        src = next((h for h in heads
                    if h["instance"] == int(r.instance_number)), None)
        if src is None:
            continue
        lps = pixel_to_patient(src["ipp"], src["iop"], src["ps"], r.x, r.y)
        # DICOM LPS -> NIfTI RAS
        out[r.level_key] = np.array([-lps[0], -lps[1], lps[2]])
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seg_dir", required=True,
                    help="TotalSpineSeg output folder containing the labelled "
                         "segmentations (step2_output)")
    ap.add_argument("--out", default=os.path.join(
        PROJECT_ROOT, "data", "reports", "totalspineseg_vs_rsna.csv"))
    args = ap.parse_args()

    import pandas as pd

    index = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "cache",
                                     "rsna_roi_v2_index.csv"))

    segs = [f for f in sorted(os.listdir(args.seg_dir))
            if f.endswith(".nii.gz") or f.endswith(".nii")]
    if not segs:
        print("[FAIL] no segmentations in {}".format(args.seg_dir))
        return 1

    rows, labels_seen = [], set()
    for f in segs:
        stem = f.split(".")[0]
        try:
            study_id = int(stem.split("_")[0])
        except ValueError:
            print("  [skip] cannot parse study id from {}".format(f))
            continue
        pred, present = disc_centroids_ras(os.path.join(args.seg_dir, f))
        labels_seen.update(present)
        truth = rsna_canal_ras(study_id, index)
        for level in DISC_LABELS:
            if level in pred and level in truth:
                d = pred[level] - truth[level]
                rows.append(dict(study_id=study_id, level=level,
                                 dx=d[0], dy=d[1], dz=d[2],
                                 dist_mm=float(np.linalg.norm(d))))
            else:
                rows.append(dict(study_id=study_id, level=level,
                                 dx=np.nan, dy=np.nan, dz=np.nan,
                                 dist_mm=np.nan))

    df = pd.DataFrame(rows)
    ok = df.dropna(subset=["dist_mm"])
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)

    print("=" * 74)
    print("  TotalSpineSeg disc centroid vs RSNA central-canal annotation")
    print("=" * 74)
    print("  studies {}   levels matched {} of {}".format(
        df.study_id.nunique(), len(ok), len(df)))
    if not len(ok):
        print("  [FAIL] no level matched. Label values present in the "
              "segmentation: {}".format(sorted(labels_seen)[:40]))
        print("  DISC_LABELS may need updating for this TotalSpineSeg version.")
        return 1

    print("")
    print("  RAW DISTANCE (these are different structures, so a few mm is expected)")
    print("    median {:.1f} mm   90th pct {:.1f} mm   max {:.1f} mm".format(
        ok.dist_mm.median(), ok.dist_mm.quantile(0.9), ok.dist_mm.max()))

    mu = ok[["dx", "dy", "dz"]].mean().to_numpy()
    resid = ok[["dx", "dy", "dz"]].to_numpy() - mu
    rd = np.linalg.norm(resid, axis=1)
    print("")
    print("  SYSTEMATIC OFFSET (correctable by a learned constant)")
    print("    mean vector  x {:+.1f}  y {:+.1f}  z {:+.1f} mm   "
          "magnitude {:.1f} mm".format(mu[0], mu[1], mu[2],
                                       float(np.linalg.norm(mu))))
    print("")
    print("  SCATTER ABOUT IT (the irreducible part)")
    print("    median {:.1f} mm   90th pct {:.1f} mm   max {:.1f} mm".format(
        np.median(rd), np.percentile(rd, 90), rd.max()))

    print("")
    print("  PER LEVEL")
    print("  {:<8}{:>8}{:>12}{:>12}".format("level", "n", "median mm",
                                            "scatter mm"))
    for lv in DISC_LABELS:
        g = ok[ok.level == lv]
        if not len(g):
            print("  {:<8}{:>8}{:>12}{:>12}".format(lv, 0, "--", "--"))
            continue
        gr = np.linalg.norm(g[["dx", "dy", "dz"]].to_numpy() - mu, axis=1)
        print("  {:<8}{:>8}{:>12.1f}{:>12.1f}".format(
            lv, len(g), g.dist_mm.median(), float(np.median(gr))))

    print("")
    print("  VERDICT")
    med_scatter = float(np.median(rd))
    if med_scatter < 5.0:
        print("    Scatter about the systematic offset is {:.1f} mm. A fixed "
              "per-condition".format(med_scatter))
        print("    offset learned from RSNA would place targets to within a few "
              "millimetres,")
        print("    which is inside the 4 mm slice thickness. The localisation "
              "path is viable.")
    elif med_scatter < 10.0:
        print("    Scatter is {:.1f} mm -- borderline. Usable for a review "
              "interface where a".format(med_scatter))
        print("    human confirms placement, marginal for unattended grading.")
    else:
        print("    Scatter is {:.1f} mm. Too large for a fixed offset; "
              "localisation needs a".format(med_scatter))
        print("    trained detector rather than a segmentation plus a constant.")
    print("")
    print("  {}".format(os.path.relpath(args.out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
