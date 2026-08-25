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
from datetime import datetime

import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from amog_modes import (  # noqa: E402
    CLASS_NAMES, N_CLASSES, LUMBAR_LEVELS, CONDITIONS, PROJECT_ROOT, _git_commit,
)

CROP = 128
SEVERITY_TO_INDEX = {"Normal/Mild": 0, "Moderate": 1, "Severe": 2}
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "cache")

# The caches the pipeline reads. Named in one place so a geometry change is a
# one-line edit rather than a search across six files -- and so the version in
# the name always corresponds to a recorded crop definition.
#
#   v1  fixed 128-pixel box        superseded
#   v2  60 mm physical FOV, r=1    selected by
#                                  thesis/chapter4/roi_geometry_ablation.md
ANN_CACHE = "rsna_roi_v2"
XSEQ_CACHE = "rsna_xseq_v2"

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


# The split seed is a module constant and is deliberately NOT the training seed.
# Chapter 3 sec:method-patient-split requires one split record, version
# controlled, consumed as a fixed list. If the split were drawn from the
# training seed, a three-seed campaign would draw three different cohorts:
# measured on the 1,974-study index, seeds 0 and 1 shared only 12.8% of their
# test patients, 1.7% were held out in all three runs, and 39.5% of the cohort
# was tested in one run while being trained on in another. "Held out" would then
# be true of a single run and false of the campaign, and the across-seed spread
# would mix optimisation variance with cohort resampling.
SPLIT_SEED = 20260825
SPLIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "splits")
SPLIT_FILE = os.path.join(SPLIT_DIR, "rsna_patient_split.csv")
SPLIT_META = os.path.join(SPLIT_DIR, "rsna_patient_split_meta.json")


def patient_split(index: pd.DataFrame, seed: int = SPLIT_SEED,
                  fracs=(0.70, 0.15)) -> tuple[set, set, set]:
    """Draw a disjoint patient-level split.

    This is the GENERATOR. Training must not call it directly -- use
    load_frozen_split, which reads the committed split file. Chapter 3 requires
    patient-level, not image-level, partitioning.
    """
    rng = np.random.default_rng(seed)
    patients = np.array(sorted(index["study_id"].unique()))
    rng.shuffle(patients)
    n = len(patients)
    a = int(fracs[0] * n)
    b = a + int(fracs[1] * n)
    tr, va, te = set(patients[:a]), set(patients[a:b]), set(patients[b:])
    assert not (tr & va) and not (tr & te) and not (va & te), "patient leakage"
    return tr, va, te


def _split_digest(df: pd.DataFrame) -> str:
    """Content hash of the split, so a silent edit is detectable."""
    import hashlib
    payload = "\n".join(
        "{},{}".format(int(r.study_id), r.partition)
        for r in df.sort_values("study_id").itertuples(index=False))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_frozen_split(index: pd.DataFrame, path: str = SPLIT_FILE,
                       seed: int = SPLIT_SEED, fracs=(0.70, 0.15)) -> pd.DataFrame:
    """Draw the split once and write it as a version-controlled artefact."""
    tr, va, te = patient_split(index, seed=seed, fracs=fracs)
    rows = ([(p, "train") for p in sorted(tr)]
            + [(p, "val") for p in sorted(va)]
            + [(p, "test") for p in sorted(te)])
    df = pd.DataFrame(rows, columns=["study_id", "partition"])

    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)

    meta = {
        "created": datetime.now().isoformat(timespec="seconds"),
        "split_seed": seed,
        "fractions": {"train": fracs[0], "val": fracs[1],
                      "test": round(1.0 - fracs[0] - fracs[1], 6)},
        "n_patients": int(len(df)),
        "n_train": int(len(tr)), "n_val": int(len(va)), "n_test": int(len(te)),
        "sha256": _split_digest(df),
        "git_commit": _git_commit(),
        "note": ("Chapter 3 sec:method-patient-split. Frozen split record. Do not "
                 "regenerate for a new experiment -- every comparison in the "
                 "thesis is made on these partitions. Regenerating invalidates "
                 "every result computed against the previous file."),
    }
    with open(os.path.splitext(path)[0] + "_meta.json", "w", encoding="utf-8") as fh:
        json.dump(meta, fh, indent=2)
    return df


