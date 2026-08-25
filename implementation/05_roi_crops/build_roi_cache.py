#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Decode every RSNA ROI once into a memory-mapped cache.

Replaces extract_25d_rois.py, which opened no image at all: it read fabricated
landmark centroids from a JSON and wrote a CSV of rows *describing* crops that
were never taken.

Measured cost without a cache: ~53 s per epoch over 1,046 ROIs, almost entirely
DICOM decode. Extrapolated to the full labelled set that is ~40 min per epoch and
~33 h for one 50-epoch run. The ablation ladder needs many runs, so the decode is
done once here.

USAGE
    python build_roi_cache.py --workers 12
    python build_roi_cache.py --max_samples 5000 --name rsna_roi_dev
    python build_roi_cache.py --verify
"""

from __future__ import annotations

import argparse
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from rsna_data import (  # noqa: E402
    build_index, build_cache, load_cache, cache_paths, CROP, CLASS_NAMES,
)
from dataset_config import resolve_dataset_dir, DEFAULT_HINTS_RSNA  # noqa: E402
from amog_modes import PROJECT_ROOT  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Build the RSNA ROI cache")
    ap.add_argument("--rsna_dir", type=str, default=None)
    ap.add_argument("--name", type=str, default="rsna_roi_v1")
    ap.add_argument("--crop", type=int, default=CROP)
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) // 2))
    ap.add_argument("--chunk", type=int, default=64)
    ap.add_argument("--max_samples", type=int, default=None)
    ap.add_argument("--no_resume", action="store_true")
    ap.add_argument("--verify", action="store_true", help="inspect an existing cache")
    ap.add_argument("--from_index", type=str, default=None,
                    help="build from an existing index CSV instead of re-indexing; "
                         "used for the geometry-derived cross-sequence crops")
    args = ap.parse_args()

    print("=" * 74)
    print("  RSNA 2.5D ROI Cache Builder")
    print("=" * 74)

    if args.verify:
        mm, valid, index, meta = load_cache(args.name, args.crop)
        print("  name      : {}".format(meta["name"]))
        print("  rows      : {}  valid {}  ({:.2f}%)".format(
            meta["n_rows"], int(valid.sum()), 100.0 * valid.mean()))
        print("  array     : {} {}".format(meta["shape"], meta["dtype"]))
        print("  on disk   : {:.2f} GB".format(meta["bytes_on_disk"] / 1e9))
        print("  patients  : {}".format(index.study_id.nunique()))
        print()
        print("  label distribution (valid rows only):")
        lab = index.loc[valid, "label"].value_counts().sort_index()
        for k, v in lab.items():
            print("    {:<12} {:>7}  ({:.1f}%)".format(
                CLASS_NAMES[int(k)], int(v), 100.0 * v / int(valid.sum())))
        print()
        print("  modality distribution:")
        for k, v in index.loc[valid, "modality"].value_counts().items():
            print("    {:<10} {:>7}".format(k, int(v)))
        # sanity: a decoded ROI must not be all zeros
        idxs = np.flatnonzero(valid)[:200]
        if len(idxs):
            sample = np.asarray(mm[idxs], dtype=np.float32)
            blank = int((sample.reshape(len(idxs), -1).max(axis=1) == 0).sum())
            print("\n  spot check on {} rows: {} blank".format(len(idxs), blank))
            print("  intensity range: [{:.3f}, {:.3f}]  mean {:.3f}".format(
                sample.min(), sample.max(), sample.mean()))
        return 0

    rsna_dir, ok = resolve_dataset_dir(args.rsna_dir, "RSNA_DATASET_DIR",
                                       DEFAULT_HINTS_RSNA, "RSNA")
    if not ok:
        print("[FAIL] RSNA dataset not found. Pass --rsna_dir.")
        return 2

    t0 = time.time()
    if args.from_index:
        # Cross-sequence crops are already located by geometry; re-indexing
        # would discard the projected coordinates that are the whole point.
        print("\nLoading prepared index: {}".format(args.from_index))
        index = pd.read_csv(args.from_index)
        if args.max_samples and len(index) > args.max_samples:
            index = index.sample(n=args.max_samples,
                                 random_state=42).reset_index(drop=True)
    else:
        print("\nIndexing keypoints against labels and series modality...")
        index = build_index(rsna_dir, args.max_samples)
    print("  {} labelled ROIs / {} patients  ({:.1f}s)".format(
        len(index), index.study_id.nunique(), time.time() - t0))
    for k, v in index.label.value_counts().sort_index().items():
        print("    {:<12} {:>7}  ({:.1f}%)".format(
            CLASS_NAMES[int(k)], int(v), 100.0 * v / len(index)))
    for k, v in index.modality.value_counts().items():
        print("    {:<12} {:>7}".format(k, int(v)))

    gb = len(index) * 3 * args.crop * args.crop * 2 / 1e9
    print("\n  cache will occupy about {:.2f} GB".format(gb))

    t0 = time.time()
    meta = build_cache(rsna_dir, index, name=args.name, crop=args.crop,
                       workers=args.workers, chunk=args.chunk,
                       resume=not args.no_resume)
    elapsed = time.time() - t0

    arr_p = cache_paths(args.name)[0]
    print("\n" + "-" * 74)
    print("  decoded {}/{} ROIs in {:.1f} min".format(
        meta["n_valid"], meta["n_rows"], elapsed / 60.0))
    print("  cache: {}  ({:.2f} GB)".format(
        os.path.relpath(arr_p, PROJECT_ROOT), meta["bytes_on_disk"] / 1e9))
    if meta["n_valid"] < meta["n_rows"]:
        miss = meta["n_rows"] - meta["n_valid"]
        print("  NOTE {} ROIs could not be decoded ({:.2f}%). They are marked"
              .format(miss, 100.0 * miss / meta["n_rows"]))
        print("       invalid and are excluded from training, not silently zeroed.")
    print("-" * 74)
    return 0


if __name__ == "__main__":
    sys.exit(main())
