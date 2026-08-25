#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Derive multi-sequence ROI stacks from DICOM patient-space geometry.

THE PROBLEM THIS SOLVES
-----------------------
RSNA annotates each condition on exactly one modality: central canal on sagittal
T2, foraminal on sagittal T1, subarticular on axial T2. Across 48,657 labelled
(patient, level, condition) targets, the number carrying more than one modality
is ZERO. So E1 has nothing to fuse and the E2/E3 router has nothing to route --
picking a modality per condition would be a fixed lookup, not a learned gate.

THE FIX, WHICH IS ALSO THE THESIS
---------------------------------
Chapter 3 argues that anatomical correspondence between sequences is already
present in the DICOM headers and has been treated as a preprocessing convenience
rather than as a signal. Here it becomes the signal: an annotated keypoint is
lifted into patient space, then projected into the other series of the same
study. That yields a genuine multi-sequence view of one physical location, which
is exactly what Core Contribution I claims and what Core Contribution II needs
something to route over.

METHOD
    1. keypoint (col,row) on slice s of series A  ->  P in patient mm
    2. for every other series B of the same study, find the slice whose plane is
       nearest to P
    3. project P onto that slice -> (col,row) plus an out-of-plane distance
    4. keep the projection only if it lands inside the image and close enough to
       the plane; otherwise record WHY it was rejected

Rejections are counted and reported rather than hidden, because the fraction of
targets that gain a usable second sequence is itself a result: it bounds how much
of the cohort the multi-sequence contributions can apply to.

OUTPUT
    data/cache/crosssequence_index.csv
    data/cache/crosssequence_stats.json

USAGE
    python build_crosssequence_index.py --max_oop 12
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_modes import PROJECT_ROOT  # noqa: E402
from geometry import pixel_to_patient, plane_basis  # noqa: E402
from rsna_data import MODALITY_MAP  # noqa: E402
from dataset_config import resolve_dataset_dir, DEFAULT_HINTS_RSNA  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CACHE = os.path.join(PROJECT_ROOT, "data", "cache")
GEOM_CSV = os.path.join(CACHE, "series_geometry.csv")
ROI_INDEX = os.path.join(CACHE, "rsna_roi_v1_index.csv")
OUT_CSV = os.path.join(CACHE, "crosssequence_index.csv")
OUT_JSON = os.path.join(CACHE, "crosssequence_stats.json")


