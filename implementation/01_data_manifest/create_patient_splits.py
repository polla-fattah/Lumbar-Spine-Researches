# Phase 3 & Gate 2: Patient-Level Leakage-Proof Dataset Splitting
# Author: Dr. Polla Fattah / Selar's PhD Research Team
# Project: AMOG-Net Lumbar Spine MRI Automated Grading

import sys
import os
import pandas as pd
import numpy as np
import random
from datetime import datetime

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)

def main():
    print("=" * 65)
    print("  Phase 3 & Gate 2: Patient-Level Dataset Split Construction")
    print("=" * 65)

    SEED = 42
    set_seed(SEED)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_csv = os.path.join(base_dir, "data", "manifests", "lumbarDISC_manifest.csv")
    splits_dir = os.path.join(base_dir, "data", "splits")
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    
    os.makedirs(splits_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    if not os.path.exists(manifest_csv):
        print(f"[FAIL] Manifest CSV not found at {manifest_csv}.")
        print("       Run 'python build_lumbarDISC_manifest.py' first.")
        sys.exit(1)

    df = pd.read_csv(manifest_csv)
    unique_patients = sorted(df['patient_id'].unique().tolist())
    total_patients = len(unique_patients)

    print(f"Total Unique Patients in Cohort: {total_patients}")

    shuffled_patients = unique_patients.copy()
    random.shuffle(shuffled_patients)

    train_end = int(total_patients * 0.70)
    val_end = train_end + int(total_patients * 0.15)

    train_ids = set(shuffled_patients[:train_end])
    val_ids = set(shuffled_patients[train_end:val_end])
    test_ids = set(shuffled_patients[val_end:])

    print("\nConstructed Patient Counts:")
    print(f"  - Training Set   : {len(train_ids)} patients ({len(train_ids)/total_patients*100:.1f}%)")
    print(f"  - Validation Set : {len(val_ids)} patients ({len(val_ids)/total_patients*100:.1f}%)")
    print(f"  - Public Test Set: {len(test_ids)} patients ({len(test_ids)/total_patients*100:.1f}%)")

    assert train_ids.isdisjoint(val_ids), "[GATE 2 ERROR] Patient leakage detected between Train and Validation!"
    assert train_ids.isdisjoint(test_ids), "[GATE 2 ERROR] Patient leakage detected between Train and Test!"
    assert val_ids.isdisjoint(test_ids), "[GATE 2 ERROR] Patient leakage detected between Validation and Test!"
    assert len(train_ids) + len(val_ids) + len(test_ids) == total_patients, "[GATE 2 ERROR] Total patient count mismatch!"

    print("\n[PASS] Gate 2 Verified: ZERO Patient Leakage Across Splits (isdisjoint == True)")

    train_file = os.path.join(splits_dir, "train_ids.txt")
    val_file = os.path.join(splits_dir, "val_ids.txt")
    test_file = os.path.join(splits_dir, "public_test_ids.txt")

    with open(train_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(list(train_ids))))

    with open(val_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(list(val_ids))))

    with open(test_file, 'w', encoding='utf-8') as f:
        f.write("\n".join(sorted(list(test_ids))))

    report_md = os.path.join(reports_dir, "dataset_splits_summary.md")
    lines = [
        "# Patient-Level Dataset Splits Summary (Gate 2)",
        f"**Generated At:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`  ",
        f"**Random Seed:** `{SEED}`  ",
        "",
        "---",
        "",
        "## Patient Leakage Status",
        "**Status:** [PASS] Gate 2 Verified – ZERO Patient Leakage  ",
        "* `train_ids.isdisjoint(val_ids) == True`",
        "* `train_ids.isdisjoint(public_test_ids) == True`",
        "* `val_ids.isdisjoint(public_test_ids) == True`",
        "",
        "---",
        "",
        "## Patient Partition Distribution",
        "",
        "| Partition Set | Patient Count | Percentage | Output File Path |",
        "| :--- | :--- | :--- | :--- |",
        f"| **Training** | `{len(train_ids)}` | `{len(train_ids)/total_patients*100:.1f}%` | `{train_file}` |",
        f"| **Validation** | `{len(val_ids)}` | `{len(val_ids)/total_patients*100:.1f}%` | `{val_file}` |",
        f"| **Public Test** | `{len(test_ids)}` | `{len(test_ids)/total_patients*100:.1f}%` | `{test_file}` |",
        f"| **Total Cohort** | `{total_patients}` | `100.0%` | `{manifest_csv}` |"
    ]

    with open(report_md, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    print("\n[SUCCESS] Split files written cleanly:")
    print(f"   - {train_file}")
    print(f"   - {val_file}")
    print(f"   - {test_file}")
    print(f"   - {report_md}")
    print("=" * 65)

if __name__ == "__main__":
    main()
