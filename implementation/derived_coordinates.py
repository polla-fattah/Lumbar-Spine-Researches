#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build an ROI index from TotalSpineSeg, with no human annotation of position.

WHAT THIS REPLACES
------------------
Every result in this thesis uses RSNA's human-annotated coordinate for each of
the 25 targets. This module produces the same index from segmentation alone:

    sagittal T2 -> TotalSpineSeg -> 5 disc centroids
                -> + a per-condition offset learned on the DEV partition
                -> 25 patient-space points
                -> projected into the series each condition is graded on
                -> (series_id, instance_number, x, y), the schema the cache
                   builder already consumes

Only the POSITION is derived. Labels, splits and every other field come from the
existing index, so a comparison between the two isolates the cost of automating
localisation and nothing else.

WHY THE OFFSETS ARE FITTED ON DEV
---------------------------------
The offsets are learned parameters. Fitting them on the same studies used to
report the result would report how well a constant can be fitted, not how well
it transfers. They are therefore fitted on dev studies and applied unchanged to
test.

THE SERIES A CONDITION IS GRADED ON
-----------------------------------
LumbarDISC annotates each condition on one sequence: foraminal on sagittal T1,
subarticular on axial T2, central canal on sagittal T2. A derived point must be
projected into the correct series, or the crop shows the right anatomy through
the wrong contrast. The mapping is taken from the existing index per study
rather than assumed, because a study may lack a series.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from amog_modes import CONDITIONS, PROJECT_ROOT  # noqa: E402
from geometry import patient_to_pixel, nearest_slice  # noqa: E402
from roi_qc import load_series_headers  # noqa: E402
from compare_totalspineseg import disc_centroids_ras  # noqa: E402
from derive_target_offsets import rsna_targets_ras  # noqa: E402

LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]


def fit_offsets(seg_dir, index, studies=None):
    """Mean offset from disc centroid to each condition's target, in RAS mm."""
    acc = {c: [] for c in CONDITIONS}
    for f in sorted(os.listdir(seg_dir)):
        if not f.endswith((".nii.gz", ".nii")):
            continue
        try:
            sid = int(f.split(".")[0].split("_")[0])
        except ValueError:
            continue
        if studies is not None and sid not in studies:
            continue
        discs, _ = disc_centroids_ras(os.path.join(seg_dir, f))
        truth = rsna_targets_ras(sid, index)
        for (level, cond), pt in truth.items():
            if level in discs and cond in acc:
                acc[cond].append(pt - discs[level])
    return ({c: np.mean(v, axis=0) for c, v in acc.items() if v},
            {c: len(v) for c, v in acc.items()})


def derive_index(seg_dir, index, offsets, studies=None):
    """Rows with the same schema as the RSNA index, positions derived."""
    import pandas as pd
    rows, skipped = [], {"no_disc": 0, "no_series": 0, "off_image": 0}

    for f in sorted(os.listdir(seg_dir)):
        if not f.endswith((".nii.gz", ".nii")):
            continue
        try:
            sid = int(f.split(".")[0].split("_")[0])
        except ValueError:
            continue
        if studies is not None and sid not in studies:
            continue

        discs, _ = disc_centroids_ras(os.path.join(seg_dir, f))
        sub = index[index.study_id == sid]
        if sub.empty:
            continue

        # Every series of each modality, not just the first. A study can carry
        # several axial T2 acquisitions covering different levels, and taking
        # the first put 4.4% of derived targets in a series that does not cover
        # them -- one was 95 slices away. Which series to read is a separate
        # problem from where to read in it, and the principled answer uses no
        # human annotation: pick the series whose slices come closest to the
        # derived point.
        headers = {}
        for mod, g in sub.groupby("modality"):
            headers[mod] = []
            for sser in sorted(set(int(v) for v in g.series_id)):
                hh = load_series_headers(sid, sser)
                if hh:
                    headers[mod].append((sser, hh))

        for _, r in sub.iterrows():
            level, cond, mod = r.level_key, r.condition_key, r.modality
            if level not in discs or cond not in offsets:
                skipped["no_disc"] += 1
                continue
            cands = headers.get(mod)
            if not cands:
                skipped["no_series"] += 1
                continue

            ras = discs[level] + offsets[cond]
            lps = np.array([-ras[0], -ras[1], ras[2]])
            best = None
            for sser, hh in cands:
                i, dist = nearest_slice(lps, hh)
                if i >= 0 and (best is None or dist < best[0]):
                    best = (dist, sser, hh[i])
            if best is None:
                skipped["no_series"] += 1
                continue
            _dist, chosen_series, s = best
            col, row_, _oop = patient_to_pixel(lps, s["ipp"], s["iop"], s["ps"])
            if not (0 <= col < s["cols"] and 0 <= row_ < s["rows"]):
                skipped["off_image"] += 1
                # keep it: the cache builder clamps, and dropping targets would
                # change the denominator and make the comparison incomparable
            rows.append(dict(
                study_id=sid, series_id=chosen_series,
                instance_number=int(s["instance"]),
                x=float(col), y=float(row_),
                condition_key=cond, level_key=level, modality=mod,
                label=int(r.label)))
    return pd.DataFrame(rows), skipped


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dev_seg", required=True, help="segmentations of dev studies")
    ap.add_argument("--test_seg", required=True, help="segmentations of test studies")
    ap.add_argument("--out", default=os.path.join(
        PROJECT_ROOT, "data", "cache", "rsna_roi_derived_index.csv"))
    args = ap.parse_args()

    import pandas as pd
    index = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "cache",
                                     "rsna_roi_v2_index.csv"))
    split = pd.read_csv(os.path.join(PROJECT_ROOT, "implementation", "splits",
                                     "rsna_patient_split.csv"))
    dev = set(split.loc[split.partition.isin(["train", "val"]),
                        "study_id"].astype(int))
    test = set(split.loc[split.partition == "test", "study_id"].astype(int))

    print("  fitting offsets on the dev partition...")
    offsets, counts = fit_offsets(args.dev_seg, index, studies=dev)
    if not offsets:
        print("[FAIL] no dev studies matched; cannot fit offsets.")
        return 1
    for c in CONDITIONS:
        if c in offsets:
            o = offsets[c]
            print("    {:<20} n={:<5} ({:+.1f}, {:+.1f}, {:+.1f}) mm".format(
                c, counts[c], o[0], o[1], o[2]))

    print("")
    print("  deriving test coordinates...")
    df, skipped = derive_index(args.test_seg, index, offsets, studies=test)
    if df.empty:
        print("[FAIL] no test rows derived.")
        return 1

    truth = index[index.study_id.isin(set(df.study_id))]
    print("    derived {} rows over {} studies".format(len(df), df.study_id.nunique()))
    print("    reference has {} rows for the same studies".format(len(truth)))
    print("    skipped: {}".format(skipped))

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    df.to_csv(args.out, index=False)
    np.save(args.out.replace("_index.csv", "_offsets.npy"),
            np.array([offsets[c] for c in CONDITIONS if c in offsets]))
    print("")
    print("  {}".format(os.path.relpath(args.out, PROJECT_ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
