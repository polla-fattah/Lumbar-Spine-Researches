# AMOG-Net v2 — Technical Specification

**Disease-Adaptive Heterogeneous Graph Learning with Anatomically Aligned Multi-Sequence MRI Representations**  
Supervisor: Dr. Polla Abdulhamid Fattah · Candidate: Selar  
Companion to [`01_SELAR_PHD_ROADMAP.md`](01_SELAR_PHD_ROADMAP.md)

---

## 1. Novelty Boundary First

The technical design has been revised because the 2026 literature now occupies much of the obvious "anatomy + multi-sequence + inter-level context + ordinal grading" space.

### Closest recent method: Chai et al. 2026

Chai et al. already provide:

- vertebra / disc / canal segmentation;
- level-specific multi-sequence MRI ROIs;
- quantitative anatomical biomarkers;
- Transformer context across lumbar levels;
- ordinal grading for canal, foraminal and subarticular disease;
- consistency regularisation;
- patient-level degeneration-burden assessment.

Therefore the PhD must **not** claim novelty from those ingredients alone.

### Other nearby work

- **M-SCAN (2025):** lumbar localisation, sagittal / axial multi-view fusion and cross-attention for spinal-canal stenosis.
- **CNN–GNN IVD grading work:** automated disc segmentation / 3D representation followed by graph-based Pfirrmann grading.

### Revised novelty claim

The doctoral contribution is concentrated in three methodological ideas plus one translational validation programme:

1. **A heterogeneous disease–anatomy graph** over condition, level and laterality, with typed anatomical relations.
2. **Disease-conditioned adaptive MRI sequence routing** that remains functional when sequences are missing.
3. **Anatomically aligned cross-sequence self-supervised learning** using DICOM patient-space correspondence.
4. **Cross-institutional zero-shot → few-shot transfer analysis** on an independent Middle Eastern clinical cohort.

Localisation, 2.5D ROIs, ordinal losses and uncertainty remain supporting components.

---

## 2. Prediction Problem

LumbarDISC is a structured multi-target grading problem, not a generic image-level Normal / Moderate / Severe task.

At full benchmark scope the model predicts:

```text
5 lumbar levels × 5 anatomical-condition targets = 25 targets
```

Per level:

- spinal canal stenosis;
- left neural foraminal narrowing;
- right neural foraminal narrowing;
- left subarticular stenosis;
- right subarticular stenosis.

Each target receives the ordered grade:

```text
Normal/Mild < Moderate < Severe
```

The local Rizgary external cohort does **not** provide all 25 targets. External transfer is restricted to the defensible overlap—primarily five central-canal targets—unless fresh radiologist annotation expands the reference standard.

---

## 3. System Overview

```text
DICOM MRI volumes
    ↓
Patient-space geometry reconstruction
    ↓
Anatomical localisation / disease-specific ROI generation
    ↓
Sequence-specific encoders
    ↓
Anatomically aligned cross-sequence self-supervised representation
    ↓
Disease-conditioned sequence router with modality dropout
    ↓
Heterogeneous disease–anatomy graph transformer
    ↓
Ordinal / cost-sensitive target heads
    ↓
Calibration + uncertainty / selective prediction
```

The novelty lives in the **representation / routing / graph reasoning**, not in choosing a newer backbone.

---

## 4. Preserve DICOM Geometry

Do not reduce DICOM to PNG as the primary scientific representation.

Use patient-space metadata such as:

- `ImagePositionPatient`;
- `ImageOrientationPatient`;
- `PixelSpacing`;
- `SliceThickness` / spacing information;
- series orientation and instance ordering.

The system must be able to determine that a sagittal L4–L5 region corresponds anatomically to specific axial slices.

This geometry supports both ROI extraction and the anatomical self-supervision objective.

---

## 5. Anatomical Localisation — Enabling Technology, Not Novelty

Use an established strong anatomical method rather than inventing another U-Net unless the localisation task itself produces a substantial new finding.

Possible implementation:

- 3D / 2.5D nnU-Net / MONAI model;
- heatmap landmark regression;
- SPIDER-pretrained vertebra / disc / canal parser;
- other state-of-the-art model selected at implementation time.

Outputs:

```text
L1–L2, L2–L3, L3–L4, L4–L5, L5–S1 centres
+ relevant canal / disc / foraminal geometry
```

Evaluation:

- localisation error in millimetres;
- PCK / landmark accuracy;
- Dice / surface metrics where masks are available.

---

## 6. Disease-Specific 2.5D ROIs

Different targets should not receive identical evidence by default.

Examples:

- **canal stenosis:** sagittal T2/STIR context + corresponding axial T2 stack;
- **foraminal narrowing:** sagittal T1 / sagittal T2 with side-aware ROI;
- **subarticular stenosis:** axial T2 dominant evidence plus sagittal context.

Use a small stack around the target rather than a single arbitrary slice:

```text
[I(-2), I(-1), I(0), I(+1), I(+2)]
```

2.5D itself is not novel; it is a memory-efficient representation that supports the core methods.

