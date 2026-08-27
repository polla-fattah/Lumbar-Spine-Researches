# MSc Project Plan — Candidate: Elaf (MSc Track 1)

**Project Title:** Level-Specific Distribution and Demographic Patterns of Lumbar Degenerative MRI Findings in a Tertiary-Hospital Cohort in the Kurdistan Region of Iraq  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Primary MSc Candidate:** Elaf  
**Best-Fit Degrees:** MSc in Data Science / Medical Informatics / Public Health / Clinical Data Science  
**Computer Science fit:** acceptable only where programme regulations permit an applied health-analytics thesis  
**Duration:** 4–6 Months  

---

## 1. Research Gap and Correct Clinical Framing

Published lumbar MRI epidemiology is dominated by large cohorts from North America, Europe and East Asia. Regional Iraqi / Kurdish MRI studies exist, so this project must **not** claim to be the first MRI study in Iraq or Kurdistan and must **not** infer population prevalence from a hospital referral cohort.

The defensible contribution is narrower:

> **Provide a carefully verified, level-resolved description of lumbar degenerative MRI findings among patients who underwent lumbar MRI at a tertiary teaching hospital in the Kurdistan Region, and compare the observed pattern with published cohorts.**

This is a **retrospective symptomatic / referral cohort**, not a random sample of the general Kurdish population.

---

## 2. Research Questions

**RQ1.** What are the observed frequencies and 95% confidence intervals of major degenerative findings at L1–L2 through L5–S1 in this hospital MRI cohort?

**RQ2.** How do finding frequencies vary across age groups and sex?

**RQ3.** Which lumbar levels show the highest observed burden of disc herniation morphology, central canal stenosis and other reported degenerative changes?

**RQ4.** After accounting for repeated levels within the same patient, what associations remain between age / sex and specific imaging findings?

**RQ5.** How does the level distribution in this cohort compare descriptively with major published lumbar MRI cohorts, while acknowledging differences in referral criteria and case mix?

Do not use the phrase **"age of onset"**. The data contain age at imaging, not age when pathology began.

---

## 3. Data Source

- 299 anonymised narrative lumbar MRI radiology reports from Rizgary Teaching Hospital.
- Reports are the primary source.
- The structured analysis matrix must be created from / reconciled to the reports and quality-checked before analysis.

### Findings available for study

- disc bulge;
- protrusion;
- extrusion;
- central canal stenosis;
- neural foraminal narrowing where reported;
- nerve-root pressure / compression where reported;
- facet arthrosis;
- ligamentum flavum hypertrophy;
- osteophytes / related degenerative findings where consistently extractable.

### Known coverage limitations

- subarticular / lateral-recess stenosis is not reliably present in the local reports and is excluded;
- laterality is incompletely recorded;
- this is a tertiary-hospital referral cohort, so observed frequencies are affected by referral / selection bias.

---

## 4. Methodology

### Month 1 — Data structuring and audit

1. Define a codebook before statistical analysis.
2. Structure each report into patient-level and level-specific variables.
3. Double-check all non-normal findings against the source text.
4. Audit missing age / sex / level information.
5. Document exclusions without silently deleting difficult cases.

### Month 2 — Descriptive analysis

- patient-level demographics;
- level-specific finding frequencies with 95% CIs;
- stacked distributions by level;
- age-band and sex stratification;
- co-occurrence matrix across levels / findings;
- publication-quality heatmaps.

Use **"observed proportion" / "cohort frequency"** when discussing the hospital sample. If the word "prevalence" is used, qualify it as **prevalence within the imaged referral cohort**, not population prevalence.

### Month 2–3 — Inferential modelling

Because one patient contributes up to five lumbar levels, level observations are correlated.

Preferred approach:

- **GEE logistic regression** or
- **mixed-effects logistic regression with patient as a random intercept**.

Potential predictors:

- age (continuous where possible; age bands for descriptive plots);
- sex;
- lumbar level;
- age × level interaction where scientifically justified.

Report odds ratios with 95% CIs. Avoid excessive hypothesis testing across many findings; pre-specify primary outcomes and apply multiplicity control for secondary comparisons where appropriate.

### Month 3 — Literature comparison

Construct a comparison table containing:

- country / cohort;
- symptomatic vs population-based sampling;
- age distribution;
- MRI protocol;
- finding definition;
- spinal level;
- reported frequency.

Do **not** interpret numerical differences as ethnic / biological differences unless study design and referral effects have been addressed.

### Months 4–5 — Thesis and manuscript

Report according to **STROBE** and prepare a manuscript suitable for submission.

---

## 5. Student Fit

**Technical difficulty:** LOW–MEDIUM.

The student should be comfortable with:

- R or Python;
- descriptive statistics;
- confidence intervals;
- logistic regression;
- GEE / mixed-effects models;
- careful clinical-literature reading.

No deep-learning model or GPU is required.

---

## 6. Expected Outputs

- MSc dissertation;
- verified analysis code and variable dictionary;
- cohort-level figures / tables;
- **one manuscript prepared for peer-reviewed journal submission**.

Possible venues should be chosen after the results are known; likely audiences include musculoskeletal / spine / medical-imaging journals. No publication outcome is guaranteed.

---

## 7. Principal Risks

| Risk | Mitigation |
|---|---|
| Reviewers reject "population prevalence" inference | Do not make that inference; frame as a symptomatic / referred tertiary-hospital cohort. |
| Claim of "first in Iraq/Kurdistan" is challenged | Remove it; describe regional evidence as limited and fragmented, not absent. |
| N = 299 considered modest | Emphasise precise level-resolved characterisation and report CIs; avoid overfitting large multivariable models. |
| Repeated lumbar levels treated as independent | Use GEE / mixed-effects modelling. |
| Missing clinical symptoms | Keep the study radiological; do not claim symptom or outcome relationships. |

---

## Regional literature that prevents an overbroad "first" claim

- Akreyi HA, Awdish HY. (2012). *Assessment of ligamentum flavum thickness correlation with demographic variables and disc degeneration in Erbil governorate population sample*. Zanco Journal of Medical Sciences, 16(2). https://zjms.hmu.edu.krd/index.php/zjms/article/view/407
- Saeed SM, Abass AK, Rasool MM. (2019). *Inter-observer agreement in MRI assessment of lumbar intervertebral discs and nerve roots using Pfirrmann classification*. Journal of Sulaimani Medical College, 9(3), 225–237. https://jsmc.univsul.edu.iq/article?id=206
- *The Role of Lumbosacral Spine MRI in Evaluation of The Low Backache of Patients in Mosul City*. Annals of the College of Medicine Mosul, 47(1), 2025. https://mmed.uomosul.edu.iq/index.php/mmed/article/view/37160
