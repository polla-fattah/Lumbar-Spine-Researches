# PhD Research Plan — Candidate: Selar

**Proposed Thesis Title:** Disease-Adaptive Heterogeneous Graph Learning with Missing-Modality Robustness and Cross-Institutional Transfer for Lumbar Spine MRI  
**Supervisor:** Dr. Polla Abdulhamid Fattah  
**Target Degree:** PhD in Computer Science / Artificial Intelligence  
**Duration:** 21–24 Months  
**Working System Name:** AMOG-Net v2 — Anatomy- and Modality-Aware Heterogeneous Graph Network

---

## 1. Doctoral Research Problem

Automated lumbar MRI grading has progressed beyond simple image classification. Recent systems already use anatomical localisation, multi-sequence ROIs, cross-view attention, anatomical biomarkers, multi-level context and ordinal grading. Therefore this PhD does **not** claim novelty from any of those components alone.

The revised doctoral problem is:

> **Can explicit disease–anatomy relationships, disease-conditioned MRI sequence routing, anatomically aligned cross-sequence self-supervision, and annotation-efficient cross-institutional adaptation improve the robustness and clinical coherence of lumbar degenerative disease grading?**

The work is trained primarily on public benchmark data and then tested on a genuinely independent Middle Eastern hospital cohort, restricted to local targets for which defensible ground truth exists.

---

## 2. Closest Work and Novelty Boundary

### Chai et al. 2026 — closest recent overlap

Chai et al. already combine:

- anatomy-guided vertebra / disc / canal segmentation;
- level-specific multi-sequence ROIs;
- quantitative anatomical biomarkers;
- Transformer-based inter-level context;
- ordinal grading of lumbar degenerative findings;
- consistency regularisation and patient-level burden assessment.

Therefore **"anatomy + multi-sequence + inter-level Transformer + ordinal grading" is not sufficient novelty in 2026.**

### Revised doctoral contributions

1. **Heterogeneous disease–anatomy graph**  
   Represent each condition / level / side as its own node (up to 25 RSNA targets) with typed edges for adjacent levels, bilateral anatomy and same-level disease interactions.

2. **Disease-conditioned adaptive sequence routing with missing-modality robustness**  
   Learn which sequence(s) should contribute to each target and each patient rather than assuming a fixed fusion rule. Train with modality dropout so the model can operate when one or more sequences are unavailable.

3. **Anatomically aligned cross-sequence self-supervised learning**  
   Use DICOM patient-space correspondence to define positive relationships among T1, sagittal T2/STIR and axial T2 representations of the same patient and spinal level.

4. **Cross-institutional zero-shot and few-shot transfer analysis**  
   Quantify the real degradation from a public multinational benchmark to an unseen local clinical cohort, then measure the annotation-efficiency of adaptation.

### Supporting, not standalone novelty

- localisation / segmentation;
- 2.5D ROI extraction;
- ordinal loss;
- class-imbalance handling;
- uncertainty calibration;
- standard CNN / Transformer backbones.

These remain part of the system but are not individually advertised as original contributions.

---

## 3. Research Questions

**RQ1 — Heterogeneous anatomical reasoning**  
Does relation-aware modelling of condition, level and laterality improve multi-target grading compared with independent target heads and a simple five-level sequence Transformer?

**RQ2 — Disease-conditioned modality routing**  
Can the model learn target-specific MRI sequence importance and remain robust when one or more sequences are missing, without requiring a separately trained network for every modality combination?

**RQ3 — Anatomically aligned self-supervision**  
Does cross-sequence pretraining based on DICOM anatomical correspondence improve grading performance and label efficiency compared with ImageNet / generic volumetric pretraining and ordinary augmentation-based self-supervision?

**RQ4 — Cross-institutional generalisation and adaptation**  
What performance degradation occurs when a benchmark-trained model is applied zero-shot to Rizgary, and how does performance recover as local labelled cases increase (e.g., N = 10, 25, 50, 100) under parameter-efficient adaptation?

No fixed recovery percentage is a success criterion. The recovery curve itself is the scientific result.

