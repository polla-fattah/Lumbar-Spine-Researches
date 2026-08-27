#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 3: Publication-Quality Visualization Generator
Candidate: Elaf
Supervisor: Dr. Polla Abdulhamid Fattah

Generates 3 high-resolution publication figures for Elaf's MSc thesis and manuscript:
 1. finding_prevalence_by_level.png (Stacked bar chart with 95% Wilson CIs across L1-S1).
 2. cooccurrence_heatmap.png (Pathology co-occurrence matrix).
 3. age_stratified_burden.png (Finding distribution across age bands).

Output:
    msc_projects/MSC1_Cohort_Characterisation/results/finding_prevalence_by_level.png
    msc_projects/MSC1_Cohort_Characterisation/results/cooccurrence_heatmap.png
    msc_projects/MSC1_Cohort_Characterisation/results/age_stratified_burden.png
"""

import os
import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.size"] = 10

LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]


def main():
    print("=" * 75)
    print("  Phase 3: Publication Figure Generator")
    print("  Candidate: Elaf | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    matrix_csv = os.path.join(base_dir, "elaf_audited_cohort_matrix.csv")
    props_csv = os.path.join(base_dir, "results", "level_proportions_95ci.csv")
    results_dir = os.path.join(base_dir, "results")
    os.makedirs(results_dir, exist_ok=True)

    if not os.path.exists(matrix_csv) or not os.path.exists(props_csv):
        print("[FAIL] Missing input data files for plotting.")
        sys.exit(1)

    df_matrix = pd.read_csv(matrix_csv)
    df_props = pd.read_csv(props_csv)

    # -------------------------------------------------------------
    # Figure 1: Level-Resolved Finding Prevalence with 95% CIs
    # -------------------------------------------------------------
    print("\n[Step 1] Rendering Figure 1: Finding Prevalence across Lumbar Levels...")
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    
    findings_to_plot = ["disc_bulge", "canal_stenosis", "facet_arthrosis", "disc_protrusion"]
    labels_map = {
        "disc_bulge": "Disc Bulge",
        "canal_stenosis": "Canal Stenosis",
        "facet_arthrosis": "Facet Arthrosis",
        "disc_protrusion": "Disc Protrusion"
    }
    colors = ["#2b5c8f", "#d95f02", "#7570b3", "#1b9e77"]
    
    x = np.arange(len(LUMBAR_LEVELS))
    width = 0.18

    for idx, f in enumerate(findings_to_plot):
        sub = df_props[df_props["finding"] == f]
        pcts = sub["percentage"].values
        y_err_lower = pcts - sub["ci_lower_95"].values
        y_err_upper = sub["ci_upper_95"].values - pcts
        y_err = [y_err_lower, y_err_upper]

        ax.bar(
            x + (idx - 1.5) * width,
            pcts,
            width,
            yerr=y_err,
            label=labels_map[f],
            color=colors[idx],
            capsize=4,
            alpha=0.88,
            edgecolor="black",
            linewidth=0.8
        )

    ax.set_ylabel("Cohort Prevalence (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Spinal Level", fontsize=12, fontweight="bold")
    ax.set_title("Level-Resolved Prevalence of Major Lumbar Findings at Rizgary Teaching Hospital (N=195)", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(LUMBAR_LEVELS, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 80)
    ax.legend(frameon=True, facecolor="white", edgecolor="none", fontsize=10)

    fig1_path = os.path.join(results_dir, "finding_prevalence_by_level.png")
    plt.tight_layout()
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"   -> Saved Figure 1 to: {os.path.relpath(fig1_path, base_dir)}")

    # -------------------------------------------------------------
    # Figure 2: Pathology Co-Occurrence Heatmap
    # -------------------------------------------------------------
    print("\n[Step 2] Rendering Figure 2: Pathology Co-Occurrence Heatmap...")
    fig, ax = plt.subplots(figsize=(8, 6.5), dpi=300)
    
    co_cols = ["disc_bulge", "disc_protrusion", "disc_extrusion", "canal_stenosis", "facet_arthrosis", "osteophytes"]
    clean_labels = ["Disc Bulge", "Protrusion", "Extrusion", "Canal Stenosis", "Facet Arthrosis", "Osteophytes"]
    
    corr = df_matrix[co_cols].corr()
    
    sns.heatmap(
        corr,
        annot=True,
        fmt=".2f",
        cmap="Blues",
        xticklabels=clean_labels,
        yticklabels=clean_labels,
        cbar_kws={"label": "Pearson Correlation (r)"},
        ax=ax,
        linewidths=0.5,
        annot_kws={"size": 10, "weight": "bold"}
    )
    
    ax.set_title("Co-Occurrence Correlation Matrix of Lumbar Findings (N=975 Levels)", fontsize=13, fontweight="bold", pad=15)
    
    fig2_path = os.path.join(results_dir, "cooccurrence_heatmap.png")
    plt.tight_layout()
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"   -> Saved Figure 2 to: {os.path.relpath(fig2_path, base_dir)}")

    # -------------------------------------------------------------
    # Figure 3: Age-Stratified Degeneration Burden
    # -------------------------------------------------------------
    print("\n[Step 3] Rendering Figure 3: Age-Stratified Finding Burden...")
    fig, ax = plt.subplots(figsize=(9, 5.5), dpi=300)
    
    age_groups = ["<35", "35-49", "50-64", "65+"]
    age_summary = df_matrix.groupby("age_group")[["disc_bulge", "canal_stenosis", "facet_arthrosis"]].mean() * 100.0
    age_summary = age_summary.reindex(age_groups)
    
    age_summary.plot(kind="bar", ax=ax, width=0.7, color=["#2b5c8f", "#d95f02", "#7570b3"], alpha=0.9, edgecolor="black", linewidth=0.8)
    
    ax.set_ylabel("Prevalence in Age Group (%)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Age Group at Imaging (Years)", fontsize=12, fontweight="bold")
    ax.set_title("Degenerative Finding Burden Stratified by Age at Imaging", fontsize=13, fontweight="bold", pad=15)
    ax.set_xticklabels(age_groups, rotation=0, fontsize=11, fontweight="bold")
    ax.set_ylim(0, 70)
    ax.legend(["Disc Bulge", "Canal Stenosis", "Facet Arthrosis"], frameon=True, facecolor="white", edgecolor="none")

    fig3_path = os.path.join(results_dir, "age_stratified_burden.png")
    plt.tight_layout()
    plt.savefig(fig3_path, dpi=300)
    plt.close()
    print(f"   -> Saved Figure 3 to: {os.path.relpath(fig3_path, base_dir)}")

    print("\n" + "=" * 75)
    print("  [SUCCESS] All 3 Publication Figures Generated Successfully.")
    print("=" * 75)


if __name__ == "__main__":
    main()