---

# 7. Core Contribution I — Anatomically Aligned Cross-Sequence Self-Supervised Learning

The self-supervised objective uses anatomical correspondence rather than only generic image augmentation.

For patient `p`, level `l`, sequences `m1` and `m2`:

```text
z(p,l,m1)  ↔  z(p,l,m2)
```

should represent the same underlying anatomical level even when visual appearance differs.

A contrastive objective may use:

```text
L_AC = -log exp(sim(z_i,z_i+)/τ) / Σ_j exp(sim(z_i,z_j)/τ)
```

### Pairing hierarchy

- same patient + same level + different sequence → strong positive;
- same patient + adjacent level → optional soft relation, tested rather than assumed;
- different patient + same level → optional semantic relation in a separate objective;
- unrelated patient / target → negative or non-positive pair.

### Required baselines

Compare against:

- ImageNet / generic pretrained encoder;
- generic medical volumetric pretraining;
- ordinary augmentation-based contrastive learning;
- supervised training from scratch.

### Primary question

Does anatomical cross-sequence pretraining improve:

- macro F1 / kappa;
- label efficiency at 10%, 25%, 50%, 100% labelled data;
- cross-institutional robustness?

---

# 8. Core Contribution II — Disease-Conditioned Adaptive Sequence Routing

The model should not assume that every disease requires every MRI sequence equally.

For condition `c`, level `l`, patient `x`, available modality `m`:

```text
F(c,l,x) = Σ_m g(c,l,m,x) · F_m(l,x)
```

with:

```text
Σ_m g(c,l,m,x) = 1   over available modalities
```

The gate `g` may be implemented with:

- a lightweight gating MLP;
- mixture-of-experts routing;
- target-conditioned attention;
- another transparent learned routing mechanism.

### Missing-modality training

Randomly remove sequences during training:

- no sagittal T1;
- no axial T2;
- no sagittal T2;
- two-sequence combinations;
- single-sequence edge cases.

The model must explicitly mask unavailable modalities rather than encode missing data as arbitrary zeros without training for that condition.

### Required comparisons

1. fixed concatenation / average fusion;
2. ordinary cross-attention;
3. disease-conditioned routing;
4. disease-conditioned routing + modality dropout.

### Interpretability claim

Routing weights are **not proof of causal importance**. They are learned model allocations. Their clinical plausibility should be compared with known sequence utility and validated by controlled ablation.

---

# 9. Core Contribution III — Heterogeneous Disease–Anatomy Graph

Do not represent the lumbar spine as only five ordered level tokens.

Create a target-level graph:

```text
v(L4-L5, Canal)
v(L4-L5, LeftForamen)
v(L4-L5, RightForamen)
v(L4-L5, LeftSubarticular)
v(L4-L5, RightSubarticular)
...
```

At full benchmark scope:

```text
|V| = 25
```

### Typed edge families

**A. Adjacent-level edges**

```text
L3–L4 ↔ L4–L5 ↔ L5–S1
```

for the same or clinically related targets.

**B. Same-level cross-condition edges**

```text
Canal ↔ Foraminal ↔ Subarticular
```

**C. Bilateral edges**

```text
LeftForamen ↔ RightForamen
LeftSubarticular ↔ RightSubarticular
```

The exact topology must be clinically justified and ablated.

### Relation-aware message passing

Conceptually:

```text
h_i' = Σ_{j∈N(i)} α(i,j,r) · W_r h_j
```

where `r` denotes relation type.

### Required graph baselines

- independent target heads;
- ordered five-level Transformer;
- homogeneous GAT / GraphSAGE;
- heterogeneous relation-aware graph;
- shuffled / random edge control.

The random-edge control is important: if a graph with arbitrary edges performs equally well, the anatomical topology has not been shown to matter.

---

# 10. Supporting Method — Ordinal and Cost-Sensitive Grading

Severity is ordered:

```text
Normal/Mild < Moderate < Severe
```

Use ordinary cross-entropy as a mandatory baseline. Test ordinal objectives such as cumulative-link / CORAL / CORN rather than assuming they will be superior.

A clinically motivated cost term may penalise:

```text
Severe → Normal
```

more heavily than:

```text
Severe → Moderate
```

but the cost matrix must be clinically justified and sensitivity-tested.

This component is **supporting methodology**, because ordinal lumbar grading is already active in the literature.

---

# 11. Supporting Method — Calibration and Uncertainty

Model output should include probability reliability, not only a class.

Evaluate:

- temperature scaling;
- deep ensembles / MC dropout / other feasible uncertainty methods;
- Expected Calibration Error;
- Brier score;
- selective prediction curves.

Example decision rule:

```text
if uncertainty(x) > δ:
    abstain / refer for human review
```

Do not imply that uncertainty calibration alone proves clinical safety.

---

# 12. Training Objective

A possible composite objective is:

```text
L_total =
    L_grade
  + λ1 L_anatomical_SSL
  + λ2 L_graph
  + λ3 L_cost
  + λ4 L_consistency
```

