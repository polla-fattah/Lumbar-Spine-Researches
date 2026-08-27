#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Can 25 target coordinates be derived from 5 disc centroids?

THE QUESTION THAT DECIDES THE LOCALISATION PIPELINE
---------------------------------------------------
TotalSpineSeg localises intervertebral DISCS -- five per lumbar spine. The
grading model needs TWENTY-FIVE targets: five levels by five conditions
(left/right foraminal, left/right subarticular, central canal). Segmentation
does not supply the missing twenty.

The proposal is that each condition sits at a roughly fixed offset from its
level's disc centre, so the twenty-five can be derived from the five by adding a
learned constant per condition. That is an assumption, and RSNA can test it
because it carries the human annotation for all twenty-five.

WHAT IS MEASURED
----------------
For every study and level, the vector from the TotalSpineSeg disc centroid to
each RSNA annotation, in patient space. Two quantities matter and they are
reported separately:

  * the MEAN offset per condition, which is the constant a pipeline would apply;
  * the SCATTER about it, which is the error that constant cannot remove.

The scatter is the answer. If it is small relative to the crop, derived
coordinates place the structure inside the field of view and the pipeline works.
If it is large, no constant helps and localisation needs a trained detector.

WHY THE LATERAL CONDITIONS ARE THE HARD CASE
--------------------------------------------
Central canal sits close to the disc in the midline, so a constant should work
there. Foraminal and subarticular targets are lateral, and how far lateral
depends on the patient's build and on the level. Those four conditions are where
this assumption is most likely to fail, and they are also the conditions on which
the grading model already performs worst.

Offsets are expressed in the PATIENT coordinate frame, not in image pixels, so
they transfer between scanners with different orientation and spacing.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import CONDITIONS, PROJECT_ROOT  # noqa: E402
from geometry import pixel_to_patient  # noqa: E402
from roi_qc import load_series_headers  # noqa: E402
from compare_totalspineseg import DISC_LABELS, disc_centroids_ras  # noqa: E402

CROP_FOV_MM = 60.0     # the physical field of view the model is given


def rsna_targets_ras(study_id, index):
    """Every annotated target for a study, in RAS world coordinates."""
    sub = index[index.study_id == study_id]
    out, cache = {}, {}
    for _, r in sub.iterrows():
        sid = int(r.series_id)
        if sid not in cache:
            cache[sid] = load_series_headers(study_id, sid)
        src = next((h for h in cache[sid]
                    if h["instance"] == int(r.instance_number)), None)
        if src is None:
            continue
        lps = pixel_to_patient(src["ipp"], src["iop"], src["ps"], r.x, r.y)
        out[(r.level_key, r.condition_key)] = np.array([-lps[0], -lps[1], lps[2]])
    return out


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seg_dir", required=True)
    ap.add_argument("--out", default=os.path.join(
        PROJECT_ROOT, "data", "reports", "target_offsets.csv"))
    args = ap.parse_args()

    import pandas as pd
    index = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "cache",
                                     "rsna_roi_v2_index.csv"))

    rows = []
    for f in sorted(os.listdir(args.seg_dir)):
        if not (f.endswith(".nii.gz") or f.endswith(".nii")):
            continue
        try:
            study_id = int(f.split(".")[0].split("_")[0])
        except ValueError:
            continue
        discs, _ = disc_centroids_ras(os.path.join(args.seg_dir, f))
        truth = rsna_targets_ras(study_id, index)
        for (level, cond), pt in truth.items():
            if level not in discs:
                continue
            d = pt - discs[level]
            rows.append(dict(study_id=study_id, level=level, condition=cond,
                             dx=d[0], dy=d[1], dz=d[2]))

    if not rows:
        print("[FAIL] no matched targets.")
        return 1
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)

    print("=" * 76)
    print("  Offset from TotalSpineSeg disc centroid to each RSNA target")
    print("  {} studies, {} target observations".format(
        df.study_id.nunique(), len(df)))
    print("=" * 76)
    print("  Patient frame: +x right, +y anterior, +z superior (mm)")
    print("")
    print("  {:<20}{:>6}{:>26}{:>12}{:>10}".format(
        "condition", "n", "mean offset (x, y, z)", "scatter", "in crop"))

    summary = []
    for cond in CONDITIONS:
        g = df[df.condition == cond]
        if not len(g):
            continue
        v = g[["dx", "dy", "dz"]].to_numpy()
        mu = v.mean(axis=0)
        resid = np.linalg.norm(v - mu, axis=1)
        med = float(np.median(resid))
        # a derived point misplaced by r still contains the structure if the
        # structure stays inside the crop centred on it
        inside = float((resid < CROP_FOV_MM / 2).mean())
        summary.append(dict(condition=cond, n=len(g), mx=mu[0], my=mu[1],
                            mz=mu[2], scatter_med=med,
                            scatter_p90=float(np.percentile(resid, 90)),
                            frac_in_crop=inside))
        print("  {:<20}{:>6}{:>10.1f}{:>8.1f}{:>8.1f}{:>10.1f}{:>9.0%}".format(
            cond, len(g), mu[0], mu[1], mu[2], med, inside))

    sdf = pd.DataFrame(summary)
    print("")
    print("  LATERALITY CHECK")
    lf = sdf[sdf.condition == "left_foraminal"].mx.iloc[0]
    rf = sdf[sdf.condition == "right_foraminal"].mx.iloc[0]
    ls = sdf[sdf.condition == "left_subarticular"].mx.iloc[0]
    rs = sdf[sdf.condition == "right_subarticular"].mx.iloc[0]
    print("    foraminal    left {:+.1f} mm   right {:+.1f} mm   separation "
          "{:.1f} mm".format(lf, rf, abs(lf - rf)))
    print("    subarticular left {:+.1f} mm   right {:+.1f} mm   separation "
          "{:.1f} mm".format(ls, rs, abs(ls - rs)))
    print("    Left and right must land on opposite sides of the midline, or a")
    print("    derived pipeline would grade the wrong side.")

    print("")
    print("  VERDICT")
    worst = sdf.scatter_med.max()
    worst_c = sdf.loc[sdf.scatter_med.idxmax(), "condition"]
    allin = sdf.frac_in_crop.min()
    print("    worst condition: {} at {:.1f} mm median scatter".format(
        worst_c, worst))
    print("    every condition keeps {:.0%}+ of targets inside a {:.0f} mm "
          "crop".format(allin, CROP_FOV_MM))
    if worst < 8.0 and allin > 0.95:
        print("    A per-condition constant offset is sufficient. Localisation")
        print("    from segmentation is viable without a trained detector.")
    elif allin > 0.90:
        print("    Usable with human confirmation of placement; the derived")
        print("    coordinate lands in the right region but not reliably centred.")
    else:
        print("    A constant offset is NOT sufficient. Localisation needs a")
        print("    trained detector rather than segmentation plus a constant.")

    out2 = args.out.replace(".csv", "_summary.csv")
    sdf.to_csv(out2, index=False)
    print("")
    print("  {}".format(os.path.relpath(args.out, PROJECT_ROOT)))
    print("  {}".format(os.path.relpath(out2, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
