Yes. I would combine both plans into **one implementation roadmap with two parallel tracks**:

* **Track A — Public-data model development**: Selar can begin immediately.
* **Track B — Rizgary Hospital data preparation**: proceeds in parallel, but must be ready before external testing.
* They join only at the **zero-shot transfer stage**.

The current methodology already supports exactly this separation: the public model is developed without Rizgary, while the local cohort is kept as a fixed external test set plus a separate adaptation pool.  

# Selar PhD Implementation Master TODO

## Phase 0 — Freeze the research protocol before coding

**Goal:** make sure later changes are recorded as deviations, not silently rewritten.

### 0.1 Freeze the methodology

* [ ] Save the current Chapter 3 as something like:

  * `protocol_chapter3_v1.0_2026-08-25.tex`
* [ ] Keep all `[TO CONFIRM]` and `[TO RECORD]` items.
* [ ] Do not replace unknown values with assumptions.
* [ ] Create a `PROTOCOL_CHANGELOG.md`.
* [ ] Every later methodological change must include:

  * date;
  * section affected;
  * reason;
  * whether the change occurred before or after seeing test results.

### 0.2 Freeze research questions

Use the five RQs exactly as defined in Chapter 3:

* RQ1 heterogeneous relational modelling;
* RQ2 anatomically aligned SSL;
* RQ3 disease-conditioned routing and missing/corrupted modalities;
* RQ4 cross-institutional transfer;
* RQ5 asymmetric error, calibration and uncertainty. 

### 0.3 Create the experiment registry

Create:

```text
experiments/
    EXPERIMENT_REGISTRY.csv
```

Minimum columns:

```text
experiment_id
date_started
research_question
configuration
dataset_version
split_version
code_commit
random_seed
pretraining
backbone
routing
graph
loss
checkpoint
validation_metric
test_status
notes
```

Use fixed IDs such as:

```text
E0-R01
E0-R02
E1-R01
...
```

Never name runs things like:

```text
final_model
final_model2
final_really_final
```

### GATE 0

Do not begin formal experiments until:

* methodology frozen;
* RQs fixed;
* experiment registry exists;
* repository exists;
* version control works.

---

# Phase 1 — Repository and reproducibility infrastructure

**Goal:** make every result reproducible before training becomes complicated.

Recommended repository:

```text
selar_lumbar_phd/
│
├── configs/
│   ├── datasets/
│   ├── models/
│   ├── experiments/
│   └── adaptation/
│
├── data/
│   ├── manifests/
│   ├── splits/
│   └── derived/
│
├── src/
│   ├── dicom/
│   ├── preprocessing/
│   ├── localisation/
│   ├── roi/
│   ├── encoders/
│   ├── ssl/
│   ├── routing/
│   ├── graph/
│   ├── losses/
│   ├── calibration/
│   └── evaluation/
│
├── scripts/
├── tests/
├── experiments/
├── reports/
├── notebooks/
└── docs/
```

### 1.1 Environment

* [ ] Record Python version.
* [ ] Record PyTorch version.
* [ ] Record CUDA/cuDNN.
* [ ] Record GPU model.
* [ ] Create `requirements.txt`, `environment.yml`, or preferably a reproducible lockfile.
* [ ] Record MONAI/SimpleITK/pydicom versions if used.
* [ ] Fix random seeds.
* [ ] Implement deterministic settings where feasible.

Chapter 3 explicitly requires exact environment, software and hardware recording. 

### 1.2 Configuration management

Every experiment should be launched from a configuration file, for example:

```text
configs/experiments/E0_resnet50.yaml
```

It should specify:

* dataset version;
* split;
* preprocessing;
* ROI;
* backbone;
* optimizer;
* learning rate;
* epochs;
* augmentation;
* loss;
* seed.

### 1.3 Automatic logging

Each run should save:

```text
config.yaml
metrics.json
training_log.csv
best_checkpoint.pt
final_checkpoint.pt
predictions.csv
git_commit.txt
environment.txt
```

### GATE 1

