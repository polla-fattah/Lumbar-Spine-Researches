# MSc Project Plan — Student 4: Imaging–Symptom–Treatment Association

**Status:** **PENDING — DO NOT ALLOCATE TO A STUDENT YET**  
**Provisional Title:** Association Between Lumbar MRI Degenerative Findings, Presenting Symptoms, Treatment Path and Outcome in a Middle Eastern Clinical Cohort  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Best-Fit Degrees:** MSc in Medical Informatics / Clinical Data Science / Epidemiology / Spine Surgery Research  
**Expected Duration after data approval:** 6–9 Months

---

## 1. Activation Conditions

This project becomes available only after written confirmation that the following can be retrieved and linked to the relevant Rizgary imaging cases:

- presenting symptoms;
- symptom duration;
- relevant examination findings if available;
- treatment decision;
- surgery / conservative treatment status;
- follow-up outcome and follow-up interval.

The hospital / ethics authority must explicitly permit this linkage. Imaging-only approval is not automatically sufficient.

If the clinical data are not available, **do not substitute synthetic outcomes or simulated patients.** That would be a different research question and should be advertised as a separate project, not as a fallback clinical-prognostic study.

---

## 2. Research Rationale

Lumbar MRI abnormalities and patient symptoms are not perfectly concordant. The clinically valuable question is therefore not whether an AI model can reproduce a radiology grade, but whether quantified imaging burden relates to what the patient experiences and what treatment is chosen.

The study must remain observational. It can estimate associations / predictive discrimination; it cannot prove that an imaging feature caused surgery or symptom resolution.

---

## 3. Research Questions

**RQ1.** How strongly do level-resolved MRI findings correlate with presenting symptom patterns?

**RQ2.** Which available imaging findings—central canal stenosis, foraminal narrowing where reliably recorded, disc herniation morphology, nerve-root pressure and multilevel burden—are associated with surgical vs conservative treatment after adjustment for available covariates?

**RQ3.** Does a pre-specified multi-level imaging-burden score improve discrimination compared with the single worst radiological grade?

**RQ4.** If follow-up is sufficiently complete, which baseline imaging and clinical variables are associated with treatment response at a clearly defined time point?

Do **not** include lateral-recess / subarticular stenosis unless new radiologist grading creates that reference variable.

---

## 4. Required Variables

### Imaging / report variables

- lumbar level;
- canal stenosis grade or severity category;
- foraminal narrowing where defensible;
- bulge / protrusion / extrusion;
- nerve-root pressure where reported;
- age / sex;
- optional AI prediction probabilities only after the imaging model has been independently validated.

### Clinical variables

- dominant symptom phenotype;
- symptom duration;
- neurological deficit where documented;
- treatment path;
- procedure type if surgical;
- follow-up duration;
- outcome definition selected before analysis.

---

## 5. Methodology

### Phase 1 — Data availability and missingness audit

Before model building:

- report how many of the imaging cases have each clinical variable;
- quantify loss to follow-up;
- define exclusions;
- draw a cohort flow diagram.

If outcome completeness is inadequate, narrow the project to **cross-sectional imaging–symptom association** rather than pretending to perform prognostics.

### Phase 2 — Discordance analysis

- cross-tabulate imaging severity vs symptom phenotype;
- weighted kappa / rank correlation where scales are genuinely comparable;
- calculate the proportions of radiologically severe / clinically mild and radiologically mild / clinically severe patterns under pre-specified definitions.

### Phase 3 — Multivariable modelling

Potential models:

- logistic regression for surgical vs conservative treatment;
- ordinal / multinomial regression for symptom categories where appropriate;
- penalised regression if the number of predictors approaches the event count.

Do not use a complex ML model merely because it is available; N is likely modest.

### Phase 4 — Prognostic modelling only if follow-up supports it

If outcome data are sufficiently complete:

- specify a single primary outcome / time point;
- use internal validation by bootstrap or cross-validation;
- compare imaging-only vs clinical-only vs combined models;
- report calibration, discrimination and decision-curve analysis if appropriate.

---

## 6. AI-Derived Features

AI embeddings or probabilities may be analysed only as a **secondary predictor** after the model generating them has been independently evaluated.

The primary clinically interpretable comparison should use:

- maximum single-level grade;
- number of affected levels;
- pre-specified burden score;
- specific morphological findings.

Do not define an opaque "Lumbar Degeneration Index" after looking at the outcome and then test it on the same data; that would be circular.

---

## 7. Expected Outputs if Activated

- MSc dissertation;
- transparent linked clinical-imaging dataset dictionary;
- association / prediction analysis with calibration and uncertainty;
- manuscript prepared for submission.

Because the project depends on external clinical data availability, it is **not part of the currently selectable MSc catalogue** until activation conditions are satisfied.

---

## 8. Risks

| Risk | Response |
|---|---|
| Clinical records cannot be linked | Do not activate the project. Offer a different pre-approved MSc topic. |
| Follow-up is sparse | Reframe to cross-sectional imaging–symptom association. |
| Surgery is strongly confounded by clinician / access factors | Treat model as association / prediction, not causal inference. |
| Event count too small | Reduce predictor set; use penalisation; avoid complex ML. |
| AI model not ready | Use radiology-report findings; AI is optional, not a dependency. |
