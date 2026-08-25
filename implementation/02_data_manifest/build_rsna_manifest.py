# Phase 2 (Track A): RSNA 2024 Lumbar Spine Master Manifest Builder
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Dataset: RSNA 2024 Lumbar Spine Degenerative Classification (1,975 Patients, 6,294 Series)

import sys
import os
import json
import pandas as pd
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

RSNA_DIR = r'C:\Users\polla\Drives\Locals\Data\lumbar-spine-degenerative-classification'

def main():
    print("=" * 65)
    print("  Phase 2 (Track A): RSNA 2024 Lumbar Spine Master Manifest Builder")
    print("=" * 65)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifests_dir = os.path.join(base_dir, "data", "manifests")
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(manifests_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    manifest_csv = os.path.join(manifests_dir, "rsna_manifest.csv")

    if not os.path.exists(RSNA_DIR):
        print(f"[FAIL] RSNA directory not found at {RSNA_DIR}.")
        sys.exit(1)

    print(f"[INGEST] Reading RSNA CSV metadata files from: {RSNA_DIR}...")
    df_train = pd.read_csv(os.path.join(RSNA_DIR, "train.csv"))
    df_series = pd.read_csv(os.path.join(RSNA_DIR, "train_series_descriptions.csv"))
    df_coords = pd.read_csv(os.path.join(RSNA_DIR, "train_label_coordinates.csv"))

    print(f"  - Patients in train.csv               : {len(df_train)}")
    print(f"  - Series in train_series_descriptions: {len(df_series)}")
    print(f"  - Coordinates in train_label_coords  : {len(df_coords)}")

    merged_df = pd.merge(df_series, df_train, on="study_id", how="inner")
    merged_df.to_csv(manifest_csv, index=False)

    num_patients = merged_df['study_id'].nunique()
    num_series = merged_df['series_id'].nunique()
    total_records = len(merged_df)

    report_md = os.path.join(reports_dir, "rsna_manifest_audit.md")
    lines = [
        "# 📋 Track A RSNA 2024 Lumbar Spine Master Manifest Audit Report",
        f"**Generated At:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**Source RSNA Path:** `{RSNA_DIR}`  ",
        f"**Master Manifest CSV:** `{manifest_csv}`  ",
        "",
        "---",
        "",
        "## 📊 RSNA Cohort Overview",
        f"* **Total Unique Patients (study_id):** `{num_patients}`",
        f"* **Total Unique MRI Series (series_id):** `{num_series}`",
        f"* **Total 3D Coordinates Keypoints:** `{len(df_coords)}`",
        f"* **Mean Series per Patient:** `{num_series / num_patients:.2f}`",
        "",
        "---",
        "",
        "## 📑 Series Distribution by MRI Modality",
        "",
        "| Series Description | Count | Percentage |",
        "| :--- | :--- | :--- |"
    ]

    s_counts = merged_df['series_description'].value_counts()
    for s_name, count in s_counts.items():
        lines.append(f"| `{s_name}` | `{count}` | `{count / len(merged_df) * 100:.1f}%` |")

    with open(report_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print(f"\n[SUCCESS] Track A RSNA Master Manifest Built Cleanly:")
    print(f"   - Total Patients : {num_patients}")
    print(f"   - Total Series   : {num_series}")
    print(f"   - Manifest CSV   : {manifest_csv}")
    print(f"   - Audit MD       : {report_md}")
    print("=" * 65)

if __name__ == "__main__":
    main()