Selar must be able to rerun one tiny toy experiment and reproduce essentially the same outputs before real training starts.

---

# TRACK A — PUBLIC-DATA DEVELOPMENT

# Phase 2 — Build the LumbarDISC master manifest

This is the **first serious implementation task**.

### 2.1 Inventory every study

Create:

```text
lumbarDISC_manifest.csv
```

One row per study/series or a normalized study-series structure containing:

```text
patient_id
study_id
series_id
series_description
sequence_type
orientation
slice_count
rows
columns
pixel_spacing
slice_spacing
manufacturer
field_strength
label_availability
coordinate_availability
qc_status
```

### 2.2 Identify sequences

Automatically identify:

* sagittal T1;
* sagittal T2/STIR;
* axial T2.

Do not trust only `SeriesDescription`; verify orientation and acquisition information. The methodology specifically requires metadata plus orientation checks. 

### 2.3 Validate labels

* [ ] Confirm all 25 target names.
* [ ] Confirm five levels:

  * L1–L2;
  * L2–L3;
  * L3–L4;
  * L4–L5;
  * L5–S1.
* [ ] Confirm three grades:

  * Normal/Mild;
  * Moderate;
  * Severe.
* [ ] Create explicit target masks for unavailable labels.

Do not impute missing labels from neighboring levels. 

### 2.4 Dataset sanity report

Generate:

* patient count;
* study count;
* sequence count;
* missing-sequence counts;
* class distribution per target;
* severe count per level;
* scanner/vendor distribution.

### GATE 2

Do not build a classifier until all dataset counts are explainable.

---

# Phase 3 — Create patient-level splits

This is critical.

### 3.1 Generate split IDs once

Create:

```text
splits/
    train_ids.txt
    validation_ids.txt
    public_test_ids.txt
```

No patient may appear in more than one.

### 3.2 Add automated leakage tests

Unit test:

```python
assert train_ids.isdisjoint(validation_ids)
assert train_ids.isdisjoint(test_ids)
assert validation_ids.isdisjoint(test_ids)
```

Also test that:

* no series crosses splits;
* no disc level crosses splits;
* no augmented derivative crosses splits.

The thesis explicitly treats the patient, not the image or disc, as the independent unit. 

### 3.3 Site-aware analysis

If institution identifiers are available:

* [ ] preserve them;
* [ ] consider institution-held-out or leave-one-site-out analysis.

Do not replace the main public test split unless justified; this can be additional analysis. 

### GATE 3

No training until the leakage test passes automatically.

---

# Phase 4 — DICOM geometry pipeline

This should be completed **before AMOG-Net**.

### 4.1 Implement DICOM loading

Read:

* `ImagePositionPatient`;
* `ImageOrientationPatient`;
* `PixelSpacing`;
* `SeriesInstanceUID`;
* slice positions;
* acquisition orientation.

### 4.2 Reconstruct physical coordinates

Implement the Chapter 3 equations for:

* pixel-to-patient coordinates;
* slice normal;
* physical slice ordering;
* sagittal-to-axial correspondence.

Do not sort slices by filename. The methodology explicitly specifies physical-coordinate ordering. 

### 4.3 Handle oblique axial acquisition

Implement:

* disc-plane estimate;
* angular difference;
* geometrically plausible axial candidate set;
* distance + angular compatibility scoring.

Chapter 3 deliberately avoids assuming all axial series are globally orthogonal. 

### 4.4 Build QC visualizations

For perhaps 30–50 randomly sampled cases produce:

```text
sagittal image
disc center
axial plane intersection
selected axial slices
level label
left/right indicator
```

### 4.5 Manual audit

Check:

* L1–L2 through L5–S1 correct;
* axial slices actually intersect intended disc level;
* no left/right inversion;
* no slice-order reversal.

### GATE 4

I would require **very high manual correctness** before downstream classification. A geometry bug here can invalidate the entire thesis.

---

# Phase 5 — Anatomical localisation

### 5.1 Choose an established localiser

Candidates include:

* SPIDER-pretrained nnU-Net-style model;
* heatmap detector;
* another validated lumbar parser.

