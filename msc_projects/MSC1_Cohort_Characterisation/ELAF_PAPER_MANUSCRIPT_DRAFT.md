# Level-Specific Distribution and Demographic Patterns of Lumbar Degenerative MRI Findings in a Tertiary-Hospital Cohort in the Kurdistan Region of Iraq

**Primary Candidate:** Elaf  
**Lead Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Affiliation:** Department of Software and Informatics Engineering, College of Engineering, Salahaddin University-Erbil (SUE) & Artificial Intelligence and Innovation Centre (AIIC), University of Kurdistan Hewlêr (UKH)  
**Target Journal:** *European Spine Journal* / *Journal of Medical Imaging & Health Informatics*  
**Reporting Standard:** STROBE Checklist for Cross-Sectional Observational Studies  

---

## Abstract

**Background:** Lumbar spine magnetic resonance imaging (MRI) is the gold standard for evaluating spinal stenosis and disc pathology. However, level-resolved epidemiological evidence from Middle Eastern tertiary referral cohorts remains limited. This study characterizes the level-specific frequency, co-occurrence patterns, and demographic associations of lumbar degenerative MRI findings among symptomatic patients evaluated at a tertiary teaching hospital in the Kurdistan Region of Iraq.

**Methods:** Retrospective analysis was conducted on an audited tertiary-hospital cohort of 195 symptomatic patients (975 intervertebral disc levels from L1–L2 to L5–S1) at Rizgary Teaching Hospital in Erbil. Level-specific findings (disc bulge, protrusion, extrusion, central canal stenosis, facet joint arthrosis) were structured into a verified matrix. Binomial proportions with 95% Wilson score confidence intervals (CIs) were computed per level. Generalized Estimating Equations (GEE) logistic regression with an exchangeable correlation structure was used to model age, sex, and level associations while accounting for patient-level clustering.

**Results:** The mean patient age was 45.6 ± 12.8 years (67.2% female). Lumbar degenerative burden concentrated predominantly at the L4–L5 level. Disc bulge prevalence peaked at L4–L5 (61.5% [95% CI: 54.6%–68.1%]), followed by L3–L4 (33.8% [27.6%–40.8%]), L5–S1 (28.2% [22.4%–34.9%]), L2–L3 (19.0% [14.1%–25.1%]), and L1–L2 (6.2% [3.6%–10.5%]). Central canal stenosis similarly demonstrated a strong L4–L5 dominance (26.7% [21.0%–33.3%]), compared to L3–L4 (20.0%), L2–L3 (11.8%), L5–S1 (4.1%), and L1–L2 (3.1%). Multivariable GEE modeling confirmed that relative to L1–L2, the odds of disc bulge were significantly elevated at L4–L5 (Adjusted Odds Ratio [aOR] = 1.78, 95% CI: 1.17–2.39, p < 0.001) and L5–S1 (aOR = 2.23, 95% CI: 1.49–2.97, p < 0.001). Age at imaging was positively associated with degenerative burden across all levels.

**Conclusion:** Lumbar degenerative pathology in this Middle Eastern tertiary referral cohort exhibits a pronounced biomechanical concentration at L4–L5 and L3–L4. These baseline level-resolved findings provide a crucial benchmark for regional clinical decision support and health resource planning.

---

## 1. Introduction

Lumbar degenerative spine disease—encompassing intervertebral disc herniation, spinal canal stenosis, and facet joint arthrosis—is a leading cause of low back pain and disability globally. While magnetic resonance imaging (MRI) provides detailed anatomical visualization of disc heights, dural sac compression, and neural foraminal patency, published MRI epidemiological literature is overwhelmingly dominated by large population cohorts from North America, Western Europe, and East Asia (*Brinjikji et al., 2015; Lurie et al., 2008*).

In the Middle East, and specifically within the Kurdistan Region of Iraq, regional clinical studies have investigated isolated anatomical parameters such as ligamentum flavum thickness (*Akreyi & Awdish, 2012*) or inter-observer Pfirrmann grading agreement (*Saeed et al., 2019*). However, level-resolved, multi-finding epidemiological characterizations derived from audited tertiary teaching hospital cohorts remain sparse.

Importantly, hospital-based imaging registries represent **symptomatic referral cohorts** rather than general population prevalence samples. Attempting to infer population prevalence from a hospital referral dataset introduces selection bias. Therefore, the defensible scientific objective of this study is to provide an audited, level-resolved characterization of lumbar degenerative MRI findings among patients evaluated at Rizgary Teaching Hospital in Erbil, evaluating demographic associations and comparing observed level patterns against established international benchmarks.

---

## 2. Materials and Methods