def load_frozen_split(index: pd.DataFrame, path: str = SPLIT_FILE,
                      allow_create: bool = True) -> tuple[set, set, set]:
    """Read the committed split and restrict it to the studies in `index`.

    The split is drawn once over the full cohort and reused unchanged by every
    stage and every training seed. A subset run (--max_targets, a partial cache)
    intersects the frozen partitions rather than drawing new ones, so a small
    run and a full run remain comparable.
    """
    if not os.path.exists(path):
        if not allow_create:
            raise FileNotFoundError(
                "frozen split missing: {}\nGenerate it once with:\n"
                "  python implementation/rsna_data.py --write-split".format(path))
        print("  [split] no frozen split found; creating {}".format(path))
        print("          commit this file -- every later comparison depends on it")
        write_frozen_split(index, path)

    rec = pd.read_csv(path)
    have = set(index["study_id"].astype(np.int64).unique())
    known = set(rec["study_id"].astype(np.int64))

    unknown = have - known
    if unknown:
        raise ValueError(
            "{} study_id(s) are absent from the frozen split, e.g. {}.\n"
            "The cohort has changed since the split was drawn. Assigning them "
            "now would silently alter the partitions every published number was "
            "computed on. Either restore the previous cohort, or redraw the "
            "split deliberately and treat all prior results as superseded."
            .format(len(unknown), sorted(unknown)[:5]))

    part = {}
    for r in rec.itertuples(index=False):
        part.setdefault(r.partition, set()).add(int(r.study_id))
    tr = part.get("train", set()) & have
    va = part.get("val", set()) & have
    te = part.get("test", set()) & have

    assert not (tr & va) and not (tr & te) and not (va & te), \
        "frozen split file contains a patient in more than one partition"
    return tr, va, te


# --------------------------------------------------------------------------- #
#  ROI decoding
# --------------------------------------------------------------------------- #
def _normalise(arr: np.ndarray) -> np.ndarray:
    lo, hi = np.percentile(arr, [1, 99])
    if hi <= lo:
        hi = lo + 1.0
    return np.clip((arr - lo) / (hi - lo), 0.0, 1.0).astype(np.float32)


# Chapter 3 sec:method-roi: "Crops are defined in physical dimensions where
# possible, then resampled to the network input resolution. This avoids a fixed
# 100-pixel crop representing different anatomical widths on scanners with
# different pixel spacing."
#
# and: "One rectangular crop is not assumed to be equally appropriate for every
# target. The crop definition is conditioned on anatomical compartment... For
# neural foraminal narrowing, the sagittal T1 stream receives greater
# parasagittal coverage."
#
# These millimetre values are documented DEFAULTS chosen to bracket the relevant
# anatomy, not measured optima. sec:method-roi says the final geometry is
# reported after sensitivity testing, which is what build_roi_variants.py does.
DEFAULT_FOV_MM = 60.0
CONDITION_FOV_MM = {
    "central_canal": 55.0,        # canal is central and compact
    "left_foraminal": 80.0,       # "greater parasagittal coverage"
    "right_foraminal": 80.0,
    "left_subarticular": 50.0,    # lateral recess is a small target
    "right_subarticular": 50.0,
}


def _read_slice(images_root: str, study, series, instance, want_spacing=False):
    path = os.path.join(images_root, str(study), str(series), "{}.dcm".format(instance))
    if not os.path.exists(path):
        return (None, None) if want_spacing else None
    try:
        import pydicom
        ds = pydicom.dcmread(path)
        arr = _normalise(ds.pixel_array.astype(np.float32))
    except Exception:
        return (None, None) if want_spacing else None
    if not want_spacing:
        return arr
    ps = getattr(ds, "PixelSpacing", None)
    if ps is None or len(ps) < 2:
        return arr, None
    try:
        return arr, (float(ps[0]), float(ps[1]))
    except Exception:
        return arr, None