Localization itself is enabling technology, not the PhD novelty. 

### 5.2 Outputs

For every study save:

```text
level
x_mm
y_mm
z_mm
confidence
localisation_status
```

Optionally:

* disc masks;
* vertebral masks;
* canal masks.

### 5.3 Evaluate localization separately

Report:

* mean error in mm;
* median error;
* 95th percentile;
* PCK;
* failure rate;
* Dice/surface metrics where masks exist.

### 5.4 Save failure flags

Do not silently correct failures.

Use:

```text
PASS
LOW_CONFIDENCE
WRONG_LEVEL
NO_LEVEL_FOUND
AXIAL_CORRESPONDENCE_FAILED
```

### GATE 5

Only continue if localisation is good enough that classifier comparisons will not merely compare crop quality.

---

# Phase 6 — ROI construction

### 6.1 Create disease-specific ROIs

**Central canal**

* sagittal T2/STIR context;
* corresponding axial T2.

**Foraminal narrowing**

* parasagittal T1;
* side-aware ROI;
* sagittal T2 as complementary context.

**Subarticular**

* mainly axial T2;
* sagittal context.

These choices are already explicitly justified clinically in Chapter 3. 

### 6.2 Define ROI dimensions physically

Prefer:

```text
millimetres → resample → network resolution
```

rather than arbitrary fixed pixel widths.

### 6.3 2.5D stack

Initial reference:

* center slice;
* ±2 slices.

Then sensitivity testing if needed.

### 6.4 ROI QC

Save overlays for validation samples.

Check:

* target included;
* no crop truncation;
* correct level;
* correct side;
* adequate axial coverage.

### GATE 6

Freeze the ROI generation method before comparing architectures.

---

# Phase 7 — Build E0 first

This is the first real grading model.

### 7.1 E0 definition

Independent ROI classifier:

* no graph;
* no routing;
* no ACSSL;
* no cross-target communication.

Use one good backbone such as:

* ResNet50;
* EfficientNet;
* ConvNeXt-Tiny;
* Swin-T.

### 7.2 Do not over-optimize architecture choice

Run a small controlled comparison.

Then choose one backbone and **freeze it for the ablation ladder**.

### 7.3 Verify training

Check:

* loss decreases;
* train/validation gap;
* confusion matrix;
* macro-F1;
* balanced accuracy;
* Quadratic Weighted Kappa (QWK);
* severe recall.

### 7.4 Reproduce E0

Repeat it with several seeds.

If runs differ wildly, the pipeline is not stable enough.

### GATE 7

Do not implement AMOG-Net until E0:

* trains reliably;
* produces believable predictions;
* produces reproducible metrics.

---

# Phase 8 — Competitive baselines

Before claiming novelty, implement strong competitors.

### 8.1 Multi-view cross-attention baseline

Create an M-SCAN-like baseline under:

* same split;
* same ROIs;
* same training budget;
* same backbone where feasible.

### 8.2 Ordered inter-level Transformer

Five levels communicate through normal sequence attention.

This is particularly important relative to Chai-style inter-level contextual modelling.

### 8.3 Published-method comparisons

Do not write:

> “Our 0.82 beats their 0.79.”

unless the dataset and protocol are comparable.

Use matched reimplementation whenever possible.

### GATE 8

Now Selar has legitimate strong references against which novelty can be judged.

---

# Phase 9 — E1: Geometry-aligned multisequence representation

Compare:

```text
E0:
independent ROI

E1:
same backbone + correctly aligned multisequence ROI
```

Everything else identical.

Question:

> Does physically correct multisequence correspondence itself help?

Record results before implementing the router.

---

# Phase 10 — E2/E3: Disease-conditioned sequence routing

## 10.1 Basic router

Input:

* normalized sequence features;
* condition embedding;
* level embedding;
* optional acquisition metadata;
* quality features.

Output:

[
g_{p,t,m}
]

for each available sequence.

### 10.2 Baselines

Compare:

* concatenation;
* average fusion;
* cross-attention;
* disease-conditioned routing.