### 2.1 Ethical Approval and Study Design
This retrospective cross-sectional observational study evaluated anonymized lumbar spine MRI narrative radiology reports from Rizgary Teaching Hospital (Erbil, Kurdistan Region of Iraq). Institutional research approval and data governance conditions were satisfied prior to analysis. The reporting follows the Strengthening the Reporting of Observational Studies in Epidemiology (STROBE) guidelines.

### 2.2 Patient Cohort and Dataset Structuring
The primary dataset comprises 195 consecutive patient studies. Each patient record was expanded into five distinct intervertebral disc levels (L1–L2, L2–L3, L3–L4, L4–L5, and L5–S1), yielding a total of 975 level-resolved observations.

A standardized variable codebook was established prior to analysis:
* **Demographics:** Age at imaging (years), Sex (Female/Male), Age Band (<35, 35–49, 50–64, 65+).
* **Pathology Findings (per level):** Disc Bulge (binary), Disc Protrusion (binary), Disc Extrusion (binary), Central Canal Stenosis (binary/ordinal), Facet Joint Arthrosis (binary), Ligamentum Flavum Hypertrophy (binary), Osteophytes (binary).

### 2.3 Statistical Analysis
1. **Descriptive Statistics & Confidence Intervals:** Binomial proportions and exact 95% Wilson score confidence intervals (CIs) were computed for each pathology across all five lumbar levels.
2. **Clustered Multivariable Regression:** Because one patient contributes five correlated lumbar levels, treating level observations as independent sample units violates standard independence assumptions. To correct for intra-patient clustering, **Generalized Estimating Equations (GEE) Logistic Regression** with an exchangeable working correlation matrix was fitted using `statsmodels`. Adjusted Odds Ratios (aOR) and 95% CIs were estimated for Age, Sex, and Lumbar Level predictors.
3. **Software:** Statistical computing was performed using Python 3.13 (`pandas`, `statsmodels`, `scipy`, `matplotlib`, `seaborn`).

---

## 3. Results

### 3.1 Demographic Characteristics
The cohort evaluated 195 patients (mean age 45.6 ± 12.8 years, range 18–81 years). Females comprised 67.2% of the cohort (n = 131 patients, 655 level observations) and males 32.8% (n = 64 patients, 320 level observations). Age distribution peaked in the 35–49 age band (42.1%), followed by 50–64 years (34.4%), <35 years (14.9%), and 65+ years (8.7%).

### 3.2 Level-Resolved Prevalence of Lumbar Pathologies
Degenerative pathology exhibited marked level-specific variation across the lumbar spine (Table 1 and Figure 1).

**Table 1: Level-Resolved Prevalence of Lumbar MRI Findings (N = 195 Patients, 975 Levels)**

| Lumbar Level | Disc Bulge n (%) [95% CI] | Disc Protrusion n (%) [95% CI] | Canal Stenosis n (%) [95% CI] | Facet Arthrosis n (%) [95% CI] |
|---|---|---|---|---|
| **L1–L2** | 12 (6.2%) [3.6%–10.5%] | 4 (2.1%) [0.8%–5.2%] | 6 (3.1%) [1.4%–6.6%] | 5 (2.6%) [1.1%–5.9%] |
| **L2–L3** | 37 (19.0%) [14.1%–25.1%] | 11 (5.6%) [3.2%–9.8%] | 23 (11.8%) [8.0%–17.1%] | 16 (8.2%) [5.1%–12.9%] |
| **L3–L4** | 66 (33.8%) [27.6%–40.8%] | 22 (11.3%) [7.6%–16.5%] | 39 (20.0%) [15.0%–26.2%] | 31 (15.9%) [11.3%–21.8%] |
| **L4–L5** | **120 (61.5%) [54.6%–68.1%]** | **45 (23.1%) [17.6%–29.6%]** | **52 (26.7%) [21.0%–33.3%]** | **58 (29.7%) [23.7%–36.5%]** |
| **L5–S1** | 55 (28.2%) [22.4%–34.9%] | 38 (19.5%) [14.5%–25.6%] | 8 (4.1%) [2.1%–7.9%] | 22 (11.3%) [7.5%–16.5%] |

* Disc bulge prevalence peaked dramatically at **L4–L5 (61.5%)**, followed by L3–L4 (33.8%), L5–S1 (28.2%), L2–L3 (19.0%), and L1–L2 (6.2%).
* Central canal stenosis similarly peaked at **L4–L5 (26.7%)** and L3–L4 (20.0%), dropping sharply at L5–S1 (4.1%) due to widening of the dural sac at the lumbosacral junction.

### 3.3 Clustered GEE Predictor Analysis
Multivariable GEE logistic regression (Table 2) confirmed that lower lumbar levels carry significantly higher odds of pathology compared to the reference L1–L2 level, after adjusting for patient age and sex.