def main():
    ap = argparse.ArgumentParser(description="Geometry-derived cross-sequence ROIs")
    ap.add_argument("--rsna_dir", type=str, default=None)
    ap.add_argument("--max_oop", type=float, default=12.0,
                    help="max |out-of-plane| distance in mm to accept a projection")
    ap.add_argument("--margin", type=int, default=16,
                    help="required margin in px from the image edge")
    args = ap.parse_args()

    print("=" * 74)
    print("  Geometry-Derived Cross-Sequence ROI Index")
    print("=" * 74)

    for p in (GEOM_CSV, ROI_INDEX):
        if not os.path.exists(p):
            print("[FAIL] missing {}".format(os.path.relpath(p, PROJECT_ROOT)))
            print("       run build_series_geometry.py and build_roi_cache.py first")
            return 2

    rsna_dir, ok = resolve_dataset_dir(args.rsna_dir, "RSNA_DATASET_DIR",
                                       DEFAULT_HINTS_RSNA, "RSNA")
    if not ok:
        return 2

    print("\nLoading geometry and annotations...")
    geom = pd.read_csv(GEOM_CSV)
    roi = pd.read_csv(ROI_INDEX)
    desc = pd.read_csv(os.path.join(rsna_dir, "train_series_descriptions.csv"))
    desc["modality"] = desc["series_description"].map(MODALITY_MAP)
    desc = desc.dropna(subset=["modality"])
    print("  {:,} slices, {:,} annotated ROIs".format(len(geom), len(roi)))

    # index geometry by (study, series) for fast lookup
    geom = geom.sort_values(["study_id", "series_id", "instance_number"])
    by_series = {k: v for k, v in geom.groupby(["study_id", "series_id"])}
    slice_lookup = {}
    for (st, se), g in by_series.items():
        slice_lookup[(st, se)] = g.set_index("instance_number")

    series_by_study = {}
    for st, g in desc.groupby("study_id"):
        series_by_study[st] = list(zip(g.series_id.tolist(), g.modality.tolist()))

    out_rows = []
    stats = {
        "annotated_targets": int(len(roi)),
        "candidate_projections": 0,
        "accepted": 0,
        "rejected_no_geometry": 0,
        "rejected_out_of_plane": 0,
        "rejected_out_of_bounds": 0,
        "oop_mm_accepted": [],
    }

    t0 = time.time()
    for n, r in enumerate(roi.itertuples(index=False), 1):
        st, se, inst = int(r.study_id), int(r.series_id), int(r.instance_number)
        src = slice_lookup.get((st, se))
        if src is None or inst not in src.index:
            stats["rejected_no_geometry"] += 1
            continue
        s = src.loc[inst]
        if isinstance(s, pd.DataFrame):
            s = s.iloc[0]

        try:
            P = pixel_to_patient(
                [s.ipp_x, s.ipp_y, s.ipp_z],
                [s.iop_0, s.iop_1, s.iop_2, s.iop_3, s.iop_4, s.iop_5],
                [s.ps_row, s.ps_col], r.x, r.y)
        except ValueError:
            stats["rejected_no_geometry"] += 1
            continue

        for se_b, mod_b in series_by_study.get(st, []):
            if se_b == se or mod_b == r.modality:
                continue
            gb = slice_lookup.get((st, se_b))
            if gb is None or len(gb) == 0:
                stats["rejected_no_geometry"] += 1
                continue
            stats["candidate_projections"] += 1

            # nearest slice: vectorised over the series
            ipp = gb[["ipp_x", "ipp_y", "ipp_z"]].to_numpy(dtype=np.float64)
            iop0 = gb.iloc[0]
            try:
                _, _, nrm = plane_basis([iop0.iop_0, iop0.iop_1, iop0.iop_2,
                                         iop0.iop_3, iop0.iop_4, iop0.iop_5])
            except ValueError:
                stats["rejected_no_geometry"] += 1
                continue
            d = (P - ipp) @ nrm
            j = int(np.argmin(np.abs(d)))
            oop = float(d[j])
            if abs(oop) > args.max_oop:
                stats["rejected_out_of_plane"] += 1
                continue

            sb = gb.iloc[j]
            # in-plane coordinates on that slice
            rdir = np.array([sb.iop_0, sb.iop_1, sb.iop_2], dtype=np.float64)
            cdir = np.array([sb.iop_3, sb.iop_4, sb.iop_5], dtype=np.float64)
            dvec = P - np.array([sb.ipp_x, sb.ipp_y, sb.ipp_z], dtype=np.float64)
            in_plane = dvec - oop * nrm
            A = np.stack([rdir * sb.ps_col, cdir * sb.ps_row], axis=1)
            sol, *_ = np.linalg.lstsq(A, in_plane, rcond=None)
            col_b, row_b = float(sol[0]), float(sol[1])

            m = args.margin
            if not (m <= col_b <= sb.cols - m and m <= row_b <= sb.rows - m):
                stats["rejected_out_of_bounds"] += 1
                continue

            stats["accepted"] += 1
            stats["oop_mm_accepted"].append(abs(oop))
            out_rows.append({
                "study_id": st, "level_key": r.level_key,
                "condition_key": r.condition_key, "label": int(r.label),
                "src_modality": r.modality, "src_series_id": se,
                "src_instance": inst,
                "modality": mod_b, "series_id": se_b,
                "instance_number": int(sb.name),
                "x": col_b, "y": row_b, "oop_mm": abs(oop),
            })

        if n % 5000 == 0:
            print("    {:6,}/{:,} annotated targets  ({:,} projections accepted)"
                  .format(n, len(roi), stats["accepted"]), flush=True)

    df = pd.DataFrame(out_rows)
    os.makedirs(CACHE, exist_ok=True)
    df.to_csv(OUT_CSV, index=False)

    oops = np.asarray(stats.pop("oop_mm_accepted"), dtype=float)
    stats["oop_mm_median"] = float(np.median(oops)) if len(oops) else None
    stats["oop_mm_p90"] = float(np.percentile(oops, 90)) if len(oops) else None
    stats["max_oop_setting"] = args.max_oop
    stats["margin_px"] = args.margin
    stats["elapsed_min"] = round((time.time() - t0) / 60.0, 2)

    if len(df):
        per_target = df.groupby(["study_id", "level_key", "condition_key"]).modality.nunique()
        stats["targets_with_derived"] = int(len(per_target))
        stats["coverage_pct"] = round(100.0 * len(per_target) / len(roi), 2)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump(stats, fh, indent=2)

    print("\n" + "-" * 74)
    print("  annotated targets        : {:,}".format(stats["annotated_targets"]))
    print("  candidate projections    : {:,}".format(stats["candidate_projections"]))
    print("  accepted                 : {:,}".format(stats["accepted"]))
    print("    rejected, out of plane : {:,}".format(stats["rejected_out_of_plane"]))
    print("    rejected, out of bounds: {:,}".format(stats["rejected_out_of_bounds"]))
    print("    rejected, no geometry  : {:,}".format(stats["rejected_no_geometry"]))
    if stats.get("targets_with_derived"):
        print("  targets gaining >=1 extra sequence: {:,}  ({:.1f}% of annotated)"
              .format(stats["targets_with_derived"], stats["coverage_pct"]))
        print("  out-of-plane distance: median {:.2f} mm, p90 {:.2f} mm".format(
            stats["oop_mm_median"], stats["oop_mm_p90"]))
    print("  -> {}".format(os.path.relpath(OUT_CSV, PROJECT_ROOT)))
    print("-" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