where:

- `L_grade`: mandatory supervised classification / ordinal objective;
- `L_anatomical_SSL`: pretraining or joint anatomical alignment objective;
- `L_graph`: graph regularisation / supervised graph contribution where required;
- `L_cost`: optional clinically cost-sensitive term;
- `L_consistency`: optional missing-modality / prediction consistency term.

Every λ term must be ablated. A loss term that adds no measurable value should be removed or reported as a negative result.

---

# 13. Experimental Ladder

| Experiment | Model |
|---|---|
| **E0** | Independent ROI classifier |
| **E1** | + DICOM-aligned multi-sequence ROIs |
| **E2** | + disease-conditioned sequence routing |
| **E3** | + missing-modality / modality-dropout training |
| **E4** | + anatomical cross-sequence SSL |
| **E5** | + homogeneous graph baseline |
| **E6** | + heterogeneous typed graph |
| **E7** | + ordinal / cost-sensitive / calibration support |
| **E8** | complete system + external transfer |

The key comparisons are not only "E8 vs E0". They must isolate:

- anatomical SSL effect;
- adaptive routing effect;
- missing-modality effect;
- heterogeneous topology effect;
- external generalisation effect.

---

# 14. Closest-Work Differentiation

| Feature | M-SCAN | Chai et al. 2026 | Proposed AMOG-Net v2 |
|---|---|---|---|
| Level localisation / ROI | Yes | Yes | Yes — supporting |
| Multi-sequence / multi-view | Yes | Yes | Yes |
| Inter-level context | Limited / task-specific | **Yes, Transformer** | Yes, but not the core novelty |
| Ordinal grading | Task dependent | **Yes** | Supporting baseline / extension |
| Quantitative biomarkers | Not core | **Yes** | Optional supporting features |
| Graph structure | No explicit 25-target heterogeneous graph | No typed 25-target disease graph | **Core contribution** |
| Disease-conditioned sequence routing | No | No explicit target-conditioned missing-modality router | **Core contribution** |
| Arbitrary missing-sequence robustness | Not core | Not core | **Core contribution** |
| Anatomical cross-sequence SSL | No | No | **Core contribution** |
| Independent Middle Eastern external test | No | No | **Core translational validation** |
| Few-shot annotation-efficiency transfer | No | No | **Core translational validation** |

This table should be updated again immediately before proposal submission and before each paper submission.

---

# 15. External Validation and Domain Adaptation

### Zero-shot experiment

Train on public benchmark data only, then freeze the model and evaluate on Rizgary without local tuning.

Primary local overlap:

```text
central canal stenosis × 5 levels
```

### Few-shot experiment

Adapt with:

```text
N = 10, 25, 50, 100 local labelled cases
```

Compare:

- no adaptation;
- intensity harmonisation only;
- adapter / PEFT;
- full fine-tuning where feasible.

Plot:

```text
performance vs local annotation count
```

No predetermined recovery percentage defines success.

---

# 16. Evaluation Metrics

### Grading

- macro F1;
- balanced accuracy;
- quadratic weighted kappa;
- per-class recall / specificity;
- Severe → Normal error rate;
- AUROC;
- patient-level bootstrap CIs.

### Calibration

- ECE;
- Brier score;
- reliability curves;
- risk–coverage / selective prediction.

### Robustness

- missing-modality configurations;
- site-held-out public validation where possible;
- local zero-shot external validation;
- few-shot adaptation curves;
- subgroup analysis by acquisition characteristics where sample size supports it.

### Efficiency

- inference time;
- parameters;
- VRAM;
- training time / compute budget.

---

# 17. Disciplined Final Novelty Statement

A defensible proposal claim is:

> **This PhD investigates whether lumbar degenerative grading can be improved by representing disease targets as a typed anatomical graph, learning disease- and patient-specific MRI sequence routing that remains robust to missing modalities, and pretraining cross-sequence representations using anatomical correspondence, with independent cross-institutional zero-shot and few-shot validation.**

It deliberately does **not** claim that anatomy-guided ROIs, multi-sequence MRI, inter-level Transformers or ordinal grading are new by themselves.

---

## References Most Important to the Novelty Boundary

1. Chai Z, Liu C, Qin R, Zhao D, Shi A. (2026). *Anatomy-guided context-aware deep learning for lumbar degenerative disease grading and burden-aware risk assessment on MRI*. Frontiers in Medicine, 13:1848548. https://doi.org/10.3389/fmed.2026.1848548
2. M-SCAN: A Multistage Framework for Lumbar Spinal Canal Stenosis Grading Using Multi-View Cross Attention. 2025. https://arxiv.org/abs/2503.01634
3. Automated Three-Dimensional Imaging and Pfirrmann Classification of Intervertebral Disc Using a Graphical Neural Network in Sagittal MRI of the Lumbar Spine. https://pubmed.ncbi.nlm.nih.gov/39266913/
4. LumbarDISC dataset publication / RSNA benchmark documentation. https://pubs.rsna.org/doi/10.1148/ryai.250480
