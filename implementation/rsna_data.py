#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Shared RSNA data layer: indexing, ROI caching, and datasets for E0-E7.

WHY A CACHE
-----------
Measured on this machine: a real ResNet-50 epoch over 1,046 ROIs took 53 s, and
almost all of it was DICOM decode, not GPU compute. Extrapolated to the full
~48,700 labelled ROIs that is roughly 40 min per epoch, so a 50-epoch run costs
about 33 hours for ONE backbone. The ablation ladder needs many such runs.

Decoding is done once here and stored as a memory-mapped array. Subsequent
epochs read pixels straight from the map, which turns the bottleneck from DICOM
parsing into RAM bandwidth.

The cache is a derived artefact, never a source of truth. It records the commit,
the crop size and the row count in a sidecar, and the loader refuses to attach
to a cache whose geometry disagrees with what the caller asked for.

LAYOUT (per cache name)
-----------------------
    data/cache/<name>.npy         memmap, float16, (N, 3, CROP, CROP)
    data/cache/<name>_valid.npy   bool, (N,)   which rows decoded successfully
    data/cache/<name>_index.csv   the index rows, in array order
    data/cache/<name>_meta.json   provenance and geometry

TARGET SCHEMA (Chapter 3)
-------------------------
25 targets per patient: 5 lumbar levels x 5 conditions, each graded on three
ordinal levels, Normal/Mild < Moderate < Severe.
"""

from __future__ import annotations

import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import (  # noqa: E402
    CLASS_NAMES, N_CLASSES, LUMBAR_LEVELS, CONDITIONS, PROJECT_ROOT,
)

CROP = 128
SEVERITY_TO_INDEX = {"Normal/Mild": 0, "Moderate": 1, "Severe": 2}
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "cache")

# RSNA series_description -> canonical modality key
MODALITY_MAP = {
    "Sagittal T1": "sag_t1",
    "Sagittal T2/STIR": "sag_t2",
    "Axial T2": "ax_t2",
}
MODALITIES = ["sag_t1", "sag_t2", "ax_t2"]

# condition string in train_label_coordinates.csv -> canonical condition key
CONDITION_MAP = {
    "spinal canal stenosis": "central_canal",
    "left neural foraminal narrowing": "left_foraminal",
    "right neural foraminal narrowing": "right_foraminal",
    "left subarticular stenosis": "left_subarticular",
    "right subarticular stenosis": "right_subarticular",
}


# --------------------------------------------------------------------------- #
#  indexing
# --------------------------------------------------------------------------- #
def build_index(rsna_dir: str, max_samples: int | None = None,
                seed: int = 42) -> pd.DataFrame:
    """Join keypoints to severity labels and series modality. Vectorised."""
    coords = pd.read_csv(os.path.join(rsna_dir, "train_label_coordinates.csv"))
    labels = pd.read_csv(os.path.join(rsna_dir, "train.csv"))
    series = pd.read_csv(os.path.join(rsna_dir, "train_series_descriptions.csv"))

    # long-form labels: study_id, target_col, severity
    long = labels.melt(id_vars="study_id", var_name="target_col", value_name="severity")
    long = long.dropna(subset=["severity"])
    long = long[long["severity"].isin(SEVERITY_TO_INDEX)]
    long["label"] = long["severity"].map(SEVERITY_TO_INDEX).astype(np.int8)

    # matching key on the coordinate side
    coords["target_col"] = (
        coords["condition"].str.strip().str.lower().str.replace(" ", "_", regex=False)
        + "_"
        + coords["level"].str.strip().str.lower().str.replace("/", "_", regex=False)
    )
    coords["condition_key"] = coords["condition"].str.strip().str.lower().map(CONDITION_MAP)
    coords["level_key"] = coords["level"].str.strip().str.replace("/", "-", regex=False)

    df = coords.merge(long[["study_id", "target_col", "label"]],
                      on=["study_id", "target_col"], how="inner")
    df = df.merge(series[["study_id", "series_id", "series_description"]],
                  on=["study_id", "series_id"], how="left")
    df["modality"] = df["series_description"].map(MODALITY_MAP)

    df = df.dropna(subset=["condition_key", "modality"])
    df = df[df["level_key"].isin(LUMBAR_LEVELS)]

    keep = ["study_id", "series_id", "instance_number", "x", "y",
            "condition_key", "level_key", "modality", "label"]
    df = df[keep].reset_index(drop=True)
    df["study_id"] = df["study_id"].astype(np.int64)
    df["series_id"] = df["series_id"].astype(np.int64)
    df["instance_number"] = df["instance_number"].astype(np.int32)

    if max_samples and len(df) > max_samples:
        df = df.sample(n=max_samples, random_state=seed).reset_index(drop=True)
    return df


def patient_split(index: pd.DataFrame, seed: int = 42,
                  fracs=(0.70, 0.15)) -> tuple[set, set, set]:
    """Disjoint patient-level split (Chapter 3 requires patient, not image)."""
    rng = np.random.default_rng(seed)
    patients = np.array(sorted(index["study_id"].unique()))
    rng.shuffle(patients)
    n = len(patients)
    a = int(fracs[0] * n)
    b = a + int(fracs[1] * n)
    tr, va, te = set(patients[:a]), set(patients[a:b]), set(patients[b:])
    assert not (tr & va) and not (tr & te) and not (va & te), "patient leakage"
    return tr, va, te


# --------------------------------------------------------------------------- #
#  ROI decoding
# --------------------------------------------------------------------------- #
def _normalise(arr: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(arr, [1, 99])
    if hi <= lo:
        hi = lo + 1.0
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


def _read_slice(images_root: str, study, series, instance):
    path = os.path.join(images_root, str(study), str(series), "{}.dcm".format(instance))
    if not os.path.exists(path):
        return None
    try:
        import pydicom
        return _normalise(pydicom.dcmread(path).pixel_array.astype(np.float32))
    except Exception:
        return None


def decode_roi(images_root: str, row: dict, crop: int = CROP) -> np.ndarray | None:
    """One 2.5D ROI: the annotated slice plus its two neighbours, cropped."""
    centre = _read_slice(images_root, row["study_id"], row["series_id"],
                         row["instance_number"])
    if centre is None:
        return None

    planes = []
    for off in (-1, 0, 1):
        if off == 0:
            planes.append(centre)
            continue
        s = _read_slice(images_root, row["study_id"], row["series_id"],
                        row["instance_number"] + off)
        planes.append(s if (s is not None and s.shape == centre.shape) else centre)

    h, w = centre.shape
    half = crop // 2
    cx, cy = int(round(float(row["x"]))), int(round(float(row["y"])))
    x0, y0 = max(0, cx - half), max(0, cy - half)
    x1, y1 = min(w, x0 + crop), min(h, y0 + crop)
    x0, y0 = max(0, x1 - crop), max(0, y1 - crop)

    out = np.zeros((3, crop, crop), dtype=np.float16)
    for c, p in enumerate(planes):
        patch = p[y0:y1, x0:x1]
        out[c, : patch.shape[0], : patch.shape[1]] = patch.astype(np.float16)
    return out


def _worker(args):
    images_root, chunk, crop = args
    results = []
    for i, row in chunk:
        roi = decode_roi(images_root, row, crop)
        results.append((i, roi))
    return results


# --------------------------------------------------------------------------- #
#  cache build / load
# --------------------------------------------------------------------------- #
def cache_paths(name: str):
    os.makedirs(CACHE_DIR, exist_ok=True)
    base = os.path.join(CACHE_DIR, name)
    return (base + ".npy", base + "_valid.npy",
            base + "_index.csv", base + "_meta.json")


def build_cache(rsna_dir: str, index: pd.DataFrame, name: str = "rsna_roi_v1",
                crop: int = CROP, workers: int = 8, chunk: int = 64,
                resume: bool = True, progress_every: int = 20) -> dict:
    """Decode every ROI once into a memory-mapped array."""
    arr_p, valid_p, idx_p, meta_p = cache_paths(name)
    n = len(index)
    images_root = os.path.join(rsna_dir, "train_images")

    shape = (n, 3, crop, crop)
    fresh = True
    if resume and os.path.exists(arr_p) and os.path.exists(valid_p):
        try:
            existing = np.load(valid_p)
            if existing.shape == (n,):
                valid = existing
                fresh = False
                print("  resuming: {}/{} rows already decoded".format(int(valid.sum()), n))
        except Exception:
            pass
    if fresh:
        valid = np.zeros(n, dtype=bool)

    mode = "r+" if (not fresh and os.path.exists(arr_p)) else "w+"
    mm = np.lib.format.open_memmap(arr_p, mode=mode, dtype=np.float16, shape=shape)

    todo = [i for i in range(n) if not valid[i]]
    if not todo:
        print("  cache already complete")
    else:
        print("  decoding {} ROIs with {} workers...".format(len(todo), workers))
        records = index.to_dict("records")
        chunks = []
        for s in range(0, len(todo), chunk):
            part = [(i, records[i]) for i in todo[s:s + chunk]]
            chunks.append((images_root, part, crop))

        done = 0
        failed = 0
        with ProcessPoolExecutor(max_workers=workers) as ex:
            futures = {ex.submit(_worker, c): c for c in chunks}
            for k, fut in enumerate(as_completed(futures), 1):
                for i, roi in fut.result():
                    if roi is None:
                        failed += 1
                        continue
                    mm[i] = roi
                    valid[i] = True
                done += 1
                if done % progress_every == 0 or done == len(chunks):
                    pct = 100.0 * done / len(chunks)
                    print("    {:5.1f}%  {}/{} chunks  ({} failed)".format(
                        pct, done, len(chunks), failed), flush=True)
                    np.save(valid_p, valid)

    mm.flush()
    del mm
    np.save(valid_p, valid)
    index.to_csv(idx_p, index=False)

    meta = {
        "name": name, "n_rows": int(n), "n_valid": int(valid.sum()),
        "crop": crop, "dtype": "float16", "shape": list(shape),
        "rsna_dir": rsna_dir,
        "class_names": CLASS_NAMES,
        "bytes_on_disk": int(os.path.getsize(arr_p)) if os.path.exists(arr_p) else 0,
    }
    with open(meta_p, "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return meta


def _ram_available_gb():
    try:
        import psutil
        return psutil.virtual_memory().available / (1024 ** 3)
    except Exception:
        return None


def load_cache(name: str = "rsna_roi_v1", crop: int = CROP, in_ram="auto"):
    """Attach to an existing cache.

    in_ram : "auto" | True | False
        Reading the array fully into RAM removes disk from the training loop
        entirely. Both caches together are 14.4 GB, which is nothing on a host
        with 100 GB but impossible on a laptop, so "auto" loads only when there
        is comfortable headroom and otherwise falls back to the memory map.

    Returns (array_or_memmap, valid, index, meta).
    """
    arr_p, valid_p, idx_p, meta_p = cache_paths(name)
    for p in (arr_p, valid_p, idx_p, meta_p):
        if not os.path.exists(p):
            raise FileNotFoundError(
                "cache '{}' incomplete - missing {}.\n"
                "Build it first: python implementation/05_roi_crops/build_roi_cache.py"
                .format(name, os.path.basename(p)))
    with open(meta_p, "r", encoding="utf-8") as fh:
        meta = json.load(fh)
    if meta["crop"] != crop:
        raise ValueError("cache '{}' was built at crop {} but {} was requested"
                         .format(name, meta["crop"], crop))
    want_ram = in_ram
    size_gb = os.path.getsize(arr_p) / (1024 ** 3)
    if want_ram == "auto":
        avail = _ram_available_gb()
        # keep a 1.6x margin so a second cache and the workers still fit
        want_ram = bool(avail is not None and avail > size_gb * 1.6 + 4.0)

    if want_ram:
        print("  [cache] loading {} ({:.2f} GB) into RAM".format(name, size_gb))
        mm = np.load(arr_p)
    else:
        mm = np.load(arr_p, mmap_mode="r")
    valid = np.load(valid_p)
    index = pd.read_csv(idx_p)
    if len(index) != mm.shape[0] or valid.shape[0] != mm.shape[0]:
        raise ValueError("cache '{}' is inconsistent; rebuild it".format(name))
    return mm, valid, index, meta


if __name__ == "__main__":
    print("rsna_data.py -- shared data layer")
    print("  targets  : {} levels x {} conditions = {}".format(
        len(LUMBAR_LEVELS), len(CONDITIONS), len(LUMBAR_LEVELS) * len(CONDITIONS)))
    print("  classes  : {}".format(", ".join(CLASS_NAMES)))
    print("  cache dir: {}".format(CACHE_DIR))