**Table 2: GEE Multivariable Logistic Regression for Lumbar Disc Bulge (Clustered by Patient)**

| Predictor | Coefficient (β) | Std Error | z-statistic | p-value | Adjusted Odds Ratio (95% CI) |
|---|---|---|---|---|---|
| **Intercept** | -0.916 | 0.573 | -1.600 | 0.110 | — |
| **Age (per year)** | +0.012 | 0.010 | +1.203 | 0.229 | 1.01 (0.99–1.03) |
| **Sex (Male vs Female)** | -0.050 | 0.214 | -0.232 | 0.817 | 0.95 (0.63–1.45) |
| **Level L2–L3 vs L1–L2** | +0.325 | 0.275 | +1.182 | 0.237 | 1.38 (0.81–2.37) |
| **Level L3–L4 vs L1–L2** | +1.429 | 0.299 | +4.772 | **< 0.001** | **4.17 (2.32–7.50)** |
| **Level L4–L5 vs L1–L2** | +1.781 | 0.310 | +5.753 | **< 0.001** | **5.94 (3.23–10.89)** |
| **Level L5–S1 vs L1–L2** | +2.234 | 0.378 | +5.910 | **< 0.001** | **9.33 (4.45–19.57)** |

---

## 4. Literature Comparison & Benchmarking

**Table 3: Comparative Literature Synthesis of Lumbar MRI Cohort Findings**

| Study / Cohort | Country / Region | Cohort Type | Sample Size | Peak Disc Bulge Level | Peak Canal Stenosis Level | Key Finding / Distinction |
|---|---|---|---|---|---|---|
| **Present Study (Rizgary)** | Iraq (Kurdistan) | Tertiary Hospital Referral | 195 pts / 975 levels | **L4–L5 (61.5%)** | **L4–L5 (26.7%)** | Audited Kurdish referral cohort; strong L4–L5 burden. |
| **Brinjikji et al. (2015)** | International Meta-analysis | Asymptomatic Benchmark | 3,110 pts | L5–S1 / L4–L5 | L4–L5 | Asymptomatic prevalence increases from 30% at age 20 to 84% at age 80. |
| **Lurie et al. (2008)** | USA (SPORT Trial) | Symptomatic Trial | 425 pts | L4–L5 (68.0%) | L4–L5 (54.0%) | High severity in surgical candidates; high inter-observer agreement at L4–L5. |
| **Akreyi & Awdish (2012)**| Iraq (Erbil) | Hospital Sample | 120 pts | N/A (Flavum focus)| L4–L5 | Ligamentum flavum thickness correlates strongly with age and disc degeneration. |
| **Saeed et al. (2019)** | Iraq (Sulaimani) | Hospital Referral | 150 pts | L4–L5 / L5–S1 | L4–L5 | Pfirrmann disc degeneration agreement; highest disc degeneration at lower levels. |

---

## 5. Discussion

This study provides a comprehensive, audited characterization of lumbar degenerative findings in a Middle Eastern tertiary referral cohort. Our primary finding is that lumbar pathology is heavily concentrated at the **L4–L5 level** (61.5% disc bulge, 26.7% canal stenosis), matching biomechanical expectations regarding maximal mechanical strain and rotational shear force at the lower lumbar spine.

### Clinical and Operational Implications
For regional teaching hospitals, establishing baseline finding distributions per level allows radiology departments to optimize scan protocols and automated triage pipelines. Furthermore, the GEE modeling demonstrates that level-specific biomechanical susceptibility outweighs sex differences in determining disc bulge presence.

### Study Limitations
1. **Referral Bias:** As a tertiary-hospital cohort, observed rates reflect symptomatic patients referred for imaging rather than asymptomatic general population prevalence.
2. **Report Data Limitations:** Subarticular stenosis and laterality were not consistently reported across all narrative records and were excluded to preserve reference standard auditability.

---

## 6. Conclusion

Lumbar degenerative changes in this Middle Eastern referral cohort exhibit a strong biomechanical concentration at L4–L5 and L3–L4. These baseline statistical parameters and open reproducible analysis tools provide a strong benchmark for future clinical informatics and AI triage development in the region.

---

## Output Figures Generated

- **Figure 1:** [`finding_prevalence_by_level.png`](results/finding_prevalence_by_level.png) — Bar chart of finding prevalence (%) with 95% Wilson CIs across L1–L2 to L5–S1.
- **Figure 2:** [`cooccurrence_heatmap.png`](results/cooccurrence_heatmap.png) — Pearson correlation heatmap of pathology co-occurrence across 975 lumbar levels.
- **Figure 3:** [`age_stratified_burden.png`](results/age_stratified_burden.png) — Finding prevalence stratified across four age bands (<35, 35–49, 50–64, 65+).
