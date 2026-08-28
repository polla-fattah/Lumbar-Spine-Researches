#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3: High-Resolution 300 DPI Publication Figure Generator
Candidate: Elaf
Supervisor: Dr. Polla Abdulhamid Fattah

Renders:
  1. results/finding_prevalence_by_level.png
  2. results/cooccurrence_heatmap.png
  3. results/age_stratified_burden.png
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

plt.rcParams["font.sans-serif"] = "DejaVu Sans"
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8

LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]


def main():
    print("=" * 75)
    print("  Phase 3: High-Resolution 300 DPI Publication Figure Generator")
    print("  Candidate: Elaf | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    matrix_csv = os.path.join(results_dir, "elaf_audited_cohort_matrix.csv")

    if not os.path.exists(matrix_csv):
        print(f"[FAIL] Audited cohort matrix not found: {matrix_csv}")
        sys.exit(1)

    df = pd.read_csv(matrix_csv)

    # -------------------------------------------------------------
    # Figure 1: Finding Prevalence by Level with 95% CIs
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
    
    levels = LUMBAR_LEVELS
    bulge_props = [df[df["disc_level"] == lvl]["disc_bulge"].mean() * 100 for lvl in levels]
    stenosis_props = [df[df["disc_level"] == lvl]["canal_stenosis"].mean() * 100 for lvl in levels]
    facet_props = [df[df["disc_level"] == lvl]["facet_arthrosis"].mean() * 100 for lvl in levels]

    x = np.arange(len(levels))
    width = 0.25

    rects1 = ax.bar(x - width, bulge_props, width, label="Disc Bulge", color="#1f77b4", edgecolor="black", linewidth=0.5)
    rects2 = ax.bar(x, stenosis_props, width, label="Canal Stenosis", color="#d62728", edgecolor="black", linewidth=0.5)
    rects3 = ax.bar(x + width, facet_props, width, label="Facet Arthrosis", color="#2ca02c", edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Prevalence in Referral Cohort (%)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Lumbar Anatomical Level", fontsize=11, fontweight="bold")
    ax.set_title("Figure 1: Prevalence of Degenerative MRI Findings across Lumbar Levels (N=195)", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(levels, fontsize=10, fontweight="bold")
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(0, 75)

    fig1_out = os.path.join(results_dir, "finding_prevalence_by_level.png")
    plt.tight_layout()
    plt.savefig(fig1_out, dpi=300)
    plt.close()
    print(f"   -> Saved Figure 1: {os.path.relpath(fig1_out, base_dir)}")

    # -------------------------------------------------------------
    # Figure 2: Co-occurrence Correlation Heatmap
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(7, 6), dpi=300)
    finding_cols = ["disc_bulge", "disc_protrusion", "canal_stenosis", "facet_arthrosis", "osteophytes"]
    finding_labels = ["Disc Bulge", "Disc Protrusion", "Canal Stenosis", "Facet Arthrosis", "Osteophytes"]
    
    corr_matrix = df[finding_cols].corr()

    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="YlOrRd", vmin=0, vmax=0.6,
                xticklabels=finding_labels, yticklabels=finding_labels, ax=ax, cbar_kws={"label": "Pearson Correlation (r)"})
    
    ax.set_title("Figure 2: Co-occurrence Correlation Matrix of Degenerative Pathologies", fontsize=11, fontweight="bold", pad=12)
    
    fig2_out = os.path.join(results_dir, "cooccurrence_heatmap.png")
    plt.tight_layout()
    plt.savefig(fig2_out, dpi=300)
    plt.close()
    print(f"   -> Saved Figure 2: {os.path.relpath(fig2_out, base_dir)}")

    # -------------------------------------------------------------
    # Figure 3: Age-Stratified Burden
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
    age_groups = ["<35", "35-49", "50-64", "65+"]
    
    patient_level_df = df.groupby(["patient_id", "age_group"])[["disc_bulge", "canal_stenosis"]].sum().reset_index()
    patient_level_df["has_any_bulge"] = (patient_level_df["disc_bulge"] > 0).astype(int)
    patient_level_df["has_any_stenosis"] = (patient_level_df["canal_stenosis"] > 0).astype(int)

    bulge_by_age = [patient_level_df[patient_level_df["age_group"] == grp]["has_any_bulge"].mean() * 100 for grp in age_groups]
    stenosis_by_age = [patient_level_df[patient_level_df["age_group"] == grp]["has_any_stenosis"].mean() * 100 for grp in age_groups]

    x = np.arange(len(age_groups))
    width = 0.35

    ax.bar(x - width/2, bulge_by_age, width, label="Patients with ≥1 Disc Bulge", color="#1f77b4", edgecolor="black", linewidth=0.5)
    ax.bar(x + width/2, stenosis_by_age, width, label="Patients with ≥1 Canal Stenosis", color="#d62728", edgecolor="black", linewidth=0.5)

    ax.set_ylabel("Proportion of Patients in Age Group (%)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Age at Imaging (Years)", fontsize=11, fontweight="bold")
    ax.set_title("Figure 3: Age-Stratified Burden of Lumbar Degeneration", fontsize=12, fontweight="bold", pad=12)
    ax.set_xticks(x)
    ax.set_xticklabels(age_groups, fontsize=10, fontweight="bold")
    ax.legend(frameon=True, facecolor="white")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(0, 100)

    fig3_out = os.path.join(results_dir, "age_stratified_burden.png")
    plt.tight_layout()
    plt.savefig(fig3_out, dpi=300)
    plt.close()
    print(f"   -> Saved Figure 3: {os.path.relpath(fig3_out, base_dir)}")

    print("\n" + "=" * 75)
    print("  [SUCCESS] All 3 Publication Figures Generated Successfully.")
    print("=" * 75)


if __name__ == "__main__":
    main()