---

## 4. Data and Target Definition

### 4.1 Public development data

- **LumbarDISC / RSNA 2024:** use the locally held labelled Kaggle training subset (approximately 1,975 studies) for core model development, while citing the full published cohort correctly as 2,697 patients / 8,593 MRI series.
- **SPIDER:** use for anatomical segmentation / localisation benchmarking and pretraining where licence terms permit.

### 4.2 Local external test data

- 294 currently identified eligible multi-sequence Rizgary imaging cases, after the raw-study reconciliation and DICOM de-identification are complete.
- 299 narrative reports used to construct / verify local reference labels.

### 4.3 Local target scope

Do **not** pretend that Rizgary reproduces the RSNA 25-target schema.

Primary external-transfer target:

- **central canal stenosis at L1–L2 through L5–S1 (5 targets)**

Secondary local morphology task, analysed separately:

- bulge / protrusion / extrusion at reported lumbar levels.

Foraminal transfer is included only where laterality and grade are sufficiently documented or after fresh radiologist annotation. Subarticular / lateral-recess transfer is excluded unless new reference grading is created.

---

## 5. Proposed Architecture

```text
DICOM volumes
    ↓
Anatomical localisation / disease-specific ROI extraction
    ↓
Sequence-specific encoders
    ↓
Anatomically aligned cross-sequence self-supervised representation
    ↓
Disease-conditioned sequence router
    ↓
Heterogeneous disease–anatomy graph transformer
    ↓
Ordinal / cost-sensitive grading heads
    ↓
Probability calibration + uncertainty / selective prediction
```

### 5.1 Graph definition

At full RSNA scope:

```text
5 lumbar levels × 5 condition/laterality targets = 25 nodes
```

Typed relations include:

- adjacent-level relations;
- bilateral relations;
- same-level cross-condition relations.

The graph must be tested against:

- independent target heads;
- a simple ordered five-level Transformer;
- a homogeneous graph without typed relations.

This is essential to show that the heterogeneous topology—not merely "using a graph"—adds value.

### 5.2 Adaptive sequence routing

For target c at level l:

```text
F(c,l) = Σ_m g(c,l,m,x) · F_m(l)
```

where `m` indexes available MRI sequences and `g` is a learned, normalised target- and patient-dependent gate.

Training includes modality dropout and explicit missing-modality experiments.

### 5.3 Anatomical self-supervision

Positive relationships are defined using DICOM geometry:

- same patient + same level + different sequence → strong positive;
- same patient + adjacent level → optional soft relation;
- unrelated patient / level combinations → negatives or non-positive pairs according to the selected objective.

The method is compared with ordinary augmentation-based contrastive learning and generic pretraining.

---

## 6. Experimental Programme

### Phase 1 — Benchmark infrastructure and foundations (Months 1–3)

- preprocess / harmonise the labelled RSNA subset;
- reconstruct patient-space geometry from DICOM metadata;
- implement / verify patient-level splits;
- implement anatomical localisation using SPIDER or an established segmentation model;
- reproduce at least one strong baseline;
- complete the literature closest-work matrix, including Chai et al. 2026, M-SCAN and relevant GNN lumbar work.

**Important:** automated local report extraction is an MSc 3 task, not a mandatory PhD deliverable. The PhD consumes the verified local matrix when available.

### Phase 2 — Core methods (Months 4–10)

Build progressively rather than attempting the full architecture at once:

| Step | Experiment |
|---|---|
| E0 | Independent ROI classifier baseline |
| E1 | + anatomically correct cross-sequence ROI alignment |
| E2 | + disease-conditioned adaptive sequence routing |
| E3 | + missing-modality / modality-dropout training |
| E4 | + anatomically aligned cross-sequence self-supervision |
| E5 | + heterogeneous disease–anatomy graph |
| E6 | + cost-sensitive ordinal heads and calibration |
| E7 | full system |

Every increment receives confidence intervals and paired statistical comparison. Components that do not help remain reported as negative findings.

### Phase 3 — Cross-institutional transfer (Months 11–16)

