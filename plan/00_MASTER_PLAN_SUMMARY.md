# Lumbar Spine MRI Research Programme — Committee-Ready Master Plan

**Project Title:** Lumbar Spine MRI AI & Clinical Studies (Rizgary Teaching Hospital & International Benchmarks)  
**Lead Academic Supervisor:** Dr. Polla Abdulhamid Fattah  
**Primary PhD Candidate:** Selar  
**Revision Date:** 2026-08-24  
**Committee Status:** **Scientifically approvable in principle; local-data work remains conditional on the governance actions in Section 5.**

---

## 1. Programme Vision

This programme separates one doctoral methodological track from several independent MSc projects. The purpose is to avoid a single oversized project, protect each student's graduation timeline from another student's research risk, and ensure that every project has a distinct research question and publication identity.

The programme has two linked aims:

1. **Computer-science contribution:** develop and test methods for anatomy-aware, disease-adaptive, multi-sequence lumbar MRI analysis that remain robust across institutions and missing MRI sequences.
2. **Clinical / health-informatics contribution:** use the local Rizgary cohort to answer clinically actionable questions about finding distributions, MRI protocol efficiency, report structuring, and—if additional records become available—imaging–symptom–outcome relationships.

The AI method is not the clinical message. For clinically oriented papers, the clinical question leads and the model is the measurement tool.

---

## 2. Research Tracks and Availability

| Track | Status | Primary question | Can start now? |
|---|---|---|---|
| **PhD — Disease-adaptive heterogeneous graph learning & transfer** | Approved in principle | Can explicit disease/level relationships, adaptive sequence routing, anatomical self-supervision, and cross-institutional adaptation improve lumbar MRI grading? | **Yes, using public benchmark data** |
| **MSc 1 — Tertiary-hospital cohort characterisation** | Available after report-data access approval | What level-specific lumbar degenerative findings occur in this symptomatic/referral cohort, and how do they vary with age and sex? | **Yes, reports only** |
| **MSc 2 — Sequence-sparing MRI triage / protocol optimisation** | Available after de-identified DICOM release | Which MRI sequences are needed for which finding, and what diagnostic trade-off accompanies a shortened protocol? | **Yes, after de-identification** |
| **MSc 3 — Clinical NLP report structuring** | Available after report-data access approval | How accurately can rule-based NLP and open-weight LLMs extract level-resolved lumbar findings from local English radiology reports? | **Yes, reports only** |
| **MSc 4 — Imaging–symptom–treatment prognostics** | **Not available for allocation yet** | How do imaging findings relate to symptoms, treatment and outcomes? | **No — clinical linkage not confirmed** |

---

## 3. Data Assets and Cohort Accounting

### 3.1 Public benchmark resources

- **RSNA LumbarDISC / RSNA 2024 lumbar degenerative classification data**: public multi-institutional, multi-sequence MRI benchmark. The full published cohort contains 2,697 patients and 8,593 MRI series; the locally held labelled Kaggle training subset used for development contains approximately 1,975 studies. The proposal must state clearly which subset is used in each experiment rather than using the two numbers interchangeably.
- **SPIDER**: public lumbar MRI anatomical segmentation resource used for localisation / segmentation development and benchmarking, subject to its licence terms.

### 3.2 Local Rizgary resources

- 299 anonymised narrative lumbar MRI radiology reports.
- 294 local case folders currently identified as eligible matched multi-sequence imaging cases.
- A raw DICOM audit found 341 DICOM StudyInstanceUID-level studies across 25,110 files.

### 3.3 Required reconciliation before committee sign-off

The relationship between **341 raw DICOM studies**, **294 eligible imaging cases**, and **299 reports** must be documented in a short cohort-flow table before final committee submission. Do not infer the reason for exclusions. Record the verified reason for every exclusion / repeat / unmatched case once the audit is complete.

Suggested format:

```text
Raw DICOM studies received                    341
    - repeat / duplicate studies              [VERIFY]
    - non-lumbar / unusable / incomplete      [VERIFY]
    - no matching report                      [VERIFY]
Eligible matched imaging cases                294
Narrative reports available                   299
Final cohort per individual project           [project-specific]
```

---

## 4. Ground-Truth and Schema Rules

1. **Do not use the folder names `normal / bulge / protrusion / extrusion` as ground truth.** The folder grouping is lossy and contains known inconsistencies. Local labels must come from the verified radiology reports / audited structured matrix.
2. **Reports are primary.** The older spreadsheet is a transcription and contains known age discrepancies; it must not override the source reports.
3. **Local and RSNA schemas are not interchangeable.** Local reports contain central canal stenosis frequently, foraminal narrowing incompletely, no verified subarticular/lateral-recess labels, and limited laterality. Therefore local external transfer is restricted to targets with defensible ground truth, principally central canal stenosis at five levels unless fresh radiologist grading is obtained.
4. **Ground truth must be independently auditable.** The evaluation set for each project must have a documented annotation / verification procedure and an agreement statistic where feasible.
5. **Patient-level independence is mandatory.** No patient may appear in more than one training / validation / test partition.

---

## 5. Ethics, Governance and Access — Approval Conditions

These are **conditions of data access**, not optional wording edits.

### 5.1 Institutional authority

Before any student receives local clinical data, record the exact hospital / institutional authority under which the work proceeds:

- hospital research committee / IRB / ethics reference number and date;
- lawful consent or waiver basis for retrospective de-identified research;
- permitted data-processing environment;
- publication and data-sharing restrictions.

### 5.2 DICOM de-identification

