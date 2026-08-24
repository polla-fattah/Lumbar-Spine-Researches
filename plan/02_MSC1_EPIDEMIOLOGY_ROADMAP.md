# MSc Project Plan — Student 1: Kurdish Population Lumbar Epidemiology

**Project Title:** Prevalence, Level Distribution, and Demographic Patterns of Lumbar Spine Degeneration: The First MRI-Based Cohort Study in Kurdistan/Iraq  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Target Degree:** MSc in Data Science / Medical Informatics / Computer Science  
**Duration:** 4–6 Months  

---

## 1. Executive Summary & Clinical Gap

* **Clinical Gap:** Published lumbar spine MRI epidemiological cohorts are almost exclusively from North America, Western Europe, China, Japan, or South Korea. No MRI-based descriptive epidemiological baseline exists for Middle Eastern, specifically Kurdish/Iraqi, populations.
* **Project Objective:** Conduct the first comprehensive descriptive epidemiological study of lumbar degenerative findings (L1–L2 … L5–S1) utilizing the 299 audited clinical radiology reports from Rizgary Teaching Hospital.
* **Why it's ideal for MSc:** **Zero AI model training required.** Requires statistical analysis, data visualization, and literature synthesis. Fast execution with high publication certainty.

---

## 2. Specific Research Objectives

1. Determine the level-by-level (L1–L2 … L5–S1) prevalence of:
   - Intervertebral disc bulge, protrusion, and extrusion.
   - Central canal stenosis (reported in 97% of cases) and neural foraminal stenosis (78%).
   - **Not subarticular / lateral recess stenosis.** Verified across all 299 reports under
     six spellings: it appears in **0%**. Rizgary radiologists do not report that
     compartment, so it cannot be included as an objective. Its absence is itself a
     reportable finding for the reporting-completeness discussion.
   - Facet joint arthrosis, ligamentum flavum hypertrophy, and nerve root compression.
2. Analyze age-stratified prevalence curves and identify the peak age of onset for severe herniation vs. canal stenosis.
3. Compare sex-specific differences in degenerative prevalence across age groups.
4. Evaluate level-coupling dominance (e.g., whether L4–L5 and L5–S1 dominance matches Western and East Asian published norms).

---

## 3. Data Source & Preparation

* **Dataset:** The 299-case structured matrix derived from Rizgary Teaching Hospital narrative `.docx` reports.

> [!IMPORTANT]
> **Dependency removed deliberately.** This project was originally gated on Phase 1 of
> Selar's PhD producing the matrix. That is an unnecessary blocking dependency: 299
> reports can be structured by hand in roughly 25--40 hours of student time. **This
> project should not wait for anyone.** Extract manually, start immediately, and
> reconcile against the automated NLP output when MSc Project 3 delivers it -- the
> agreement between the two then becomes a validation result for MSc 3 rather than a
> delay for MSc 1.
* **Sample Size:** N = 299 patients (294 with matching multi-sequence DICOM series).
* **Variables:** Age, Sex, Spinal Level (L1–L2 to L5–S1), Finding Categories (Bulge, Protrusion, Extrusion, Stenosis, Nerve Root Compression, Facet Arthrosis).

---

## 4. Methodological Workflow & Timeline

```mermaid
flowchart LR
    Step1[Month 1: Data Structuring & Hygiene] --> Step2[Month 2: Descriptive & Inferential Statistics]
    Step2 --> Step3[Month 3: Comparative Literature Synthesis]
    Step3 --> Step4[Months 4-5: Manuscript Writing & Journal Submission]
```

### Month 1: Data Import & Variable Definition
- Import audited 299-case matrix into Python (Pandas / Statsmodels) or R.
- Perform sanity checks on age/sex distributions, removing transcription artifacts.
- Code binary and ordinal severity indicators per spinal level.

### Month 2: Statistical Analysis
- Calculate overall and level-specific prevalence (%) with 95% Confidence Intervals (CI).
- Run chi-square (χ²) tests and Fisher's exact tests for sex-stratified comparisons.
- Perform multi-variable logistic regression to compute Odds Ratios (OR) for degeneration as a function of age deciles.
- Generate high-publication-quality heatmaps of finding prevalence across spinal levels.

### Month 3: Literature Benchmark & Meta-Comparison
- Compile comparative literature benchmark table comparing Kurdistan prevalence metrics against major published cohorts (e.g., Framingham Heart Study spine cohort, Wakayama Spine Study, Asian/European datasets).
- Highlight key regional concordances and discordances.

### Months 4–5: Manuscript Preparation & Submission
- Draft manuscript according to STROBE guidelines for observational cross-sectional studies.
- Submit to target journal.

---

## 5. Target Venues & Target Outputs

* **Targets** — Reach: *European Spine Journal* (IF ~2.8). Target: *Journal of Orthopaedic Surgery and Research* (IF ~2.6). Floor: *BMC Musculoskeletal Disorders*.
* **Note:** the highest-certainty publication in the programme. Descriptive epidemiology of an unstudied population is a well-understood contribution that reviewers know how to assess, and it needs no model to work.
* **Primary Output:** 1 peer-reviewed clinical journal paper **submitted** (acceptance typically lands after the degree ends) + MSc Thesis Dissertation.

---

## 6. Risk Management

| Potential Risk | Severity | Mitigation Strategy |
| :--- | :---: | :--- |
| Sample size (N = 299) questioned by reviewers | Low | Emphasize that this is a *single-center descriptive baseline* for an unstudied region; compute exact 95% CIs. |
| Missing clinical symptom data | Low | Frame study strictly as a *radiological prevalence study* rather than a clinical symptom-correlation study. |
