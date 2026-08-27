#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 1: Real Rizgary Clinical Cohort Extraction & 5-Level Expansion Engine
Candidate: Elaf
Supervisor: Dr. Polla Abdulhamid Fattah

Reads `Data/research LSS 1.xlsx` (195 patient records extracted from Rizgary Teaching Hospital narrative reports),
cleans patient demographics, normalizes multi-level text strings, and expands into a 975-row level-resolved dataset
(195 patients × 5 lumbar levels: L1-L2, L2-L3, L3-L4, L4-L5, L5-S1).

Output:
    msc_projects/MSC1_Cohort_Characterisation/elaf_audited_cohort_matrix.csv
"""

import os
import sys
import re
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]

LEVEL_PATTERNS = {
    "L1-L2": [r"\bl1[-_ /]*2\b", r"\bl1[-_ /]*l2\b"],
    "L2-L3": [r"\bl2[-_ /]*3\b", r"\bl2[-_ /]*l3\b"],
    "L3-L4": [r"\bl3[-_ /]*4\b", r"\bl3[-_ /]*l4\b"],
    "L4-L5": [r"\bl4[-_ /]*5\b", r"\bl4[-_ /]*l5\b"],
    "L5-S1": [r"\bl5[-_ /]*s1\b", r"\bl5[-_ /]*1\b"]
}


def parse_level_string(text_val: str, target_level: str) -> int:
    """Check if target_level is present in the text string (e.g. 'L4-5, L5-S1')."""
    if pd.isna(text_val):
        return 0
    text_str = str(text_val).lower().strip()
    if text_str in ["none", "normal", "no", "nil", "nan", "-"]:
        return 0
    
    patterns = LEVEL_PATTERNS[target_level]
    for pat in patterns:
        if re.search(pat, text_str):
            return 1
    return 0


def assign_age_group(age: float) -> str:
    """Assign standardized age band."""
    if pd.isna(age) or age <= 0:
        return "Unknown"
    if age < 35:
        return "<35"
    elif age <= 49:
        return "35-49"
    elif age <= 64:
        return "50-64"
    else:
        return "65+"


def main():
    print("=" * 75)
    print("  Phase 1: Rizgary Cohort Extraction & 5-Level Expansion Engine")
    print("  Candidate: Elaf | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    excel_path = os.path.join(base_dir, "Data", "research LSS 1.xlsx")
    out_csv = os.path.join(os.path.dirname(__file__), "elaf_audited_cohort_matrix.csv")

    if not os.path.exists(excel_path):
        print(f"[FAIL] Source data file not found: {excel_path}")
        sys.exit(1)

    print(f"\n[Step 1] Loading raw transcription data from: {os.path.relpath(excel_path, base_dir)}")
    raw_df = pd.read_excel(excel_path)
    print(f"   -> Raw dataset shape: {raw_df.shape[0]} patients, {raw_df.shape[1]} columns")

    expanded_rows = []

    for idx, row in raw_df.iterrows():
        p_id = f"RIZGARY_P_{idx+1:03d}"
        
        # Age cleaning
        raw_age = row.get("age ", row.get("age", np.nan))
        try:
            age = float(str(raw_age).strip())
            age = age if (10 <= age <= 100) else np.nan
        except (ValueError, TypeError):
            age = np.nan
            
        # Gender cleaning (0: Female, 1: Male)
        raw_gender = str(row.get("gender", "")).lower().strip()
        sex = 1 if "male" in raw_gender and "female" not in raw_gender else 0
        sex_str = "Male" if sex == 1 else "Female"
        
        age_grp = assign_age_group(age)

        # Extract text columns for pathology fields
        bulge_text = str(row.get("Disc bulge", ""))
        protrusion_text = str(row.get("Disc protrusion", ""))
        extrusion_text = str(row.get("Disc extrusion", ""))
        stenosis_text = str(row.get("spinal canal stenosis", ""))
        facet_text = str(row.get("facet joint arthrosis", ""))
        flavum_text = str(row.get("ligamnetum flavum", ""))
        osteophyte_text = str(row.get("osteophyte", ""))

        for lvl in LUMBAR_LEVELS:
            b_flag = parse_level_string(bulge_text, lvl)
            p_flag = parse_level_string(protrusion_text, lvl)
            e_flag = parse_level_string(extrusion_text, lvl)
            s_flag = parse_level_string(stenosis_text, lvl)
            f_flag = parse_level_string(facet_text, lvl)
            fl_flag = parse_level_string(flavum_text, lvl)
            o_flag = parse_level_string(osteophyte_text, lvl)

            expanded_rows.append({
                "patient_id": p_id,
                "age": age,
                "age_group": age_grp,
                "sex": sex,
                "sex_label": sex_str,
                "disc_level": lvl,
                "disc_bulge": b_flag,
                "disc_protrusion": p_flag,
                "disc_extrusion": e_flag,
                "canal_stenosis": s_flag,
                "facet_arthrosis": f_flag,
                "ligamentum_flavum": fl_flag,
                "osteophytes": o_flag
            })

    matrix_df = pd.DataFrame(expanded_rows)
    
    # Impute missing ages with median if any missing
    median_age = matrix_df["age"].median()
    matrix_df["age"] = matrix_df["age"].fillna(median_age)
    
    matrix_df.to_csv(out_csv, index=False)

    print(f"\n[Step 2] Expanded dataset successfully created:")
    print(f"   -> Patients Ingested : {len(raw_df)}")
    print(f"   -> Level Observations: {len(matrix_df)} ({len(raw_df)} × 5 levels)")
    print(f"   -> Mean Age          : {matrix_df['age'].mean():.1f} ± {matrix_df['age'].std():.1f} years")
    print(f"   -> Sex Breakdown     : {matrix_df['sex_label'].value_counts().to_dict()}")
    print(f"   -> Output File       : {os.path.relpath(out_csv, base_dir)}")
    print("=" * 75)


if __name__ == "__main__":
    main()
