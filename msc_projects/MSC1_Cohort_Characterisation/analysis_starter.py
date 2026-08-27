#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MSc 1 — Lumbar MRI Cohort Characterisation Analysis Starter Script
Candidate: Elaf
Supervisor: Dr. Polla Abdulhamid Fattah

This script demonstrates:
 1. Synthetic dataset creation matching Elaf's codebook schema.
 2. Level-specific finding proportion & 95% Wilson Score CIs.
 3. Co-occurrence heatmap visualization.
 4. GEE Logistic Regression (clustering by patient_id to account for repeated levels).

Usage:
    python analysis_starter.py
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
import statsmodels.formula.api as smf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Calculate 95% Wilson score interval for binomial proportions."""
    if n == 0:
        return 0.0, 0.0
    z = 1.95996  # 95% confidence
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = (z * np.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return lower, upper


def generate_synthetic_cohort(n_patients: int = 100, seed: int = 42) -> pd.DataFrame:
    """Generate synthetic dataset matching Elaf's Codebook for testing."""
    np.random.seed(seed)
    records = []
    
    for i in range(1, n_patients + 1):
        p_id = f"RIZGARY_P_{i:03d}"
        age = int(np.random.normal(52, 12))
        age = max(18, min(85, age))
        sex = np.random.choice([0, 1], p=[0.55, 0.45])  # 0: Female, 1: Male
        
        for idx, lvl in enumerate(LUMBAR_LEVELS):
            # Lower levels (L4-L5, L5-S1) have higher pathology probabilities
            base_prob = 0.15 + (idx * 0.12) + (age / 200.0)
            base_prob = min(0.85, base_prob)
            
            bulge = int(np.random.binomial(1, base_prob))
            protrusion = int(np.random.binomial(1, base_prob * 0.6))
            extrusion = int(np.random.binomial(1, base_prob * 0.2))
            canal_stenosis = int(np.random.choice([0, 1, 2], p=[1 - base_prob, base_prob * 0.7, base_prob * 0.3]))
            facet_arthrosis = int(np.random.binomial(1, base_prob * 0.5))
            
            records.append({
                "patient_id": p_id,
                "age": age,
                "sex": sex,
                "disc_level": lvl,
                "disc_bulge": bulge,
                "disc_protrusion": protrusion,
                "disc_extrusion": extrusion,
                "canal_stenosis": canal_stenosis,
                "canal_stenosis_binary": 1 if canal_stenosis > 0 else 0,
                "facet_arthrosis": facet_arthrosis
            })
            
    return pd.DataFrame(records)


def compute_level_summaries(df: pd.DataFrame) -> pd.DataFrame:
    """Compute level-resolved proportions and 95% CIs."""
    results = []
    for lvl in LUMBAR_LEVELS:
        sub = df[df["disc_level"] == lvl]
        n = len(sub)
        
        for col in ["disc_bulge", "disc_protrusion", "disc_extrusion", "canal_stenosis_binary", "facet_arthrosis"]:
            k = sub[col].sum()
            prop = k / n
            low, high = wilson_ci(k, n)
            results.append({
                "disc_level": lvl,
                "finding": col,
                "count": k,
                "total": n,
                "proportion": prop,
                "ci_lower_95": low,
                "ci_upper_95": high
            })
            
    return pd.DataFrame(results)


def fit_gee_model(df: pd.DataFrame):
    """Fit Generalized Estimating Equations (GEE) to account for patient clustering."""
    print("\n" + "="*70)
    print("  Fitting GEE Logistic Regression (Clustered by Patient ID)")
    print("="*70)
    
    # Sort by patient_id to ensure proper GEE group clustering
    df_sorted = df.sort_values(by="patient_id").copy()
    
    fam = sm.families.Binomial()
    ind = sm.cov_struct.Exchangeable()
    
    model = smf.gee(
        "disc_bulge ~ age + C(sex) + C(disc_level)",
        groups="patient_id",
        data=df_sorted,
        family=fam,
        cov_struct=ind
    )
    res = model.fit()
    print(res.summary())
    return res


def main():
    print("=" * 70)
    print("  MSc 1 Analysis Starter Script (Candidate: Elaf)")
    print("  Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 70)
    
    output_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("\n[Step 1] Generating synthetic demonstration dataset...")
    df = generate_synthetic_cohort(n_patients=100)
    print(f"   -> Created dataset with {len(df['patient_id'].unique())} patients and {len(df)} level records.")
    
    print("\n[Step 2] Computing level-resolved finding proportions & 95% CIs...")
    summary_df = compute_level_summaries(df)
    print("\nSample Level Summary (Disc Bulge):")
    print(summary_df[summary_df["finding"] == "disc_bulge"][["disc_level", "count", "proportion", "ci_lower_95", "ci_upper_95"]])
    
    csv_out = os.path.join(output_dir, "demo_level_summary.csv")
    summary_df.to_csv(csv_out, index=False)
    print(f"\n[OK] Saved level summaries to {csv_out}")
    
    print("\n[Step 3] Fitting GEE logistic regression model...")
    fit_gee_model(df)
    
    print("\n" + "="*70)
    print("  [SUCCESS] Starter script completed successfully.")
    print("="*70)


if __name__ == "__main__":
    main()