### 10.3 Missing-modality masking

Implement explicit availability mask.

Never represent a missing sequence merely as an empty image. 

### 10.4 Modality dropout

Train using:

* all three sequences;
* T1 + sagittal T2;
* sagittal T2 + axial T2;
* T1 + axial T2;
* individual sequences where meaningful.

### 10.5 Corrupted modality tests

Simulate:

* motion;
* noise;
* bias field;
* slice loss;
* truncation;
* resolution degradation.

The improved methodology now makes corruption explicitly different from absence. 

### 10.6 Router diagnostics

Save:

* routing weights;
* gate entropy;
* per-target sequence preference.

Detect collapse:

```text
if router always chooses sagittal T2
→ routing novelty has failed
```

Do not hide this.

### GATE 10

Continue only after proving whether routing really beats simpler fusion.

---

# Phase 11 — E4: Anatomically aligned cross-sequence SSL

### 11.1 Build positive pairs

Strong positive:

```text
same patient
same lumbar level
different MRI sequence
```

Do not use adjacent levels as primary positives.

### 11.2 Implement projection head

Use:

[
f \rightarrow P_m(f)\rightarrow z
]

The downstream classifier uses encoder features before projection.

### 11.3 Initial SSL baselines

Compare:

* random initialization;
* ImageNet;
* generic SSL;
* generic medical pretraining;
* anatomical cross-sequence SSL.

### 11.4 Label efficiency

Repeat supervised training using:

* 10%;
* 25%;
* 50%;
* 100%

of labels.

### 11.5 Sequence-preservation test

Test whether ACSSL accidentally erases sequence-specific information.

Compare:

* T1-only probes;
* sagittal-T2-only probes;
* axial-T2-only probes.

This safeguard is explicitly part of the revised methodology. 

### GATE 11

If ACSSL does not help, keep the negative result and move on.

Do not force it into the final architecture.

---

# Phase 12 — E5/E6: Heterogeneous disease–anatomy graph

Only now should Selar implement the graph.

### 12.1 Construct 25 nodes

[
5\ levels\times5\ targets=25\ nodes
]

Each node contains:

* routed visual feature;
* level embedding;
* condition embedding.

### 12.2 Add typed edges

Three edge families:

```text
A. adjacent level
B. same-level cross-condition
C. bilateral
```

### 12.3 Implement evidence masks

Distinguish:

```text
missing LABEL
vs
missing IMAGE EVIDENCE
```

Missing labels should not necessarily delete graph nodes. 

### 12.4 Required graph comparisons

Run:

```text
independent heads
ordered level Transformer
homogeneous graph
heterogeneous graph
ungated heterogeneous graph
gated heterogeneous graph
shuffled-edge graph
```

### 12.5 Edge ablation

Test:

* no adjacency;
* no bilateral;
* no cross-condition;
* each family alone.

### 12.6 Information-contagion stress test

Find natural cases where:

```text
L4-L5 = Severe
L3-L4 = Normal/Mild
```

Measure whether graph inference incorrectly elevates the normal adjacent level.

The new methodology explicitly requires this stress test. 

### GATE 12

Retain the graph only if:

* overall performance improves or meaningful robustness improves;
* shuffled/random topology performs worse;
* isolated-lesion false positives do not materially increase.

---

# Phase 13 — E7: Losses, calibration and uncertainty

Do this **after the main representation is working**.

### 13.1 Mandatory baseline

Cross-entropy.

### 13.2 Compare alternatives

* class weighting;
* focal loss;
* ordinal threshold formulation;
* asymmetric cost-sensitive loss.

### 13.3 Cost-tradeoff evaluation

Do not report only severe recall.

Report:

* Severe sensitivity;
* Severe specificity;
* Severe PPV;
* Severe→Normal rate;
* Normal→Severe rate;
* percentage predicted Severe.

The revised methodology explicitly guards against “solve undergrading by predicting Severe everywhere.” 

### 13.4 Calibration

Fit only on validation data:

* temperature scaling.

Evaluate:

* Brier score;
* ECE;
* reliability diagrams.

### 13.5 Uncertainty

Primary:

* MC dropout or small ensemble.

Secondary if useful:

* conformal prediction and risk-coverage curves for selective prediction.

Do not let conformal prediction become a separate mini-PhD.

### GATE 13

Select the simplest configuration that gives reproducible clinical or statistical benefit.

---

# TRACK B — RIZGARY HOSPITAL DATA PREPARATION

This track should occur **in parallel** with Phases 2–13.

# Phase R1 — Permissions and ethics

Before Selar receives local DICOM data:

* [ ] formal hospital approval;
* [ ] ethics/IRB reference;
* [ ] consent/waiver basis;
* [ ] approved storage location;
* [ ] confirmation whether cloud/GPU processing is permitted;
* [ ] data-access roles defined.

The methodology explicitly says the raw DICOM currently contains identifiers and must not be given to students or external compute in that state. 

---

# Phase R2 — De-identification

Implement and validate a DICOM de-identification pipeline.

Check:

* patient name;
* patient ID;
* DOB;
* accession identifiers;
* institution-specific identifiers where required;
* dates according to approved policy;
* private tags;
* burned-in identifiers;
* re-identification key separated.

Preserve research-critical fields such as:

* geometry;
* sequence type;
* acquisition parameters;
* scanner information permitted by policy.

Do not destroy:

* `ImagePositionPatient`;
* `ImageOrientationPatient`;
* `PixelSpacing`.

---

# Phase R3 — Reconcile the local cohort

Create:

```text
rizgary_master_manifest.csv
```

For every candidate case:

```text
case_id
report_exists
sag_t1_exists
sag_t2_exists
ax_t2_exists
dicom_geometry_valid
duplicate
repeat_scan
central_canal_label_available
foraminal_label_available
subarticular_label_available
eligible
exclusion_reason
```

Do **not** assume:

```text
341 → 294 → 299
```

until all numbers have been reconciled.

Chapter 3 explicitly requires the final cohort flow to explain every exclusion. 

---

# Phase R4 — Build local report-derived matrix

One row per:

```text
case × lumbar level
```

Minimum fields:

```text
case_id
level
central_canal
bulge
protrusion
extrusion
foraminal_finding
laterality
root_effect
source_phrase
source_report
verification_status
```

Critical rule:

```text
Not Reported ≠ Normal
```

The methodology explicitly requires NR to remain separate. 

---

# Phase R5 — Source-text audit

Every label used for external evaluation must be manually traced to:

* report phrase;
* lumbar level;
* laterality where relevant.

Do not allow NLP output to become automatic truth.

---

# Phase R6 — Independent radiologist central-canal grading

This is important.

Preferably two readers independently grade:

```text
L1-L2
L2-L3
L3-L4
L4-L5
L5-S1
```

into:

```text
Normal/Mild
Moderate
Severe
```

### Reader protocol

* [ ] shared grading sheet;
* [ ] same definitions;
* [ ] blinded to model result;
* [ ] ideally blinded to original report first;
* [ ] disagreements adjudicated;
* [ ] weighted kappa recorded;
* [ ] exact agreement recorded;
* [ ] one-grade/two-grade disagreements recorded.

The methodology now explicitly calls for this harmonized reader reference as the strongest external ground truth. 

---

# Phase R7 — Freeze the local split

Only after reconciliation and label distribution are known.

Create:

```text
rizgary_test_ids.txt
rizgary_adaptation_pool_ids.txt
```

The test set is untouchable.

Never use it for:

* architecture selection;
* threshold selection;
* calibration;
* PEFT configuration;
* early stopping;
* epoch selection.

---

# MERGE POINT — PUBLIC MODEL + RIZGARY

Only now do the two tracks meet.

# Phase 14 — Freeze the public model

Before opening Rizgary test labels:

record:

```text
model architecture
weights
preprocessing
ROI rules
sequence router
graph
loss
calibration
decision rules
code commit
config file
```

Give it a version:

```text
AMOG_PUBLIC_FROZEN_v1.0
```

