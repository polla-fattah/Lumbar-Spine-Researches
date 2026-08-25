"""Phase 4 (Track A): Join RSNA keypoints to their severity grades.

Produces one row per annotated (study, condition, level) target, carrying the
series and instance the annotation sits on plus the in-plane (x, y) centre.
That row is everything the ROI extractor needs to cut a real crop.

No metric here is derived from another. Counts are counts.
"""
import argparse
import os
import sys

import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from dataset_config import resolve_dataset_dir, DEFAULT_HINTS_RSNA

GRADES = ["Normal/Mild", "Moderate", "Severe"]
GRADE_TO_ORDINAL = {g: i for i, g in enumerate(GRADES)}


def target_column(condition: str, level: str) -> str:
    """'Spinal Canal Stenosis' + 'L1/L2' -> 'spinal_canal_stenosis_l1_l2'."""
    cond = condition.strip().lower().replace(" ", "_")
    lvl = level.strip().lower().replace("/", "_")
    return f"{cond}_{lvl}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rsna_dir", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    rsna_dir, ok = resolve_dataset_dir(
        args.rsna_dir, "RSNA_DATASET_DIR", DEFAULT_HINTS_RSNA, "RSNA")
    if not ok:
        return 1

    coords = pd.read_csv(os.path.join(rsna_dir, "train_label_coordinates.csv"))
    series = pd.read_csv(os.path.join(rsna_dir, "train_series_descriptions.csv"))
    grades = pd.read_csv(os.path.join(rsna_dir, "train.csv"))

    print(f"keypoints          : {len(coords):,}")
    print(f"series             : {len(series):,}")
    print(f"studies in train   : {len(grades):,}")

    df = coords.merge(series, on=["study_id", "series_id"], how="left")
    n_no_series = df["series_description"].isna().sum()
    if n_no_series:
        print(f"[WARN] {n_no_series} keypoints have no series description")

    df["target_col"] = [
        target_column(c, l) for c, l in zip(df["condition"], df["level"])
    ]

    long = grades.melt(id_vars="study_id", var_name="target_col", value_name="grade")
    df = df.merge(long, on=["study_id", "target_col"], how="left")

    n_missing = df["grade"].isna().sum()
    print(f"keypoints w/o grade: {n_missing:,}  "
          f"({n_missing / len(df) * 100:.2f}% -- dropped)")
    df = df.dropna(subset=["grade"]).copy()

    # RSNA's in-plane coordinates are literally named 'x' and 'y'. Rename the
    # vertical one before deriving any label, or the label overwrites it.
    df = df.rename(columns={"x": "cx", "y": "cy"})

    df["label"] = df["grade"].map(GRADE_TO_ORDINAL)
    unmapped = df["label"].isna().sum()
    if unmapped:
        print(f"[WARN] {unmapped} rows have an unrecognised grade string -- dropped")
        df = df.dropna(subset=["label"])
    df["label"] = df["label"].astype(int)

    out = df[["study_id", "series_id", "instance_number", "series_description",
              "condition", "level", "target_col", "grade", "label",
              "cx", "cy"]].copy()
    out["instance_number"] = out["instance_number"].astype(int)
    out["dcm_path"] = [
        os.path.join("train_images", str(s), str(se), f"{int(i)}.dcm")
        for s, se, i in zip(out["study_id"], out["series_id"],
                            out["instance_number"])
    ]

    assert out["cx"].notna().all() and out["cy"].notna().all(),         "coordinate columns must survive the label mapping"

    out_path = args.out or os.path.join(
        os.path.dirname(__file__), "rsna_targets.csv")
    out.to_csv(out_path, index=False)

    print(f"\ntargets written     : {len(out):,} -> {out_path}")
    print(f"unique studies      : {out['study_id'].nunique():,}")

    print("\nclass distribution")
    vc = out["grade"].value_counts()
    for g in GRADES:
        n = int(vc.get(g, 0))
        print(f"  {g:<12} {n:>7,}  {n / len(out) * 100:5.2f}%")
    maj = vc.max() / len(out)
    print(f"\nMAJORITY-CLASS BASELINE ACCURACY: {maj * 100:.2f}%")
    print("(any model must be judged against this, not against zero)")

    print("\ncondition x modality")
    print(out.groupby(["condition", "series_description"]).size().to_string())
    return 0


if __name__ == "__main__":
    sys.exit(main())
