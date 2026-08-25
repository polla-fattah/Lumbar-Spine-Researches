"""Phase 5 (Track A): Cut real 2.5D ROI crops from RSNA DICOMs.

For every target produced by Phase 4 this decodes the annotated slice and its
two neighbours, crops a fixed *physical* field of view centred on the
annotation, and stacks the three slices as channels.

Physical rather than pixel FOV: RSNA studies come from many scanners and
PixelSpacing ranges widely, so a fixed pixel box would frame a different amount
of anatomy per study. Crops are taken in mm and resized once.

Output is a uint8 memmap (N, 3, S, S) plus an index CSV whose row order matches
it. Rows that fail to decode are recorded with ok=0 and never silently dropped.
"""
import argparse
import os
import sys
import warnings

import cv2
import numpy as np
import pandas as pd
import pydicom
from tqdm import tqdm

warnings.filterwarnings("ignore", category=UserWarning)

FOV_MM = 60.0     # physical edge length of the crop
OUT_SIZE = 128    # pixels after resize


def load_slice(path):
    """Return a float32 2-D array and (row_mm, col_mm) spacing, or (None, None)."""
    try:
        ds = pydicom.dcmread(path)
        arr = ds.pixel_array.astype(np.float32)
    except Exception:
        return None, None
    slope = float(getattr(ds, "RescaleSlope", 1) or 1)
    inter = float(getattr(ds, "RescaleIntercept", 0) or 0)
    arr = arr * slope + inter
    ps = getattr(ds, "PixelSpacing", None)
    if ps is None or len(ps) < 2:
        return arr, None
    return arr, (float(ps[0]), float(ps[1]))


def crop_physical(arr, cx, cy, spacing):
    """Crop FOV_MM around (cx, cy). Falls back to a pixel box if spacing is absent."""
    h, w = arr.shape
    if spacing is None:
        half_r = half_c = OUT_SIZE // 2
    else:
        row_mm, col_mm = spacing
        half_r = max(4, int(round(FOV_MM / 2.0 / row_mm)))
        half_c = max(4, int(round(FOV_MM / 2.0 / col_mm)))

    r0, r1 = int(round(cy)) - half_r, int(round(cy)) + half_r
    c0, c1 = int(round(cx)) - half_c, int(round(cx)) + half_c

    # Pad rather than shift, so an annotation near the edge stays centred.
    pad_t, pad_b = max(0, -r0), max(0, r1 - h)
    pad_l, pad_r = max(0, -c0), max(0, c1 - w)
    if pad_t or pad_b or pad_l or pad_r:
        arr = np.pad(arr, ((pad_t, pad_b), (pad_l, pad_r)), mode="edge")
        r0 += pad_t; r1 += pad_t; c0 += pad_l; c1 += pad_l

    patch = arr[r0:r1, c0:c1]
    if patch.size == 0:
        return None
    return cv2.resize(patch, (OUT_SIZE, OUT_SIZE), interpolation=cv2.INTER_LINEAR)


def to_uint8(patch):
    """Per-crop robust window. MRI has no absolute intensity scale."""
    lo, hi = np.percentile(patch, (1.0, 99.0))
    if hi <= lo:
        lo, hi = float(patch.min()), float(patch.max())
        if hi <= lo:
            return np.zeros_like(patch, dtype=np.uint8)
    return np.clip((patch - lo) / (hi - lo) * 255.0, 0, 255).astype(np.uint8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rsna_dir", required=True)
    ap.add_argument("--targets", default=os.path.join(
        os.path.dirname(__file__), "..", "04_rsna_targets", "rsna_targets.csv"))
    ap.add_argument("--out_dir", default=os.path.dirname(__file__))
    ap.add_argument("--limit", type=int, default=0, help="debug: first N targets")
    args = ap.parse_args()

    df = pd.read_csv(args.targets)
    if args.limit:
        df = df.head(args.limit).copy()
    n = len(df)
    print(f"targets to extract : {n:,}")

    os.makedirs(args.out_dir, exist_ok=True)
    npy_path = os.path.join(args.out_dir, "rsna_rois.npy")
    arr_out = np.lib.format.open_memmap(
        npy_path, mode="w+", dtype=np.uint8, shape=(n, 3, OUT_SIZE, OUT_SIZE))

    ok_flags = np.zeros(n, dtype=np.uint8)
    n_no_spacing = 0
    slice_cache = {}
    last_series = None

    for i, row in enumerate(tqdm(df.itertuples(index=False), total=n, ncols=88)):
        series_dir = os.path.join(
            args.rsna_dir, "train_images", str(row.study_id), str(row.series_id))
        if series_dir != last_series:
            slice_cache.clear()          # annotations are grouped by series
            last_series = series_dir

        inst = int(row.instance_number)
        chans = []
        spacing_seen = None
        for off in (-1, 0, 1):
            key = inst + off
            if key not in slice_cache:
                p = os.path.join(series_dir, f"{key}.dcm")
                slice_cache[key] = load_slice(p) if os.path.exists(p) else (None, None)
            a, sp = slice_cache[key]
            if a is None:                # missing neighbour -> reuse centre slice
                a, sp = slice_cache.get(inst, (None, None))
            if a is None:
                chans = []
                break
            if sp is not None:
                spacing_seen = sp
            patch = crop_physical(a, row.cx, row.cy, sp)
            if patch is None:
                chans = []
                break
            chans.append(to_uint8(patch))

        if len(chans) == 3:
            arr_out[i] = np.stack(chans, axis=0)
            ok_flags[i] = 1
            if spacing_seen is None:
                n_no_spacing += 1

    arr_out.flush()
    df = df.copy()
    df["ok"] = ok_flags
    df["roi_index"] = np.arange(n)
    idx_path = os.path.join(args.out_dir, "rsna_roi_index.csv")
    df.to_csv(idx_path, index=False)

    n_ok = int(ok_flags.sum())
    print(f"\nextracted ok       : {n_ok:,} / {n:,}  ({n_ok / n * 100:.2f}%)")
    print(f"failed             : {n - n_ok:,}")
    print(f"no PixelSpacing    : {n_no_spacing:,} (fell back to pixel box)")
    print(f"array              : {npy_path}  {arr_out.shape} uint8")
    print(f"index              : {idx_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