def decode_roi(images_root: str, row: dict, crop: int = CROP,
               radius: int = 1, fov_mm: float | None = None,
               per_condition: bool = False) -> np.ndarray | None:
    """One 2.5D ROI: the annotated slice and its neighbours, cropped and resized.

    radius        1 -> 3 slices, 2 -> 5 slices (Chapter 3's reference r=2)
    fov_mm        physical edge length of the crop; None reproduces the old
                  fixed-pixel box, kept only so the two can be compared
    per_condition when True the FOV comes from CONDITION_FOV_MM, so the canal,
                  foraminal and subarticular compartments are framed differently
    """
    centre, spacing = _read_slice(images_root, row["study_id"], row["series_id"],
                                  row["instance_number"], want_spacing=True)
    if centre is None:
        return None

    offsets = list(range(-radius, radius + 1))
    planes = []
    for off in offsets:
        if off == 0:
            planes.append(centre)
            continue
        s = _read_slice(images_root, row["study_id"], row["series_id"],
                        row["instance_number"] + off)
        # A missing or differently-shaped neighbour falls back to the centre
        # slice rather than dropping the ROI: an edge-of-series annotation is
        # still a valid target, it simply has less through-plane context.
        planes.append(s if (s is not None and s.shape == centre.shape) else centre)

    h, w = centre.shape
    cx, cy = int(round(float(row["x"]))), int(round(float(row["y"])))

    if fov_mm is None or spacing is None:
        half_r = half_c = crop // 2
    else:
        mm = fov_mm
        if per_condition:
            mm = CONDITION_FOV_MM.get(row.get("condition_key"), fov_mm)
        row_mm, col_mm = spacing
        half_r = max(4, int(round(mm / 2.0 / row_mm)))
        half_c = max(4, int(round(mm / 2.0 / col_mm)))

    r0, r1 = cy - half_r, cy + half_r
    c0, c1 = cx - half_c, cx + half_c

    # Pad rather than shift, so an annotation near the image border stays at the
    # centre of its crop. Shifting the window would silently move the target
    # off-centre exactly for the peripheral anatomy that is hardest to grade.
    pad_t, pad_b = max(0, -r0), max(0, r1 - h)
    pad_l, pad_rr = max(0, -c0), max(0, c1 - w)

    out = np.zeros((len(offsets), crop, crop), dtype=np.float16)
    for ci, p in enumerate(planes):
        pp = p
        if pad_t or pad_b or pad_l or pad_rr:
            pp = np.pad(p, ((pad_t, pad_b), (pad_l, pad_rr)), mode="edge")
        patch = pp[r0 + pad_t:r1 + pad_t, c0 + pad_l:c1 + pad_l]
        if patch.size == 0:
            return None
        if patch.shape != (crop, crop):
            import cv2
            patch = cv2.resize(patch.astype(np.float32), (crop, crop),
                               interpolation=cv2.INTER_LINEAR)
        out[ci] = patch.astype(np.float16)
    return out


def _worker(args):
    images_root, chunk, crop, radius, fov_mm, per_cond = args
    results = []
    for i, row in chunk:
        roi = decode_roi(images_root, row, crop, radius, fov_mm, per_cond)
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
                resume: bool = True, progress_every: int = 20,
                radius: int = 1, fov_mm: float | None = None,
                per_condition: bool = False) -> dict:
    """Decode every ROI once into a memory-mapped array."""
    arr_p, valid_p, idx_p, meta_p = cache_paths(name)
    n = len(index)
    images_root = os.path.join(rsna_dir, "train_images")

    n_ch = 2 * radius + 1
    shape = (n, n_ch, crop, crop)
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
            chunks.append((images_root, part, crop, radius, fov_mm, per_condition))

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
        # Geometry is recorded so a cache built under one crop definition can
        # never be mistaken for another. thesis/chapter4/roi_geometry_ablation.md
        # is the experiment that selected these values.
        "radius": int(radius),
        "n_channels": int(2 * radius + 1),
        "fov_mm": fov_mm,
        "per_condition_fov": bool(per_condition),
        "condition_fov_mm": CONDITION_FOV_MM if per_condition else None,
        "geometry": ("fixed pixel box" if fov_mm is None else
                     "{} mm physical FOV{}".format(
                         fov_mm, ", per-compartment" if per_condition else "")),
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