The local DICOM export is **not yet safe for student distribution**. The de-identification tool has been dry-run, but the clean copy and restricted linkage file remain to be completed.

Required before MSc 2 or local-image PhD work:

- [ ] de-identified DICOM copy generated;
- [ ] linkage key stored separately under restricted access;
- [ ] private tags reviewed / stripped as appropriate;
- [ ] UIDs handled according to the hospital-approved de-identification policy;
- [ ] burned-in pixel text checked where relevant;
- [ ] only de-identified data released to students;
- [ ] cloud / external GPU use confirmed as permissible before upload.

### 5.3 Public release is separate from research use

A future data descriptor or public release requires **separate hospital permission** and a stricter disclosure review. Internal research approval does not imply permission to publish the imaging dataset.

### 5.4 MSc 4 requires additional approval

Linking symptoms, treatment decisions or outcomes to imaging is a new disclosure scope and must receive explicit institutional approval before MSc 4 is advertised as available.

---

## 6. Independence of Student Projects

The original dependency chain has been removed.

| Project | Independent start plan |
|---|---|
| **MSc 1** | Manually structure the 299 reports for its own epidemiological / cohort analysis; later compare with MSc 3 automated extraction as a validation exercise. |
| **MSc 3** | Own the NLP research question and automated extraction method. It does not need the PhD model. |
| **MSc 2** | Train matched standard baselines for each sequence configuration; AMOG-Net is an optional later comparator, never a prerequisite. |
| **PhD** | Begin with public RSNA + SPIDER. It does not depend on local NLP extraction during the core-method development phase. |
| **MSc 4** | No allocation until clinical records and permissions are confirmed. |

---

## 7. Project Boundaries, Data Stewardship and Authorship

Shared data do not create automatic authorship.

- **MSc 1 owns the epidemiological / cohort research question and statistical analysis.**
- **MSc 2 owns the sequence-ablation / protocol-optimisation research question and matched-model experiments.**
- **MSc 3 owns the NLP method comparison, error analysis and structured-extraction tool.**
- **The PhD owns the novel disease-adaptive heterogeneous graph, cross-sequence self-supervision, missing-modality robustness and domain-transfer methodology.**
- **MSc 4, if activated, owns the clinical linkage / prognostic analysis.**

The verified structured matrix is a **programme / hospital research asset**, not the personal property of one student. Authorship follows substantive contribution under institutional policy / CRediT principles rather than mere access to the same dataset.

---

## 8. Updated PhD Novelty Position

The doctoral work must not claim novelty merely from combining:

- segmentation / localisation;
- multi-sequence MRI;
- a Transformer across lumbar levels;
- ordinal grading;
- quantitative biomarkers.

A June 2026 study by Chai et al. already combines anatomy-guided segmentation, level-specific multi-sequence ROIs, anatomical biomarkers, inter-level Transformer context, ordinal grading and consistency regularisation. Therefore the revised doctoral novelty is deliberately narrower and stronger:

1. **Heterogeneous disease–anatomy graph:** 25 condition-level nodes with typed relations for adjacent levels, bilateral anatomy and same-level condition interactions—not merely five ordered lumbar-level tokens.
2. **Disease-conditioned adaptive sequence routing:** the model learns which sequence is informative for each condition / level / case and remains functional under arbitrary missing modalities.
3. **Anatomically aligned cross-sequence self-supervised learning:** DICOM spatial correspondence defines positive relationships across T1 / sagittal T2 / axial T2 before supervised grading.
4. **Cross-institutional zero-shot and annotation-efficient few-shot adaptation:** public benchmark development followed by genuinely independent local validation.

Ordinal loss, uncertainty calibration, localisation and 2.5D ROIs remain important **supporting methods**, but they are not presented as independent novelty claims.

Key closest-work reference: Chai Z, Liu C, Qin R, Zhao D, Shi A. (2026). *Anatomy-guided context-aware deep learning for lumbar degenerative disease grading and burden-aware risk assessment on MRI*. Frontiers in Medicine, 13, 1848548. https://doi.org/10.3389/fmed.2026.1848548

---

## 9. Publication Policy

The programme aims to produce manuscripts suitable for peer-reviewed submission; **publication is never guaranteed**.

Use three venue levels internally:

- **Reach:** ambitious venue if the evidence is exceptional;
- **Target:** realistic first-choice venue for the completed study;
- **Fallback:** credible indexed venue if the first-choice scope or review outcome does not fit.

Student-facing project descriptions should say **"expected output: a thesis plus a manuscript prepared for journal submission"**, not "high publication certainty" or "guaranteed publication".

For the PhD, a realistic working target is **3–4 submitted original papers with 1–2 accepted during candidature**, while recognising that acceptance timing is outside the candidate's control.

---

## 10. Committee Recommendation

**Recommended decision: APPROVE IN PRINCIPLE, subject to the following conditions before student advertisement / local DICOM access:**

1. complete ethics / institutional reference fields;
2. generate and verify the de-identified DICOM copy;
3. reconcile 341 raw DICOM studies → 294 eligible imaging cases → project-specific cohorts;
4. use the revised MSc 1 non-population framing;
5. use matched independently trained sequence models in MSc 2 rather than zeroing modalities at test time;
6. use an independent / adjudicated reference standard for the MSc 3 test set;
7. keep MSc 4 unavailable until clinical linkage data and approval are confirmed;
8. use the revised PhD novelty claims that explicitly differentiate the work from Chai et al. 2026 and M-SCAN.

With these conditions satisfied, the programme is suitable for publication as a structured postgraduate research-opportunities catalogue.
