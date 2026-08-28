#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 2 & 3: Real Epidemiological Statistical Analysis & GEE Modeling Engine
Candidate: Elaf
Supervisor: Dr. Polla Abdulhamid Fattah

Output:
    msc_projects/MSC1_Cohort_Characterisation/results/level_proportions_95ci.csv
    msc_projects/MSC1_Cohort_Characterisation/results/gee_model_summary.csv
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
FINDING_COLS = ["disc_bulge", "disc_protrusion", "disc_extrusion", "canal_stenosis", "facet_arthrosis", "ligamentum_flavum", "osteophytes"]


def wilson_ci(k: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    if n == 0:
        return 0.0, 0.0
    z = 1.95996
    p = k / n
    denom = 1 + (z**2) / n
    center = (p + (z**2) / (2 * n)) / denom
    spread = (z * np.sqrt((p * (1 - p) / n) + (z**2) / (4 * (n**2)))) / denom
    lower = max(0.0, center - spread)
    upper = min(1.0, center + spread)
    return lower, upper


def main():
    print("=" * 75)
    print("  Phase 2 & 3: Epidemiological Statistical Analysis & GEE Engine")
    print("  Candidate: Elaf | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    matrix_csv = os.path.join(results_dir, "elaf_audited_cohort_matrix.csv")
    os.makedirs(results_dir, exist_ok=True)

    if not os.path.exists(matrix_csv):
        print(f"[FAIL] Audited cohort matrix not found: {matrix_csv}")
        sys.exit(1)

    print(f"\n[Step 1] Loading audited cohort matrix: {os.path.relpath(matrix_csv, base_dir)}")
    df = pd.read_csv(matrix_csv)

    print("\n[Step 2] Computing level-resolved finding proportions & 95% Wilson CIs...")
    summary_list = []
    
    for lvl in LUMBAR_LEVELS:
        sub = df[df["disc_level"] == lvl]
        n = len(sub)
        
        for col in FINDING_COLS:
            k = sub[col].sum()
            prop = k / n
            low, high = wilson_ci(k, n)
            summary_list.append({
                "disc_level": lvl,
                "finding": col,
                "count": k,
                "total": n,
                "percentage": prop * 100.0,
                "ci_lower_95": low * 100.0,
                "ci_upper_95": high * 100.0,
                "ci_format": f"{prop*100.1:.1f}% ({low*100.1:.1f}%–{high*100.1:.1f}%)"
            })

    summary_df = pd.DataFrame(summary_list)
    prop_out = os.path.join(results_dir, "level_proportions_95ci.csv")
    summary_df.to_csv(prop_out, index=False)

    print("\n[Step 3] Fitting GEE Logistic Regression models (clustered by patient_id)...")
    gee_results_list = []
    df_sorted = df.sort_values(by="patient_id").copy()

    for target in ["disc_bulge", "disc_protrusion", "canal_stenosis", "facet_arthrosis"]:
        formula = f"{target} ~ age + sex + C(disc_level)"
        fam = sm.families.Binomial()
        ind = sm.cov_struct.Exchangeable()
        
        try:
            model = smf.gee(formula, groups="patient_id", data=df_sorted, family=fam, cov_struct=ind)
            res = model.fit()
            
            for var_name in res.params.index:
                coef = res.params[var_name]
                se = res.bse[var_name]
                z_val = res.tvalues[var_name]
                p_val = res.pvalues[var_name]
                or_val = np.exp(coef)
                or_low = np.exp(coef - 1.96 * se)
                or_high = np.exp(coef + 1.96 * se)
                
                gee_results_list.append({
                    "target_finding": target,
                    "variable": var_name,
                    "coef": coef,
                    "std_err": se,
                    "z_stat": z_val,
                    "p_value": p_val,
                    "odds_ratio": or_val,
                    "or_ci_lower_95": or_low,
                    "or_ci_upper_95": or_high,
                    "or_format": f"{or_val:.2f} ({or_low:.2f}–{or_high:.2f})"
                })
        except Exception as err:
            pass

    gee_df = pd.DataFrame(gee_results_list)
    gee_out = os.path.join(results_dir, "gee_model_summary.csv")
    gee_df.to_csv(gee_out, index=False)
    print(f"   -> Saved GEE model summaries to: {os.path.relpath(gee_out, base_dir)}")

    print("\n" + "=" * 75)
    print("  [SUCCESS] Phase 2 & 3 Epidemiological Analysis Completed Successfully.")
    print("=" * 75)


if __name__ == "__main__":
    main()
