# Publication Plan — Revised AMOG-Net Programme

**Companion to:** [`01_SELAR_PHD_ROADMAP.md`](01_SELAR_PHD_ROADMAP.md) and [`07_AMOGNET_TECHNICAL_SPEC.md`](07_AMOGNET_TECHNICAL_SPEC.md)

---

## 1. Publication Principle

This is a **menu of defensible manuscripts**, not a promise to publish every component separately.

The programme should avoid both extremes:

- one enormous paper gated on every component working;
- salami-slicing small ablations into weak papers.

A realistic doctoral output is **3–4 submitted original manuscripts**, with acceptance timing treated as outside the candidate's control.

Use three venue categories internally:

- **Reach** — ambitious venue if the result is exceptional;
- **Target** — realistic venue for the mature study;
- **Fallback** — credible indexed alternative if fit / review outcome requires it.

A fallback is not a guarantee of publication.

---

## 2. Literature Update That Changes the Plan

Chai et al. (Frontiers in Medicine, June 2026) already combine anatomical parsing, level-specific multi-sequence ROIs, quantitative anatomical biomarkers, inter-level Transformer context, ordinal grading and consistency regularisation.

Therefore the following are **not independently strong novelty claims anymore**:

- segmentation-guided grading;
- multi-sequence ROIs;
- inter-level Transformer context;
- ordinal grading alone.

The revised publication programme focuses on the aspects that remain distinct:

1. anatomical cross-sequence self-supervision;
2. disease-conditioned sequence routing + missing-modality robustness;
3. heterogeneous condition-level anatomical graph reasoning;
4. cross-institutional zero-shot / few-shot adaptation;
5. integrated validation if the complete system is strong.

---

## 3. Candidate Paper A — Anatomically Aligned Cross-Sequence Learning + Disease-Adaptive Routing

**Working title:** *Anatomically Aligned Cross-Sequence Representation Learning with Disease-Adaptive Modality Routing for Lumbar MRI*

### Core question

Can DICOM-aligned self-supervision and target-conditioned routing improve both label efficiency and robustness to missing MRI sequences?

### Minimum experimental evidence

- generic pretraining vs anatomical SSL;
- fixed fusion vs cross-attention vs disease-conditioned router;
- modality dropout ablation;
- label fractions 10 / 25 / 50 / 100%;
- missing-sequence robustness;
- confidence intervals / repeated seeds.

### Why it can stand alone

The method addresses **how sequences are represented and selected**, not simply whether T1 or T2 performs better.

### Venue planning

- Reach: *Medical Image Analysis* / MICCAI if methodological evidence is strong.
- Target: *IEEE Journal of Biomedical and Health Informatics* / *Artificial Intelligence in Medicine*.
- Fallback: *Computers in Biology and Medicine* / *Scientific Reports* depending on scope.

---

## 4. Candidate Paper B — Heterogeneous Disease–Anatomy Graph

**Working title:** *SpineGraph: Typed Heterogeneous Anatomical Graph Learning for Joint Multi-Level Lumbar Disease Grading*

### Core question

Does an explicit 25-target graph with typed anatomical relations outperform:

- independent target heads;
- a simple five-level Transformer;
- a homogeneous graph;
- a shuffled-edge control?

### Required novelty proof

The paper must show that **typed anatomical topology** matters. Merely adding a GNN is insufficient because graph-based disc grading already exists in the literature.

### Venue planning

- Reach: *IEEE Transactions on Medical Imaging* / *Medical Image Analysis*.
- Target: *IEEE JBHI*.
- Fallback: *Computers in Biology and Medicine*.

This is the paper most worth aiming high with if the effect is substantial and replicated.

---

## 5. Candidate Paper C — Cross-Institutional Generalisation and Few-Shot Adaptation

**Working title:** *Zero-Shot and Annotation-Efficient Transfer of Lumbar MRI Grading to a Middle Eastern Clinical Cohort*

### Core question

How much performance is lost when a public-benchmark model is applied to an unseen local hospital cohort, and how efficiently can that gap be reduced with limited local annotation?

### Primary design

```text
Public benchmark development
        ↓
model frozen
        ↓
Rizgary zero-shot evaluation
        ↓
N = 10 / 25 / 50 / 100 local adaptation
```

### Local target scope

Primary external grading is central canal stenosis at five lumbar levels unless fresh annotation expands the ground truth.

### Why it is strong

The scientific result is the **domain-shift and annotation-efficiency curve**, not a requirement to achieve a predetermined recovery percentage.

### Venue planning

- Reach: *Radiology: Artificial Intelligence*.
- Target: *European Radiology* / *Artificial Intelligence in Medicine*.
- Fallback: *European Spine Journal* / *Scientific Reports* depending on emphasis.

---

## 6. Candidate Paper D — Integrated AMOG-Net v2

**Working title:** *AMOG-Net v2: Disease-Adaptive Heterogeneous Graph Learning for Robust Multi-Sequence Lumbar MRI Assessment*

This manuscript exists only if the main components show meaningful, reproducible value.

It integrates:

```text
localisation
→ anatomical SSL
→ disease-conditioned routing
→ missing-modality robustness
→ heterogeneous graph
→ ordinal / calibrated output
→ external validation
```

### Required evidence

- full E0–E8 ablation;
- closest-work comparison including Chai et al. 2026 and M-SCAN;
- site-held-out / external test;
- uncertainty calibration;
- negative components reported honestly.

If the integrated system does not add more than the component papers, retain it as the thesis synthesis chapter rather than forcing a publication.

---

## 7. Optional Paper E — Local Clinical Impact / Reader Study

This is not a starting PhD paper.

If a working tool, radiologist time and separate ethics approval become available, a reader study can test:

- reporting time;
- agreement;
- severe-case sensitivity;
- performance with vs without AI assistance;
- junior vs senior reader effects.

This would be stronger evidence of clinical impact than retrospective model accuracy alone.

---

## 8. Enabling Work That Should Not Automatically Become a Paper

### Localisation / segmentation

Publish separately only if the localisation method itself contributes something substantial such as:

- cross-sequence anatomical alignment;
- domain-robust level localisation;
- a new annotation resource;
- clear superiority under difficult degenerated anatomy.

"We trained U-Net / nnU-Net for lumbar segmentation" is not enough.

### Ordinal loss

Publish separately only if there is a clear clinically meaningful result. If ordinary cross-entropy performs equally well, report that negative result within a broader methods paper.

---

## 9. Data Descriptor — Conditional Only

A de-identified report-linked Rizgary cohort could become a valuable data descriptor **only if the hospital separately approves public release**.

Do not treat research-use permission as data-sharing permission.

Before any data-descriptor plan:

- separate institutional approval;
- UID policy / regeneration;
- burned-in annotation review;
- privacy risk assessment;
- data-use licence;
- documentation of what can and cannot be shared.

If public image release is not permitted, a metadata / aggregate cohort paper may still be possible without releasing the source imaging.

---

## 10. PhD Publication KPI

Suggested internal KPI:

- minimum: 2 strong original manuscripts submitted;
- working target: 3–4 submitted;
- stretch: 2+ accepted during candidature;
- no requirement that every proposed component becomes a paper.

The contribution is the quality and coherence of the scientific evidence, not the number of manuscript titles.

---

## 11. Closest-Work Reference

Chai Z, Liu C, Qin R, Zhao D, Shi A. (2026). *Anatomy-guided context-aware deep learning for lumbar degenerative disease grading and burden-aware risk assessment on MRI*. Frontiers in Medicine, 13:1848548. https://doi.org/10.3389/fmed.2026.1848548
