# MSc 1 — Student Onboarding & Data Codebook Guide

**Candidate:** Elaf  
**Degree Track:** MSc in Data Science / Medical Informatics / Public Health / Clinical Data Science  
**Lead Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Project Title:** *Level-Specific Distribution and Demographic Patterns of Lumbar Degenerative MRI Findings in a Tertiary-Hospital Cohort in the Kurdistan Region of Iraq*  
**Companion Documents:** [`plan/02_MSC1_EPIDEMIOLOGY_ROADMAP.md`](../../plan/02_MSC1_EPIDEMIOLOGY_ROADMAP.md) · [`RESEARCH_PLAN.md`](RESEARCH_PLAN.md) · [`DATA_AND_GOVERNANCE.md`](DATA_AND_GOVERNANCE.md)

---

## 1. Project Welcome & Core Objectives for Elaf

Welcome to the project! This guide lays out your exact research roadmap, clinical data codebook, and statistical guidelines.

Your master’s thesis focuses on providing a **verified, level-resolved epidemiological characterisation** of lumbar spine MRI findings among 299 patients at Rizgary Teaching Hospital in Erbil.

### Core Scientific Questions You Will Answer
1. **Finding Frequencies & 95% CIs:** What are the observed frequencies and 95% confidence intervals of major degenerative findings at levels L1–L2 through L5–S1?
2. **Demographic Variations:** How do finding frequencies vary across age bands (<30, 30–45, 46–60, >60) and sex?
3. **Anatomical Burden:** Which lumbar levels exhibit the highest observed burden of disc herniation morphology (bulge, protrusion, extrusion) and central canal stenosis?
4. **Clustered Predictor Analysis:** After accounting for repeated lumbar levels within the same patient, what associations remain between age/sex and specific imaging findings?
5. **Literature Comparison:** How does this cohort compare descriptively with published international (*Brinjikji et al., Lurie et al.*) and regional (*Akreyi & Awdish, Saeed et al.*) lumbar MRI cohorts?

---

## 2. Clinical Data Codebook (Variable Dictionary)

Before running statistical models, you must structure the 299 narrative reports into a clean, audited dataset following this exact variable schema:

### 2.1 Patient-Level Demographics
| Variable Name | Data Type | Description & Value Coding |
|---|---|---|
| `patient_id` | String | Anonymised patient identifier (e.g., `RIZGARY_P_001`) |
| `age` | Integer | Age in years at time of imaging |
| `age_group` | Categorical | `0`: <30 yrs · `1`: 30–45 yrs · `2`: 46–60 yrs · `3`: >60 yrs |
| `sex` | Binary | `0`: Female · `1`: Male |
| `report_date` | Date | Date of MRI examination (`YYYY-MM-DD`) |

### 2.2 Level-Resolved Imaging Findings (5 Levels: L1–L2, L2–L3, L3–L4, L4–L5, L5–S1)
Each patient contributes 5 rows to the level-level dataset.

| Variable Name | Target Level | Data Type | Value Coding & Definitions |
|---|---|---|---|
| `disc_level` | All | Categorical | `L1-L2`, `L2-L3`, `L3-L4`, `L4-L5`, `L5-S1` |
| `disc_bulge` | Level-specific | Binary | `0`: Absent/Normal · `1`: Present (Circumferential bulge) |
| `disc_protrusion` | Level-specific | Binary | `0`: Absent · `1`: Present (Focal protrusion) |
| `disc_extrusion` | Level-specific | Binary | `0`: Absent · `1`: Present (Extrusion / Sequestration) |
| `canal_stenosis` | Level-specific | Ordinal | `0`: Normal/Mild · `1`: Moderate · `2`: Severe |
| `foraminal_narrowing`| Level-specific | Binary | `0`: Absent/Not reported · `1`: Present |
| `nerve_root_pressure`| Level-specific | Binary | `0`: Absent/Not reported · `1`: Present |
| `facet_arthrosis` | Level-specific | Binary | `0`: Absent/Not reported · `1`: Present |
| `ligamentum_flavum` | Level-specific | Binary | `0`: Normal · `1`: Hypertrophied |
| `osteophytes` | Level-specific | Binary | `0`: Absent · `1`: Present |

> [!CAUTION]
> **Data Scope Rules:**
> 1. Subarticular / lateral-recess stenosis is **excluded** because local reports do not consistently record it.
> 2. Reports are the **primary reference standard**. Do not rely on unverified spreadsheets.

---

## 3. Mandatory Methodological Guardrails

When writing your thesis and paper, strictly follow these framing rules set by your supervisor:

1. **Cohort Framing:** Always refer to the dataset as a **"retrospective tertiary-hospital referral cohort"**. Never call it a "population prevalence survey".
2. **Terminology:** Use **"Age at Imaging"**, never *"Age of Onset"* (the data records when the MRI was taken, not when disease started).
3. **No Overbroad Novelty Claims:** Do not claim this is "the first MRI study in Iraq or Kurdistan." Acknowledge existing regional literature (*Akreyi & Awdish 2012, Saeed et al. 2019*).
4. **Clustered Data Analysis:** Because 1 patient contributes 5 lumbar levels, level observations are correlated. You **must** use **Generalized Estimating Equations (GEE) Logistic Regression** or **Mixed-Effects Logistic Regression** (random intercept for `patient_id`). Treating 5 levels from one patient as independent sample units is statistically incorrect.

---

## 4. Elaf's 5-Phase Dissertation Timeline

```text
┌─────────────────────────────────────────────────────────────────────────┐
│ Month 1: Data Audit & Codebook Verification                             │
│ • Structure 299 reports into codebook schema                            │
│ • Verify non-normal findings against source report text                 │
├─────────────────────────────────────────────────────────────────────────┤
│ Month 2: Descriptive Analysis & Cohort Visualisation                    │
│ • Compute level-specific frequencies with 95% Wilson CIs                │
│ • Generate co-occurrence heatmaps and level-burden bar charts           │
├─────────────────────────────────────────────────────────────────────────┤
│ Month 3: Inferential Modeling & Literature Benchmarking                 │
│ • Fit GEE / Mixed-Effects Logistic Regression (OR, 95% CIs)             │
│ • Construct comparative benchmark matrix vs. published literature       │
├─────────────────────────────────────────────────────────────────────────┤
│ Months 4–5: Thesis Writing & STROBE Manuscript Preparation              │
│ • Complete 5 thesis chapters                                            │
│ • Format paper manuscript following STROBE guidelines for submission    │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Starter Tools & Scripts

You are provided with a Python starter script in this directory:
- [`analysis_starter.py`](analysis_starter.py): Demonstrates data loading, 95% Wilson CI calculation, co-occurrence heatmap plotting, and GEE model execution.

To get started, activate the environment and run:
```bash
python analysis_starter.py
```
