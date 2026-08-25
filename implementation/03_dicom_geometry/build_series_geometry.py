#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Extract REAL per-slice DICOM geometry for every RSNA series.

Replaces the substitution in dicom_geometry_parser.py, which never read
ImageOrientationPatient and instead assigned textbook cosines by substring
match on series_description. Correspondence derived from assumed orientations
is fictional, which voids Core Contribution I's premise.

Reads headers only (stop_before_pixels=True), so this is I/O bound rather than
decode bound and parallelises well.

OUTPUT
    data/cache/series_geometry.csv
        study_id, series_id, instance_number,
        ipp_x, ipp_y, ipp_z,
        iop_0 .. iop_5,
        ps_row, ps_col, rows, cols, thickness

USAGE
    python build_series_geometry.py --workers 12
    python build_series_geometry.py --verify
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dataset_config import resolve_dataset_dir, DEFAULT_HINTS_RSNA  # noqa: E402
from amog_modes import PROJECT_ROOT  # noqa: E402
from geometry import roundtrip_error_mm, plane_basis  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

OUT_CSV = os.path.join(PROJECT_ROOT, "data", "cache", "series_geometry.csv")


def _scan_series(args):
    """Read headers for every slice of one series."""
    study_id, series_id, series_dir = args
    import pydicom
    rows = []
    try:
        files = os.listdir(series_dir)
    except OSError:
        return rows
    for fn in files:
        if not fn.lower().endswith(".dcm"):
            continue
        path = os.path.join(series_dir, fn)
        try:
            d = pydicom.dcmread(path, stop_before_pixels=True)
            ipp = [float(v) for v in d.ImagePositionPatient]
            iop = [float(v) for v in d.ImageOrientationPatient]
            ps = [float(v) for v in d.PixelSpacing]
        except Exception:
            continue
        try:
            inst = int(getattr(d, "InstanceNumber", os.path.splitext(fn)[0]))
        except Exception:
            continue
        rows.append({
            "study_id": study_id, "series_id": series_id, "instance_number": inst,
            "ipp_x": ipp[0], "ipp_y": ipp[1], "ipp_z": ipp[2],
            "iop_0": iop[0], "iop_1": iop[1], "iop_2": iop[2],
            "iop_3": iop[3], "iop_4": iop[4], "iop_5": iop[5],
            "ps_row": ps[0], "ps_col": ps[1],
            "rows": int(getattr(d, "Rows", 0)), "cols": int(getattr(d, "Columns", 0)),
            "thickness": float(getattr(d, "SliceThickness", 0.0) or 0.0),
        })
    return rows


def verify(path=OUT_CSV):
    if not os.path.exists(path):
        print("[FAIL] no geometry table at {}".format(path))
        return 1
    g = pd.read_csv(path)
    print("  slices          : {:,}".format(len(g)))
    print("  series          : {:,}".format(g.groupby(['study_id', 'series_id']).ngroups))
    print("  studies         : {:,}".format(g.study_id.nunique()))

    iop = g[["iop_0", "iop_1", "iop_2", "iop_3", "iop_4", "iop_5"]].to_numpy()
    uniq = np.unique(np.round(iop, 3), axis=0)
    print("  distinct orientations observed: {:,}".format(len(uniq)))
    print("    (the previous parser assumed exactly 2)")

    # true round-trip on a random sample, using the real header values
    rng = np.random.default_rng(0)
    take = rng.choice(len(g), size=min(500, len(g)), replace=False)
    errs = []
    for i in take:
        r = g.iloc[i]
        try:
            errs.append(roundtrip_error_mm(
                [r.ipp_x, r.ipp_y, r.ipp_z],
                [r.iop_0, r.iop_1, r.iop_2, r.iop_3, r.iop_4, r.iop_5],
                [r.ps_row, r.ps_col], r.cols / 2.0, r.rows / 2.0))
        except Exception:
            errs.append(float("nan"))
    errs = np.asarray(errs, dtype=float)
    ok = np.isfinite(errs)
    print("\n  round-trip on {} real slices: max {:.2e} mm, {} degenerate"
          .format(int(ok.sum()), np.nanmax(errs) if ok.any() else float('nan'),
                  int((~ok).sum())))

    # how far from the textbook cosines the real data actually is
    sag_ideal = np.array([0, 1, 0, 0, 0, -1], dtype=float)
    ax_ideal = np.array([1, 0, 0, 0, 1, 0], dtype=float)
    dev = np.minimum(np.abs(iop - sag_ideal).max(axis=1),
                     np.abs(iop - ax_ideal).max(axis=1))
    print("  deviation from the assumed textbook cosines:")
    print("    median {:.4f}   90th pct {:.4f}   max {:.4f}".format(
        np.median(dev), np.percentile(dev, 90), dev.max()))
    print("    slices off by >0.05: {:,} ({:.1f}%)".format(
        int((dev > 0.05).sum()), 100.0 * (dev > 0.05).mean()))
    return 0


def main():
    ap = argparse.ArgumentParser(description="Extract real RSNA series geometry")
    ap.add_argument("--rsna_dir", type=str, default=None)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    print("=" * 74)
    print("  RSNA Series Geometry Extractor (real DICOM headers)")
    print("=" * 74)

    if args.verify:
        return verify()

    rsna_dir, ok = resolve_dataset_dir(args.rsna_dir, "RSNA_DATASET_DIR",
                                       DEFAULT_HINTS_RSNA, "RSNA")
    if not ok:
        return 2

    images = os.path.join(rsna_dir, "train_images")
    print("\nEnumerating series...")
    tasks = []
    for study in sorted(os.listdir(images)):
        sp = os.path.join(images, study)
        if not os.path.isdir(sp):
            continue
        for series in os.listdir(sp):
            tasks.append((int(study), int(series), os.path.join(sp, series)))
    print("  {:,} series across {:,} studies".format(
        len(tasks), len({t[0] for t in tasks})))

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    print("\nReading headers with {} workers...".format(args.workers))
    t0 = time.time()
    rows = []
    done = 0
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futures = [ex.submit(_scan_series, t) for t in tasks]
        for fut in as_completed(futures):
            rows.extend(fut.result())
            done += 1
            if done % 400 == 0 or done == len(tasks):
                print("    {:5.1f}%  {:,}/{:,} series  {:,} slices".format(
                    100.0 * done / len(tasks), done, len(tasks), len(rows)), flush=True)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print("\n  {:,} slices in {:.1f} min -> {}".format(
        len(df), (time.time() - t0) / 60.0, os.path.relpath(OUT_CSV, PROJECT_ROOT)))
    print()
    return verify()


if __name__ == "__main__":
    sys.exit(main())