No changes after seeing local test results.

---

# Phase 15 — E8 zero-shot Rizgary evaluation

Run the frozen model on the fixed Rizgary test cohort.

No:

* local fine-tuning;
* local calibration;
* threshold change;
* model selection.

### Report

Compare:

[
M_{\text{public}}
\quad \text{vs}\quad
M_{\text{Rizgary}}
]

for:

* macro-F1;
* balanced accuracy;
* Quadratic Weighted Kappa (QWK);
* severe recall;
* calibration.

Also stratify by:

* level;
* severity;
* scanner;
* acquisition;
* missing sequences;
* geometry quality;
* localization success.

---

# Phase 16 — Verified-ROI analysis

On a predefined Rizgary subset:

run model twice:

```text
automated ROI
verified/corrected ROI
```

This separates:

```text
localisation failure
```

from:

```text
grading/domain-shift failure
```

The methodology formally defines this diagnostic control. 

---

# Phase 17 — Few-shot adaptation

Use **only the adaptation pool**.

For:

[
N=10,\ 25,\ 50,\ 100
]

Repeat each (N) several times with different stratified samples.

Compare:

* no adaptation;
* head-only;
* router + head;
* graph + head;
* late-encoder PEFT;
* constrained PEFT;
* full fine-tuning where defensible.

The methodology explicitly treats this as an annotation–performance curve rather than one fine-tuned score. 

Do not keep changing PEFT settings after inspecting the fixed Rizgary test set.

---

# Phase 18 — Final statistical analysis

For every main claim:

### Patient-level bootstrap

Resample whole patients (stratified by target severity class to prevent zero-positive minority resamples), not isolated targets.

### Paired comparisons

Because models see the same patients.

### Repeated seeds

For confirmatory experiments, I would require at least:

```text
3 seeds minimum
```

Preferably 5 for the most important contribution if compute allows.

### Multiple comparisons

Define:

* confirmatory analyses;
* exploratory analyses.

Use FDR where many secondary hypotheses are tested.

### Always report

* effect size;
* confidence interval;
* point estimate.

Avoid:

```text
p < 0.05 = success
```

---

# Phase 19 — Failure analysis

Every final model should have a structured error audit.

For representative cases record:

```text
case ID
ground truth
prediction
probabilities
localisation
available sequences
routing weights
graph messages
uncertainty
error type
```

Error categories:

* wrong localization;
* adjacent-grade error;
* severe↔normal error;
* missing sequence;
* corrupted sequence;
* ambiguous label;
* apparent model error.

Do not cherry-pick attractive Grad-CAM examples.

---

# Phase 20 — Decide what enters the final AMOG-Net

This is crucial.

The final model is **not automatically E8 with every module**.

A module enters the final system only if it:

* improves a prespecified important metric;
* improves robustness;
* improves calibration;
* or provides another reproducible scientifically meaningful benefit.

Possible outcome:

```text
ACSSL helps
router helps
graph does not
```

That is still an excellent PhD result.

Or:

```text
graph helps
ordinal loss does not
```

Also perfectly valid.

The thesis already commits to reporting negative results rather than deleting unsuccessful components. 

---

# The five rules I would print and place beside Selar's desk

1. **Never use Rizgary test data to improve the model.**
2. **Never compare two methods using different data splits.**
3. **Never add a component without an ablation proving what it contributes.**
4. **Never silently correct a failed case or label. Record it.**
5. **Never change the protocol after seeing the result without documenting the change.**

If she follows those five rules plus the gates above, she will avoid most of the mistakes that commonly damage medical-AI PhDs.

The immediate first task should therefore be very concrete:

> **Week 1–2 deliverable: repository + environment + LumbarDISC manifest + patient-level split + leakage tests.**

Then:

> **Week 3–5: DICOM geometry + sagittal/axial alignment + visual QC.**

Then:

> **Week 6 onward: localisation → ROI → E0.**

Only after **E0 is stable and reproducible** should she touch ACSSL, routing or graph modelling.

That is the implementation order I would give Selar as her working roadmap.
