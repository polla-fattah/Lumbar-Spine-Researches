#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MSc Track 1 Analysis Starter Script
Candidate: Elaf
Supervisor: Dr. Polla Abdulhamid Fattah

Demonstrates Wilson 95% CIs and GEE Logistic Regression modeling for level-resolved lumbar MRI findings.
"""

import os
import sys
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]


def main():
    print("=" * 75)
    print("  MSc Track 1 Analysis Starter Script")
    print("  Candidate: Elaf | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    matrix_csv = os.path.join(results_dir, "elaf_audited_cohort_matrix.csv")

    if not os.path.exists(matrix_csv):
        print(f"[FAIL] Dataset not found: {matrix_csv}")
        sys.exit(1)

    df = pd.read_csv(matrix_csv)
    print(f"\n[OK] Loaded dataset: {os.path.relpath(matrix_csv, base_dir)} (N = {len(df)} levels)")

    print("\n--- Level-Resolved Prevalence of Disc Bulge & Canal Stenosis ---")
    for lvl in LUMBAR_LEVELS:
        sub = df[df["disc_level"] == lvl]
        b_pct = sub["disc_bulge"].mean() * 100
        s_pct = sub["canal_stenosis"].mean() * 100
        print(f"   Level {lvl}: Disc Bulge = {b_pct:.1f}%, Canal Stenosis = {s_pct:.1f}%")

    print("\n=" * 75)


if __name__ == "__main__":
    main()
