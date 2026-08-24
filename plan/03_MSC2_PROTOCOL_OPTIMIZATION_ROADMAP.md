# MSc Project Plan — Student 2: Sequence-Sparing Lumbar MRI Protocol Evaluation

**Project Title:** Finding-Specific Evaluation of Sequence-Sparing Lumbar MRI for Rapid Triage: A Matched-Model Ablation Study  
**Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Target Degree:** MSc in Computer Science / Artificial Intelligence / Biomedical Engineering  
**Duration:** 6–8 Months

---

## 1. Clinical Question

Abbreviated spine MRI protocols already exist in the literature, so this project does **not** claim to invent rapid MRI. The research contribution is a **finding-specific, local validation of which lumbar MRI sequences are necessary for which radiological targets and what diagnostic trade-off follows when the protocol is shortened in a resource-constrained teaching hospital.**

The project asks:

> **Can a shorter lumbar MRI sequence set preserve sufficient sensitivity for selected radiologically severe findings while materially reducing measured acquisition time?**

It is a triage / screening study, not a proposal to replace a comprehensive diagnostic MRI protocol.

---

## 2. Research Questions

**RQ1.** How does performance change for central canal stenosis, foraminal narrowing where defensibly labelled, and disc-herniation morphology when MRI sequence combinations are reduced?

**RQ2.** Which MRI sequence contributes the most diagnostic information for each finding type and lumbar level?

**RQ3.** What sensitivity–specificity trade-off is achievable for **radiologically severe / high-risk findings** under an abbreviated sequence set?

**RQ4.** What scanner-time / throughput improvement would follow from the shortened protocol using **measured local acquisition durations**, not assumed durations?

Do not use the term **"urgent surgical finding"** unless an independently verified surgical-urgency label becomes available.

No fixed sensitivity threshold is declared in advance unless a radiologist / clinical protocol committee supplies a justified non-inferiority or safety threshold.

---

## 3. Experimental Design — Critical Correction

### The invalid design to avoid

Do **not** train one full-protocol network and then zero out an unseen modality only at test time as the primary ablation. That creates an out-of-distribution input and confounds sequence importance with model brittleness.

### Required primary design

Train **matched models separately for each sequence configuration**, using:

- the same patient-level folds;
- the same architecture family / encoder capacity as far as possible;
- the same augmentation and optimisation budget;
- the same evaluation set;
- identical label definitions.

Suggested configurations:

| Config | MRI input | Purpose |
|---|---|---|
| **A — Full** | Sagittal T1 + Sagittal T2/STIR + Axial T2 | comparison reference |
| **B — Sagittal** | Sagittal T1 + Sagittal T2/STIR | removes axial imaging |
| **C — T2 sagittal only** | Sagittal T2/STIR | minimal single-sequence triage candidate |
| **D — T2 combined** | Sagittal T2/STIR + Axial T2 | preserves axial information while omitting T1 |

A standard ResNet / EfficientNet / modest 2.5D encoder is sufficient. AMOG-Net may be added later as a secondary comparator, but the MSc must not depend on it.

### Optional secondary experiment

Train one modality-dropout model and compare its missing-sequence behaviour with the matched separately trained models. This tests robustness but does not replace the primary controlled design.

---

## 4. Data and Splitting

- Use only de-identified Rizgary DICOM data after governance approval.
- Current eligible imaging cohort: approximately 294 matched cases, subject to final raw-study reconciliation.
- Split by patient, never by image / slice.
- Because N is modest, use either:
  - a locked test set plus repeated train/validation seeds, or
  - nested / repeated patient-level cross-validation with a clearly separated final test subset.

The label-to-image / level correspondence must be explicit. Whole-image labels that cannot be anatomically matched to the reported level must not be treated as target-specific ground truth.

---

## 5. Scan-Time Measurement

Do not publish assumed values such as "25 min" or "8–10 min" unless they are verified locally.

Preferred sources:

1. scanner protocol console / sequence prescription times;
2. DICOM acquisition / series timing fields where reliable;
3. radiology department protocol logs;
4. direct prospective timing of a non-patient protocol simulation if permitted.

For every configuration report:

- total acquisition time;
- absolute minutes saved;
- percentage reduction;
- theoretical exams per scanner day under transparent assumptions.

A throughput simulation must clearly state that it models operational capacity and does not prove improved patient outcomes.

---

## 6. Evaluation

Report by finding type and, where sample size permits, by level.

Primary metrics:

- sensitivity / recall for Severe or high-risk radiological findings;
- specificity;
- macro F1 / balanced accuracy;
- AUROC with 95% CIs;
- false-negative count and error severity.

Comparisons:

- DeLong test for paired AUCs where assumptions are met;
- bootstrap paired confidence intervals for other metrics;
- report absolute and relative performance difference from Config A.

For triage framing, the false-negative analysis is at least as important as overall accuracy.

---

## 7. Workflow

### Month 1

- data de-identification confirmation;
- DICOM pipeline and patient-level folds;
- label / level audit;
- extract actual sequence timing data;
- implement baseline architecture.

### Months 2–3

- train Config A–D independently under matched conditions;
- repeat seeds / folds;
- save predictions for paired analysis.

### Month 4

- finding-specific diagnostic statistics;
- false-negative audit;
- optional modality-dropout comparison.

### Month 5

- scanner-time and throughput simulation;
- radiologist review of the proposed triage scope and failure cases.

### Months 6–7

- dissertation and manuscript preparation according to STARD / CLAIM as appropriate.

---

## 8. Student Fit

**Technical difficulty:** MEDIUM–HIGH.

Requires:

- Python / PyTorch;
- DICOM handling (pydicom, SimpleITK or MONAI);
- GPU access;
- ROC / sensitivity / specificity analysis;
- careful experimental control.

The student does **not** need to invent a new neural architecture.

---

## 9. Expected Outputs

- MSc dissertation;
- reproducible matched sequence-ablation code;
- finding-specific diagnostic trade-off table;
- scanner-time / throughput analysis;
- **one manuscript prepared for journal submission**.

No publication or predefined performance level is guaranteed.

---

## 10. Main Risks

| Risk | Mitigation |
|---|---|
| Single-sequence model performs poorly | This remains a valid negative result; identify the minimum acceptable multi-sequence combination. |
| Reviewers object that abbreviated MRI is not novel | Frame novelty as finding-specific local validation and operational trade-off, not invention of rapid MRI. |
| Timing data unavailable | Do not make throughput claims until actual protocol duration is obtained. |
| Labels insufficient for foraminal / laterality analysis | Restrict to central canal and other defensibly labelled findings. |
| Severe class too small | Report wide CIs honestly and avoid unsupported safety claims. |

---

## Relevant abbreviated-protocol precedent

Abbreviated spine MRI has already been evaluated in emergency cord-compression workflows using sagittal and axial T2-weighted stacks. This MSc therefore frames its contribution as **lumbar finding-specific local validation and operational trade-off**, not invention of abbreviated MRI. See: *Implementing a rapid cord compression Magnetic Resonance Imaging protocol in the emergency department: Lessons learned*. https://pmc.ncbi.nlm.nih.gov/articles/PMC11571330/