After local DICOM de-identification and reference-label approval:

1. freeze the public-data model;
2. evaluate zero-shot on local canal-stenosis targets;
3. stratify degradation by level, scanner / acquisition features and severity;
4. adapt using N = 10, 25, 50, 100 local labelled cases;
5. compare PEFT / adapter approaches with full fine-tuning and simple intensity harmonisation where feasible;
6. report annotation-efficiency curves rather than a predetermined success threshold.

### Phase 4 — synthesis, external credibility and thesis (Months 17–24)

- final site-held-out / external analyses;
- integrated ablation and robustness study;
- dissertation synthesis;
- code / reproducibility package subject to dataset licence and hospital policy;
- optional reader / clinical-impact study only if separately approved and feasible.

---

## 7. Evaluation

### Primary grading metrics

- macro F1;
- balanced accuracy;
- quadratic weighted kappa;
- per-class sensitivity / recall, especially Severe;
- one-vs-rest AUROC;
- Severe → Normal error rate;
- confidence intervals via patient-level bootstrap.

### Calibration / uncertainty

- Expected Calibration Error;
- Brier score;
- reliability diagrams;
- coverage vs risk for selective prediction.

### Localisation

- localisation error in mm;
- PCK or equivalent landmark accuracy;
- surface / Dice metrics only where masks exist.

### Robustness

- institution-held-out validation where public data permit;
- missing-sequence performance;
- scanner / protocol subgroup analysis;
- zero-shot local degradation;
- few-shot recovery curve.

### Efficiency

- parameters;
- FLOPs / MACs where appropriate;
- VRAM;
- inference time;
- training time / compute budget.

---

## 8. Publication Plan

The PhD is not required to publish every architectural component separately.

**Working target:** 3–4 original manuscripts submitted, with at least 1–2 accepted during candidature if review timelines allow.

### Candidate Paper A — Cross-sequence anatomical pretraining + disease-adaptive routing

Core contribution: anatomically aligned SSL plus target-specific modality routing and missing-modality robustness.

### Candidate Paper B — Heterogeneous disease–anatomy graph

Core contribution: typed 25-node anatomical-condition graph, directly compared with independent heads and simple inter-level Transformers.

### Candidate Paper C — Cross-institutional zero-shot and few-shot transfer

Core contribution: performance degradation and annotation-efficiency when transferring from the public benchmark to the unseen Rizgary cohort.

### Candidate Paper D — Integrated system / clinical validation

Only if the full system and local validation are strong enough to justify an integrated manuscript.

Submission is controllable; acceptance timing is not. Each manuscript should have a reach, target and fallback venue selected at the time of writing.

---

## 9. Key Risks and Mitigation

| Risk | Severity | Mitigation |
|---|---:|---|
| Chai et al. 2026 overlaps with anatomy + multi-sequence + inter-level context + ordinal grading | **High if ignored** | Explicitly differentiate through heterogeneous condition-level graph, adaptive routing, anatomical SSL and external transfer. |
| Full system becomes too large | High | Stage E0–E7; three central innovations are sufficient if supported rigorously. |
| Heterogeneous graph adds little | Medium | Publish the negative result; retain routing / SSL / transfer contribution. |
| Local zero-shot performance drops severely | Medium | Treat domain shift as a scientific finding; quantify and analyse it. |
| Local labels do not match RSNA schema | Solved by scope | Restrict external grading to defensible overlapping targets. |
| Compute unavailable | Medium | Confirm GPU access before Phase 2; use 2.5D ROIs, mixed precision and staged models. |
| Local DICOM governance incomplete | High for local phase | No student / external-compute access until de-identification and permissions are complete. |

---

## 10. Closest-Work Reference

Chai, Z., Liu, C., Qin, R., Zhao, D., & Shi, A. (2026). Anatomy-guided context-aware deep learning for lumbar degenerative disease grading and burden-aware risk assessment on MRI. *Frontiers in Medicine, 13*, 1848548. https://doi.org/10.3389/fmed.2026.1848548
