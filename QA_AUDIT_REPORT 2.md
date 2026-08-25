# AMOG-Net Implementation Remediation and Verification Plan
## Chapter 3 Methodology Conformance — Developer Action Report

**Project:** Selar PhD — AMOG-Net  
**Purpose:** Convert the current implementation from a promising engineering scaffold into a scientifically defensible implementation of Chapter 3.  
**Status at start of this plan:** **Not approved for thesis-result generation.**  
**Primary specification:** `chapter3(1).tex` / Chapter 3 Methodology  
**Current implementation package reviewed:** `implementation.zip`  
**Prepared:** 2026-08-25

---

## 1. Executive decision

The current implementation should **not be discarded**. It already contains useful and, in several places, well-designed foundations:

- a unified E0–E7 training engine;
- real supervised forward/backward/optimizer paths;
- sequence-specific encoders;
- explicit modality masks;
- modality dropout;
- a disease-conditioned router;
- a 25-node graph schema;
- homogeneous and heterogeneous graph modules;
- shuffled and ungated graph controls;
- an ordinal head;
- cost-sensitive loss utilities;
- calibration, metric, bootstrap, and FDR utilities;
- run provenance and synthetic/smoke support.

However, the current package is **not yet methodologically equivalent to Chapter 3**. Several features are present in source code but are not connected to the runtime path that is supposed to answer the research question. Other stages are currently synthetic placeholders but are labelled as if they were scientific stages.

The remediation objective is therefore:

> **Do not rewrite the whole project. Preserve the useful architecture, but make every scientific claim traceable to an executed runtime path, a Chapter 3 requirement, a reproducible artifact, and a test that would fail if that requirement were broken.**

No E0–E8 number should be treated as a confirmatory thesis result until the **P0 blockers** in this report are closed.

---

# 2. Non-negotiable QA philosophy

The next development cycle must use four rules.

## Rule 1 — Test behavior, not the presence of code

The existence of a class or function is not evidence that the methodology is implemented.

Examples:

```python
self.projector = ACSSLProjector(...)
```

does **not** prove ACSSL is active.

```python
"model_state_dict" in checkpoint
```

does **not** prove the correct trained model was restored.

A method is considered implemented only when the relevant runtime path is executed and produces the expected observable behavior.

---

## Rule 2 — Test the tests

Every high-value scientific test must have an accompanying **negative or mutation test**.

For example:

1. run the correct implementation and confirm the test passes;
2. deliberately break the relevant behavior;
3. confirm the same test fails.

If a test still passes after the behavior is deliberately broken, the test is not valid evidence.

This is particularly important because previous tests have already produced:
- a **false failure**, by treating legitimate multi-relation R-GCN edges as duplicate edges; and
- a **false pass**, by matching an unrelated `to_csv` occurrence rather than proving that the split mechanism was correct.

---

## Rule 3 — Chapter 3 is the specification

Every scientific test should include a comment such as:

```python
# Chapter 3: sec:method-patient-split
```

and should test the actual methodological promise of that section.

The question is not:

> Does the code look internally consistent?

The question is:

> Does the executed code perform the experiment Chapter 3 says will be performed?

---

## Rule 4 — Separate software gates from scientific gates

The project needs two classes of gate.

### Software/CI gate

Means only:

> the program executes, tensors have valid shapes, dependencies load, and the path does not crash.

Acceptable labels:

```text
SMOKE PASS
CI PASS
EXECUTION PASS
```

### Scientific methodology gate

Means:

> real or approved controlled data were used, the Chapter 3 protocol was followed, required artifacts were generated, and the scientific acceptance tests passed.

Acceptable label:

```text
SCIENTIFIC GATE PASS
```

A smoke test must **never** automatically produce a “scientifically certified” report.

---

# 3. Required development workflow before any repair

Before changing code, create an immutable baseline.

## 3.1 Tag the reviewed implementation

Create a source-control tag such as:

```text
pre_remediation_2026-08-25
```

Record:
- Git commit hash;
- Python/PyTorch/CUDA versions;
- current test results;
- current audit report;
- current output/checkpoint directory hashes.

Do not delete the old implementation. The old version is evidence of what was changed and why.

---

## 3.2 Create a methodology deviation log

Add:

```text
docs/METHODOLOGY_DEVIATIONS.md
```

Each deviation must contain:

```text
ID
Date
Chapter 3 section
Original prespecified method
Executed method
Reason
Was the change made before or after viewing held-out results?
Impact on interpretation
Supervisor approval/status
```

A later implementation change must not silently rewrite the protocol.

---

## 3.3 Create a Chapter 3 traceability table

Add:

```text
docs/CHAPTER3_TRACEABILITY.md
```

Minimum columns:

| Chapter 3 requirement | Runtime entry point | Core implementation | Test | Output artifact | Status |
|---|---|---|---|---|---|

No item should be marked `Implemented` merely because a class exists.

Allowed status values should be:

```text
NOT STARTED
SCAFFOLD ONLY
CONNECTED
RUNTIME VERIFIED
SCIENTIFICALLY VERIFIED
```

---

# 4. Priority classification

## P0 — Must be fixed before confirmatory E0–E7 training

1. Freeze one patient split across all experiments and seeds.
2. Make the real DICOM geometry implementation canonical.
3. Establish a defensible localisation path.
4. Replace the active ROI path with Chapter-3-compatible ROI construction.
5. Implement a real ACSSL pretraining path.
6. Fix the public-model freeze procedure.
7. Prevent synthetic Track B code from masquerading as real external validation.

## P1 — Must be fixed before the relevant RQ can be claimed

8. Complete RQ3 quality/corruption routing.
9. Complete graph baselines, edge-family ablations, and evidence masking.
10. Complete E7 calibration and cost-sensitivity protocol.
11. Add training augmentation.
12. Strengthen statistics/repeated-seed pairing.
13. Harden de-identification before local clinical data are used by the research team.

## P2 — Important for final thesis quality but can follow the P0/P1 core

14. Uncertainty/ensembles/risk-coverage.
15. Internal conformal analysis if retained.
16. Efficiency profiling.
17. Full publication/release packaging.
18. Expanded regional or clinical workflow claims — outside current scope unless separately approved.

---

# 5. P0-01 — Freeze the public patient split

## Chapter 3 requirement

All public partitions are patient-level, frozen, and reused across all experiments. Model random seed must affect optimization, not cohort membership.

The same held-out patients must be used for:
- E0 through E7;
- all ablations;
- all random training seeds;
- paired statistical comparisons.

---

## Current defect

In `rsna_data.py`:

```python
def patient_split(index, seed=42, ...):
    ...
    rng.shuffle(patients)
```

and in `amog_train.py`:

```python
tr, va, te = patient_split(tt, seed=args.seed)
```

The same `args.seed` controls both:
- model initialization/training randomness; and
- who belongs to train/validation/test.

Therefore different training seeds produce different held-out cohorts.

This invalidates:
- repeated-seed comparison;
- paired E0–E7 ablations;
- paired bootstrap differences;
- paired AUC tests.

---

## How to demonstrate the problem before fixing it

Add a regression test that intentionally reproduces the current defect:

```python
idx = load_real_or_fixture_target_table()

tr1, va1, te1 = patient_split(idx, seed=42)
tr2, va2, te2 = patient_split(idx, seed=43)

assert te1 == te2
```

This test should **fail on the current code**.

Record the overlap:

```python
overlap = len(te1 & te2) / len(te1 | te2)
```

The exact value is not the criterion. The criterion is that the sets should be identical once the split has been frozen.

---

## Required fix

### A. Generate split files once

Use:

```text
data/splits/train_ids.txt
data/splits/val_ids.txt
data/splits/public_test_ids.txt
```

The split-generation script may use a dedicated, explicitly named:

```text
split_seed
```

but that seed is used **once** to create the files.

### B. Training code loads split files

`amog_train.py` must not call a random split function during a scientific run.

Implement something like:

```python
splits = load_frozen_splits(split_dir)

tr_ids = splits["train"]
va_ids = splits["val"]
te_ids = splits["test"]
```

### C. Separate seeds

Configuration must distinguish:

```yaml
split_version: public_split_v1
split_seed: 20260825
model_seed: 42
```

After `public_split_v1` is frozen, changing `model_seed` must never change patient membership.

### D. Hash the files

Record SHA-256 hashes of all split files in every run result.

---

## Acceptance tests

### Test 1 — same split across model seeds

```python
assert ids_for_run(seed=42).test == ids_for_run(seed=43).test
```

### Test 2 — same split across stages

```python
assert e0_test_ids == e3_test_ids == e4_test_ids == e6_test_ids == e7_test_ids
```

### Test 3 — zero leakage

```python
assert train.isdisjoint(val)
assert train.isdisjoint(test)
assert val.isdisjoint(test)
```

### Test 4 — no target/slice leakage

Every series, slice, level, side, crop, and augmentation from one patient must inherit that patient’s split.

### Mutation test

Temporarily reintroduce:

```python
patient_split(tt, seed=args.seed)
```

The fixed-split test must fail.

---

## Required output artifacts

```text
data/splits/public_split_v1/train_ids.txt
data/splits/public_split_v1/val_ids.txt
data/splits/public_split_v1/public_test_ids.txt
data/splits/public_split_v1/split_manifest.json
reports/public_split_v1_audit.md
```

The manifest should include:
- patient counts;
- target counts;
- severity counts;
- generation date;
- split seed;
- file hashes.

---

# 6. P0-02 — Make real DICOM patient-space geometry canonical

## Chapter 3 requirement

Cross-sequence correspondence must be based on DICOM patient-space geometry using at least:

- `SeriesInstanceUID`;
- `ImagePositionPatient`;
- `ImageOrientationPatient`;
- `PixelSpacing`;
- physical slice normal;
- physical slice ordering;
- sagittal-to-axial correspondence;
- laterality preservation.

Filename order must not define physical slice order.

---

## Current defect

The project contains two geometry paths:

### Better path

```text
03_dicom_geometry/build_series_geometry.py
03_dicom_geometry/build_crosssequence_index.py
geometry.py
```

These move toward reading actual DICOM geometry.

### Obsolete/dangerous path

```text
03_dicom_geometry/dicom_geometry_parser.py
```

This older path guesses textbook sagittal/axial geometry and inserts fallback/default values.

The master pipeline still invokes the obsolete path.

This creates a serious risk:

> the scientific pipeline may report DICOM alignment while actually using guessed geometry.

---

## Required fix

1. Declare one canonical geometry module.
2. Remove the old guessed-orientation parser from scientific execution.
3. If the old parser is retained, move it to:

```text
legacy/
```

or rename it:

```text
synthetic_geometry_smoke.py
```

4. `run_full_amog_pipeline.py` must call only the canonical real-DICOM geometry path.
5. Missing mandatory geometry should produce a QC failure, not a plausible default coordinate.

---

## Real sample integration test

Use the uploaded sample case archive:

```text
case.3.zip
```

as a **local integration fixture**, subject to privacy handling. Do not commit identifying raw DICOM to a public repository.

For the sample:

1. extract all DICOM files to a controlled working directory;
2. group by `SeriesInstanceUID`;
3. classify candidate sagittal T1, sagittal T2/STIR, axial T2;
4. read actual `ImageOrientationPatient`;
5. read actual `ImagePositionPatient`;
6. compute slice normal;
7. order slices by projection onto the normal;
8. verify spacing continuity;
9. reconstruct patient coordinates;
10. map a sagittal level/point to plausible axial slices;
11. render an overlay/montage for manual inspection;
12. verify left/right orientation.

---

## Acceptance tests

### Test — physical ordering beats filename ordering

Create a fixture whose filenames are deliberately shuffled. The resulting slice order must remain unchanged.

### Test — transform round-trip is not enough

Do not accept only:

```text
voxel -> patient -> voxel
```

because the same wrong transform can round-trip perfectly.

The test must compare against known DICOM tags or manually verified geometry.

### Test — missing geometry fails visibly

Delete `ImageOrientationPatient` from a test DICOM.

Expected behavior:

```text
QC_FAIL_GEOMETRY
```

not a hard-coded canonical orientation.

### Test — laterality survives reorientation

A known left-sided point must remain anatomically left after tensor reorientation.

### Mutation test

Force the old parser into the pipeline. The canonical-path test must fail.

---

## Required artifacts

```text
data/manifests/series_geometry_v1.parquet
data/derived/crosssequence_index_v1.parquet
reports/dicom_geometry_qc.md
reports/dicom_geometry_failures.csv
reports/sample_case_geometry_overlay/
```

---

# 7. P0-03 — Replace synthetic localisation with a defensible localisation strategy

## Chapter 3 requirement

Localisation is enabling technology, not novelty.

The primary end-to-end pipeline should use:
- an established localiser/segmenter; or
- another validated anatomical parser.

The study must report:
- localisation error in mm where reference points exist;
- PCK or equivalent;
- mask metrics where available;
- complete failure rate;
- low-confidence/failure flags.

---

## Current defect

`04_localization/spider_locator.py` generates synthetic/fixed coordinates and fixed high confidence values. It does not represent execution of a real SPIDER model.

Therefore phrases such as:

```text
SPIDER localisation
100% localisation coverage
```

are not scientifically valid when produced by this script.

---

## Two acceptable implementation strategies

### Strategy A — Oracle-coordinate grading control for early public experiments

For controlled LumbarDISC grading experiments, use benchmark-provided coordinate annotations as a clearly labelled:

```text
ORACLE / ANNOTATION-BASED ROI CONTROL
```

This is scientifically useful because it isolates the grading contribution from localisation failure.

It must **not** be called an automated localiser.

### Strategy B — Real automated localiser

Implement/reproduce a genuine established localiser, for example a SPIDER-pretrained segmentation/localisation model where licensing permits.

This is required before:
- fully automated end-to-end claims;
- local external automated pipeline claims;
- localisation-controlled domain-shift decomposition.

---

## How to detect synthetic localisation automatically

Add a test:

1. provide two substantially different MRI studies;
2. run the localisation stage;
3. inspect whether the output is suspiciously identical and independent of image content.

Also verify that model weights are actually loaded and used.

A test that checks only that five coordinates exist is inadequate.

---

## Required status vocabulary

Use:

```text
PASS
LOW_CONFIDENCE
WRONG_LEVEL
NO_LEVEL_FOUND
INSUFFICIENT_COVERAGE
GEOMETRY_FAILURE
```

Do not silently repair the primary automated result.

---

## Acceptance criteria

For oracle-control mode:
- mode is explicitly labelled `oracle_coordinate`;
- no automated-localisation claim is made.

For real-localiser mode:
- actual model/checkpoint path is recorded;
- output depends on image input;
- error metrics are computed on a validation subset with known locations;
- failures remain in the audit record.

---

# 8. P0-04 — Rebuild the active ROI path to match Chapter 3

## Chapter 3 requirement

The methodology specifies:
- anatomically localised ROIs;
- physical dimensions where possible;
- disease/compartment-specific evidence;
- side-aware foraminal ROIs;
- 2.5D stacks;
- five slices (`r=2`) as the initial reference configuration;
- sensitivity testing may select another radius;
- consistent ROI inputs across matched model comparisons.

---

## Current defect

The unified data path in `rsna_data.py` currently uses:

```python
CROP = 128
```

and:

```python
for off in (-1, 0, 1):
```

which produces:
- a fixed 128 × 128 pixel crop;
- a 3-slice stack.

The same basic crop path is used across different target types.

This does not yet implement the methodology’s:
- physical-mm ROI definition;
- five-slice reference;
- condition-specific crop logic;
- side-aware foraminal crop logic.

---

## Required fix

Create a single canonical ROI specification object, for example:

```yaml
roi_version: roi_v2
central_canal:
  sag_t2_fov_mm: [W, H]
  ax_t2_fov_mm: [W, H]
  stack_radius: 2

foraminal:
  sag_t1_fov_mm: [W, H]
  side_aware: true
  parasagittal_offset_mm: ...
  stack_radius: 2

subarticular:
  ax_t2_fov_mm: [W, H]
  sag_context: true
  stack_radius: 2
```

Exact values should be selected from the development cohort and then frozen.

---

## Important methodological point

A final radius other than 2 is acceptable **only if** the Chapter 3 sensitivity experiment is actually performed and the chosen value is recorded prospectively from development/validation evidence.

Do not simply change Chapter 3 after seeing held-out test results.

---

## Required tests

### Physical-FOV test

Two scans with different `PixelSpacing` should produce crops representing approximately the same physical width.

### Five-slice reference test

For the initial reference configuration:

```python
assert stack.shape[0] == 5
```

### Laterality test

A left foraminal target must not use the right-side crop.

### Compartment test

Central canal, foraminal, and subarticular ROI builders must not all resolve to the same crop definition.

### Boundary test

At the edge of a volume:
- missing neighboring slices must be handled explicitly;
- duplicated center slices, if used, must be logged;
- the data loader must not silently cross into a different series.

### Mutation test

Replace physical FOV with `128px`. The physical-FOV test must fail on scans with different pixel spacing.

---

## Required QC artifact

Generate a montage from a predefined validation subset showing:

```text
study ID
level
condition
side
sequence
target point
crop boundary
selected 2.5D slices
geometry status
```

Manual review must be documented.

---

# 9. P0-05 — Make E0 scientifically reproducible before adding novelty

## Chapter 3 requirement

E0 is the mandatory independent ROI classifier. It must use:
- the same frozen patient split;
- the same canonical ROI definition;
- no graph;
- no routing;
- no ACSSL;
- no cross-target communication.

A stable backbone is then selected for the main ablation ladder.

---

## Required work

Before moving to E1:

1. complete P0-01 through P0-04;
2. train E0 on real public data;
3. repeat with at least the minimum prespecified seeds;
4. verify that all seeds use identical train/validation/test IDs;
5. store patient-target predictions;
6. report confidence intervals using patient-clustered resampling;
7. record hardware/runtime/config.

---

## Required E0 output

```text
runs/E0/<run_id>/
    config.yaml
    split_manifest.json
    environment.json
    best_checkpoint.pt
    predictions_val.csv
    predictions_test.csv
    metrics_val.json
    metrics_test.json
    train_log.csv
    git_commit.txt
```

`predictions_test.csv` should contain at minimum:

```text
patient_id
target_id
level
condition
side
truth
p_normal_mild
p_moderate
p_severe
predicted_class
```

This format is important later for paired analysis.

---

# 10. P1-01 — Add the competitive baselines required by Chapter 3

The internal E0–E7 ladder alone is not enough.

Implement matched baselines with:
- the same patient split;
- same ROI inputs;
- same backbone where feasible;
- similar optimization budget.

Required comparisons:

1. independent ROI classifier;
2. fixed concatenation;
3. equal averaging;
4. strong sagittal–axial cross-attention / M-SCAN-like comparator;
5. ordered five-level Transformer context baseline;
6. homogeneous graph;
7. typed heterogeneous graph.

Do not claim superiority over a published point estimate obtained on another split.

---

# 11. P0-06 — Implement real ACSSL pretraining for E4

## Chapter 3 requirement

RQ2 is not:

> Does an ACSSL class exist?

It is:

> Does DICOM-defined anatomical cross-sequence self-supervision improve representation, label efficiency, and transfer?

The primary positive pair is:

```text
same patient
same lumbar level
different MRI sequence
```

Adjacent levels are **not** the primary positive pair and may only be explored as a separate ablation.

---

## Current defect

The current project contains:
- `ACSSLProjector`;
- `info_nce`;
- `ACSSLFramework`.

However the E4 training runner launches:

```text
amog_train.py --stage E4
```

and the supervised E4 forward path does not use the projector or `info_nce`.

Therefore the projector can be dead while the E4 stage still runs and reports a result.

---

## Required new training sequence

### Phase 1 — Build ACSSL pair index

Create a development-only pairing table:

```text
patient_id
level
sequence_a
sequence_b
roi_a
roi_b
geometry_quality
pair_valid
```

Conditions:
- same patient;
- same level;
- different sequence;
- valid geometry;
- no public test patients;
- no Rizgary test patients.

### Phase 2 — Self-supervised pretraining

Train sequence encoders + projection heads using the anatomical pair objective.

Save:

```text
ACSSL_encoder_pretrained_<version>.pt
```

### Phase 3 — Transfer encoder weights into E4

Instantiate the downstream E4 grading model and explicitly load the pretrained encoder weights.

The transfer operation must be logged.

### Phase 4 — Supervised grading

Fine-tune the model under the same supervised conditions as the matched baseline.

---

## Runtime proof required

### Gradient test

During ACSSL pretraining:

```python
loss.backward()

assert any(p.grad is not None and p.grad.abs().sum() > 0
           for p in projector.parameters())
```

Also verify encoder gradients.

### Call-path test

Monkeypatch `info_nce` to raise:

```python
def bomb(*args, **kwargs):
    raise RuntimeError("ACSSL CALLED")
```

A real ACSSL pretraining step must hit the patched function and raise.

This is a much stronger test than searching source text.

### Weight-change test

Hash encoder weights before and after ACSSL pretraining.

They must change.

### Checkpoint-transfer test

After loading the ACSSL checkpoint into E4, compare a known encoder parameter or full state hash to the pretrained checkpoint.

### Leakage test

Assert:

```text
ACSSL_pretraining_patients ∩ public_test_patients = ∅
```

---

## Label-efficiency experiment

Implement 10%, 25%, 50%, and 100% labelled development fractions.

Use predefined patient-level subsets, not a fresh random sample for every method.

Compare:
- random initialization;
- ImageNet;
- generic medical pretraining where available;
- ordinary image SSL;
- anatomical cross-sequence SSL.

---

## Sequence-information preservation test

After ACSSL, run single-sequence probes.

At minimum:
- sagittal T1 probe;
- sagittal T2/STIR probe;
- axial T2 probe.

The purpose is to detect whether cross-sequence alignment erased sequence-specific diagnostic information.

---

## Documentation correction

The current ACSSL README language that implies an anatomical-distance weighting between neighboring levels must be reconciled with Chapter 3.

The **primary** Chapter 3 ACSSL positive is:

```text
same patient + same level + different sequence
```

If anatomical distance between different levels is tested, it must be labelled a secondary/adjacent-level ablation rather than the main contribution.

---

# 12. P1-02 — Complete RQ3: quality-aware and corruption-aware routing

## Already useful

The current router correctly supports:
- explicit availability mask;
- zero weight for unavailable modalities;
- renormalization over surviving modalities;
- target/level conditioning;
- modality dropout.

Preserve these.

---

## Missing methodological requirements

Chapter 3 also requires present-but-corrupted sequence handling.

A modality can exist but be unreliable. Missingness and corruption are distinct.

The implementation must add:

```text
q_{p,m}
```

a quality representation or pre-specified quality indicators.

Possible inputs:
- motion score;
- truncation/coverage flag;
- spacing irregularity;
- slice loss;
- unusual resolution;
- geometry quality;
- other pre-specified non-label QC features.

---

## Required corruption suite

Apply one sequence at a time:

- noise increase;
- bias-field/intensity distortion;
- controlled contrast change;
- motion-like corruption;
- resolution degradation;
- slice loss;
- partial truncation.

Do not manufacture new disease anatomy.

---

## Required comparisons

1. fixed concatenation;
2. equal averaging;
3. ordinary cross-attention;
4. disease-conditioned routing;
5. routing + modality dropout;
6. quality-aware routing without corruption training;
7. quality-aware routing with corruption training.

---

## Runtime tests

### Quality vector reaches the gate

Change only `q_{p,m}` while image features remain fixed.

Confirm router logits/weights can change.

### Missing vs corrupted distinction

- missing modality -> availability weight must be exactly zero;
- corrupted modality -> modality remains available but quality may cause its learned weight to decrease.

### Corruption intervention

For a controlled input:

```text
clean axial T2 weight = g_clean
corrupted axial T2 weight = g_corrupt
```

The thesis does not hard-code that `g_corrupt` must always be lower; that is an empirical result.

But the implementation must be capable of responding to the quality evidence.

### Mutation test

Remove quality from the router concatenation. The quality-path test must fail.

---

# 13. P1-03 — Complete graph methodology and evidence masking

## Already useful

Preserve:
- 25 target nodes;
- adjacent-level relation;
- same-level cross-condition relation;
- bilateral relation;
- homogeneous graph;
- typed graph;
- shuffled graph;
- ungated graph;
- gated residual graph.

---

## A. Correct evidence masking

### Current risk

The current graph path does:

```python
nodes = nodes * evidence.unsqueeze(-1)
h = self.gnn(nodes, edge_index, edge_type)
```

Zeroing the initial feature is not equivalent to masking messages from unsupported nodes throughout a multi-layer graph.

With biases/self-updates, a zeroed node can become non-zero and later participate in message passing.

### Required fix

Implement per-patient message/edge masking so that:

```text
evidence_mask(node_j) = 0
```

means messages from `node_j` are excluded from the neighbor softmax/message aggregation.

Do not confuse:
- missing label; and
- missing image evidence.

A node without a local ground-truth label may still have valid image evidence and remain in the forward graph.

---

## B. Add ordered level Transformer baseline

Chapter 3 requires a generic inter-level context comparator.

This is essential for the novelty boundary:

> Is the typed heterogeneous graph better than generic level-context attention?

---

## C. Add edge-family ablations

Required:
- remove adjacent-level edges;
- remove same-level cross-condition edges;
- remove bilateral edges;
- retain only adjacency;
- retain only same-level cross-condition;
- retain only bilateral.

---

## D. Add graph perturbation controls

Required/valuable:
- shuffled relation endpoints;
- shuffled relation types;
- random edge deletion;
- random rewiring with matched edge count.

The control must preserve the characteristics needed for a fair comparison.

For R-GCN-style graphs, duplicate identity is:

```text
(source, destination, relation_type)
```

not merely `(source, destination)`.

---

## E. Add isolated-lesion contamination test

Find held-out cases such as:

```text
L4-L5 Severe
L3-L4 Normal/Mild
```

for the same target type.

Compare:
- independent head;
- homogeneous graph;
- ungated heterogeneous graph;
- gated heterogeneous graph.

Report:
- adjacent-level false-positive rate;
- change in Severe probability at the normal neighbor;
- fraction of correct local predictions converted to an incorrect higher grade.

---

## Evidence-mask acceptance test

Construct two inference paths:

1. graph with unsupported node physically disconnected from message passing;
2. graph with the implementation’s evidence mask.

Outputs for supported nodes should agree within tolerance.

### Mutation test

Replace message masking with only initial feature zeroing. The test must fail under a graph with non-zero biases/multiple layers.

---

# 14. P1-04 — Complete E7: ordinal, clinical cost, and calibration

## A. Cross-entropy remains mandatory

Every ordinal/cost configuration must be compared against standard categorical cross-entropy under matched features.

---

## B. Do not hard-code one clinical cost matrix as truth

The current implementation has useful cost-loss mechanics, but Chapter 3 does not authorize arbitrary constants as clinical truth.

Create a small pre-specified family, for example:

```yaml
cost_profiles:
  benchmark_like: ...
  mild_asymmetry: ...
  moderate_asymmetry: ...
  strong_asymmetry: ...
```

The specific values must be justified or explicitly treated as sensitivity analysis.

Record:

```text
C matrix
lambda_cost
selection rule
```

---

## C. Report both under-grading and over-grading

Minimum severe-class reporting:

- Severe sensitivity;
- Severe specificity;
- Severe PPV;
- fraction of all targets predicted Severe;
- Severe -> Normal/Mild;
- Severe -> Moderate;
- Normal/Mild -> Severe;
- macro-F1;
- balanced accuracy;
- quadratic weighted kappa;
- calibration.

A cost-sensitive model cannot be called better merely because it predicts Severe more often.

---

## D. Actually apply temperature scaling

### Current gap

A `TemperatureScaler` utility exists, but E7 must:
1. collect validation logits;
2. fit `T` on validation only;
3. freeze `T`;
4. apply the same `T` to held-out test logits;
5. store `T` in the final checkpoint/package.

### Runtime test

Fit a non-trivial temperature on deliberately overconfident validation logits.

Then verify that the test-evaluation path uses:

```python
calibrated_logits = logits / T
```

### Mutation test

Monkeypatch calibration application to return raw logits. The test must fail by checking a known difference in probabilities or NLL.

---

## E. QWK interpretation

Use quadratic weighted kappa for **ordinal distance**.

Do not use QWK as the measure of directional clinical asymmetry.

Directional asymmetry belongs to:
- the cost matrix;
- Severe -> Normal/Mild;
- Normal/Mild -> Severe;
- severe FP/FN trade-off.

---

## F. Uncertainty/selective prediction

These can follow after the core E7 comparison.

If retained:
- MC dropout or small ensemble;
- predictive entropy;
- risk-coverage;
- internal conformal analysis as secondary.

Do not let this block E0–E7 core implementation.

---

# 15. P1-05 — Add MRI-safe training augmentation

The main real-data training path needs controlled augmentation.

Candidate transformations:
- modest intensity scaling;
- gamma/contrast;
- bias-field simulation;
- noise;
- small translations;
- small rotations;
- limited elastic deformation where anatomically plausible.

Avoid transformations that manufacture or destroy canal/foraminal pathology.

---

## Laterality rule

If a horizontal flip changes anatomical left/right:

```text
left foraminal target <-> right foraminal target
left subarticular target <-> right subarticular target
```

Graph node identity must be swapped consistently.

### Property test

Build a synthetic fixture with an obvious left marker.

After flipping:
- image marker must appear on the right;
- label side must change;
- target/node ID must change accordingly.

### Mutation test

Flip the image without swapping labels. The laterality test must fail.

---

# 16. P1-06 — Strengthen statistics and prediction provenance

## Patient-clustered bootstrap

Bootstrap patients, not individual targets.

On each replicate:
- sample patient IDs with replacement;
- include all targets belonging to that patient together.

---

## Paired comparison requirement

Before any paired test:

```python
assert model_A.patient_target_keys == model_B.patient_target_keys
```

The key should include at minimum:

```text
patient_id
target_id
```

Do not pair two arrays merely because they have equal length.

---

## Repeated seeds

Use:
- same data split;
- different model seeds.

Report:
- mean and variability across model seeds;
- patient-level uncertainty separately.

---

## Bootstrap count

Before final confirmatory analysis, pre-specify a stable count such as 2,000–5,000 replicates, subject to compute.

Do not change the number because a preferred confidence interval looks better.

---

# 17. P0-07 — Fix the final public-model freeze stage

## Chapter 3 requirement

The zero-shot model is the **selected trained public model**, frozen before any Rizgary test label is used.

---

## Current critical defect

`12_freeze/freeze_amog_model.py` constructs a new model and saves its state immediately.

A checkpoint containing:

```text
model_state_dict
```

is therefore not sufficient evidence.

---

## Required freeze workflow

### Step 1 — select model on public validation evidence

Selection must use only public development/validation data.

Record:

```text
selected_run_id
selected_checkpoint
selection_metric
selection_value
model_seed
architecture
```

### Step 2 — load the selected checkpoint

```python
model = build_model(config)
ckpt = torch.load(selected_checkpoint)
model.load_state_dict(ckpt["model_state_dict"])
```

### Step 3 — restore calibration

If temperature scaling is selected:

```python
T = ckpt_or_calibration_artifact["temperature"]
```

### Step 4 — package all scientific dependencies

Frozen release should contain or reference:

```text
model weights
architecture/config
backbone
ROI version
geometry version
preprocessing version
split version
calibration temperature
graph topology version
software versions
Git commit
checkpoint checksum
```

### Step 5 — make the package immutable

Create:

```text
AMOG_PUBLIC_FROZEN_v1.0/
```

with a manifest and SHA-256 checksums.

---

## Behavioral checkpoint-restore test

This is mandatory.

```text
trained selected model
        |
        v
prediction A on fixed fixture
        |
        v
save/freeze
        |
        v
destroy/reinitialize object
        |
        v
load frozen artifact
        |
        v
prediction B on same fixture
```

Require:

```python
assert_allclose(A, B, atol=...)
```

This proves actual weight restoration.

### Mutation test

Replace the loaded state with a newly initialized state.

The restore test must fail.

---

## Freeze refusal rules

The freeze script must refuse to run if:
- source run is `smoke`;
- checkpoint is missing;
- split hash is missing;
- config is missing;
- validation-selection evidence is missing;
- calibration is required but absent.

---

# 18. P0-08 — Quarantine synthetic Track B code

## Current problem

Current Track B contains scripts that create fictional cohort rows, fixed scanner metadata, zero features/targets, and dummy adaptation operations.

These are useful only as software fixtures.

They must not produce artifacts labelled as:
- clinical transfer;
- zero-shot performance;
- Rizgary result;
- few-shot adaptation result.

---

## Required restructuring

Move or rename synthetic paths:

```text
13_track_b/smoke/...
```

or:

```text
ingest_rizgary_cohort_smoke.py
evaluate_zero_shot_smoke.py
adaptation_smoke.py
```

All smoke outputs must contain:

```text
NON-CITABLE SYNTHETIC OUTPUT
```

in both machine-readable and human-readable reports.

---

## Scientific-mode guard

Real Track B scripts must require explicit real inputs:

```text
--rizgary-manifest
--reference-matrix
--fixed-test-ids
--adaptation-pool-ids
--frozen-public-model
```

If any are absent, the real scientific mode must fail.

No automatic fallback to synthetic patients is allowed.

---

# 19. P1-07 — Build the real Rizgary data track

This begins only after the relevant approvals and de-identification requirements are satisfied.

## Required cohort manifest

Create one reconciled row per candidate study with fields such as:

```text
pseudonymous_case_id
report_exists
sag_t1_exists
sag_t1_usable
sag_t2_exists
sag_t2_usable
ax_t2_exists
ax_t2_usable
dicom_geometry_valid
duplicate
repeat_scan
central_canal_reference_available
foraminal_reference_available
subarticular_reference_available
eligible
exclusion_reason
```

Do not invent reasons for the numerical transition between raw archive, candidate matches, and final cohort.

---

## Reference matrix

One row per:

```text
case x lumbar level
```

Keep:

```text
NOT_REPORTED
```

separate from:

```text
NORMAL
```

Do not infer a normal finding merely because a narrative report did not mention it.

---

## Preferred central-canal reference standard

For the strongest RQ4 analysis:
- two qualified readers independently grade;
- same three-class definition;
- five lumbar levels;
- blinded to model predictions;
- adjudication for disagreements;
- report exact agreement and weighted kappa.

If full dual reading is infeasible, use the prespecified resource-limited fallback in Chapter 3.

---

# 20. P1-08 — Freeze the Rizgary test set before zero-shot evaluation

After cohort reconciliation and reference-standard construction:

```text
rizgary_test_ids.txt
rizgary_adaptation_pool_ids.txt
```

The split is frozen **before** public model performance is inspected on Rizgary.

The fixed test set must never be used for:
- architecture selection;
- threshold selection;
- temperature fitting;
- PEFT-rank selection;
- epoch selection;
- module-placement selection;
- local harmonization parameter fitting.

---

## Acceptance test

Hash the local test file and write that hash into every zero-shot and adaptation result.

Every adaptation size must evaluate on exactly the same fixed local test IDs.

---

# 21. P1-09 — Implement true zero-shot Rizgary evaluation

## Required behavior

Load:

```text
AMOG_PUBLIC_FROZEN_v1.0
```

Then process real de-identified Rizgary DICOM using the **same frozen preprocessing/geometry/ROI/localisation rules**.

No local:
- fine-tuning;
- calibration;
- threshold optimization;
- model selection.

Primary target scope:
- five central-canal targets.

---

## Required outputs

Report public-held-out vs Rizgary external performance on the **same central-canal task**.

At minimum:
- macro-F1;
- balanced accuracy;
- QWK;
- severe recall;
- severe precision;
- calibration;
- absolute performance drop;
- relative performance drop.

Stratify where sample size supports:
- level;
- severity;
- scanner/vendor;
- field strength;
- slice thickness/resolution;
- sequence availability;
- geometry quality;
- localisation success;
- reference-standard type.

---

# 22. P1-10 — Implement verified-ROI external control

On a predefined subset:

```text
automated ROI
vs
qualified verified/corrected ROI
```

Use the exact same frozen grading model.

Report:

```text
Delta_M_loc = M_verifiedROI - M_autoROI
```

This is a diagnostic control, not a replacement for the fully automated headline result.

The subset must be selected before model-result inspection.

---

# 23. P1-11 — Implement few-shot adaptation exactly as prespecified

Use adaptation sizes:

```text
N = 10, 25, 50, 100
```

subject to the final eligible local cohort.

Each N must be sampled multiple times, preferably stratified by central-canal severity where feasible.

Compare:

1. no adaptation;
2. simple/non-learned harmonization if defensible;
3. head-only;
4. router + head;
5. graph + head;
6. late-encoder PEFT + head;
7. constrained multi-module PEFT;
8. full fine-tuning where defensible.

All adapted models are evaluated on the same fixed Rizgary test set.

---

## Required anti-overfit safeguards

- PEFT rank/adapter size selected before final few-shot experiment;
- learning-rate range fixed;
- epoch budget fixed;
- stopping rule fixed;
- fixed local test never touched for selection;
- several independent adaptation draws per N;
- variance reported.

---

# 24. P1-12 — Harden DICOM de-identification before local research use

## Current useful foundation

The de-identification script already:
- replaces patient ID/name;
- deletes some direct PHI tags;
- creates pseudonymous IDs;
- produces an audit artifact.

Preserve the useful structure.

---

## Current problems requiring correction

### A. Hard-coded salt

Current source includes a fixed salt string.

Move the secret to a protected environment/secret store.

Do not commit it.

### B. Linkage/re-identification mapping location

The mapping is currently stored under the project data tree.

The mapping must be stored in a separately controlled hospital/governance location not accessible to the ordinary model-training repository.

### C. Private tags

Implement:
- removal; or
- explicit allowlist/audit policy.

### D. UIDs

Define a consistent UID-remapping policy where required while preserving internal referential integrity.

### E. Dates

Apply the institutionally approved date policy:
- remove;
- or consistently shift;
- or retain only approved temporal information.

Do not choose silently.

### F. Burned-in identifiers

Add a burned-in-annotation/pixel-content review step where applicable.

### G. Simulation audit language

The no-input branch must not output:

```text
100% erased
compliance certified
```

as though real DICOM had been inspected.

Rename this result:

```text
DEIDENTIFICATION_SMOKE_TEST
```

---

## Privacy acceptance criteria

Before Selar receives the local research copy:

- direct identifiers removed according to approved policy;
- pseudonymous IDs validated;
- private tags handled;
- UID policy documented;
- date policy documented;
- burned-in review performed where applicable;
- linkage file stored separately;
- raw identifiable DICOM not present in ordinary research workspace;
- hospital/ethics/compute permissions recorded.

This technical QA is **not a legal or institutional certification**. Formal approval remains an institutional responsibility.

---

# 25. P1-13 — Rewrite the master pipeline’s success semantics

## Current risk

`run_full_amog_pipeline.py` currently treats successful script execution as a full pipeline success and prints hard-coded cohort/release statements.

This is unsafe for a research project.

---

## Required change

The master pipeline should produce two independent summaries.

### Software status

```text
software_execution_status:
    environment: PASS
    geometry_smoke: PASS
    model_smoke: PASS
```

### Scientific status

```text
scientific_status:
    public_split_frozen: PASS/FAIL
    real_geometry_verified: PASS/FAIL
    roi_qc: PASS/FAIL
    e0_real_training: PASS/FAIL
    acssl_runtime_verified: PASS/FAIL
    ...
```

Scientific status must be derived from actual gate artifacts.

---

## Remove hard-coded cohort counts

Do not print:

```text
1,975 patients
351 cases
...
```

unless the value is read from the corresponding frozen manifest.

Every count should include:
- manifest version;
- timestamp;
- hash.

---

## Refuse misleading combinations

Examples:

- smoke E4 + real E5 -> refuse scientific ladder;
- synthetic Rizgary + real public model -> refuse zero-shot label;
- random frozen model + real external data -> refuse external evaluation.

---

# 26. Test-suite redesign: how to attack the tests themselves

This is a dedicated workstream.

## 26.1 Classify tests

Every test should be one of:

```text
UNIT
INTEGRATION
METHODOLOGY
MUTATION/NEGATIVE
REAL-DATA QC
```

A unit test must not be treated as a methodology certification.

---

## 26.2 Avoid source-text presence tests for behavior

Weak pattern:

```python
assert "info_nce(" in source
```

Better:

```python
monkeypatch info_nce
run one E4 pretraining step
assert patched function was called
```

Weak pattern:

```python
assert "to_csv" in split_source
```

Better:

```python
run split generation
verify exact output IDs
rerun scientific training with different model seed
verify same split IDs were loaded
```

---

## 26.3 Required mutation tests

At minimum deliberately break each of these and confirm the corresponding methodology test fails:

1. make split depend on model seed;
2. allow one patient into train and test;
3. sort DICOM by filename;
4. replace real orientation with a hard-coded axial/sagittal orientation;
5. make all ROI crops fixed pixels;
6. reduce 5-slice stack to 3 without changing config;
7. disconnect ACSSL loss;
8. detach the ACSSL projector;
9. fail to load ACSSL pretrained encoder;
10. ignore quality vector in routing;
11. let unavailable modality receive non-zero weight;
12. make shuffled graph identical to anatomical graph;
13. ignore edge types;
14. disable graph evidence-edge masking;
15. disable the graph gate while claiming gated mode;
16. skip temperature scaling;
17. fit calibration on test labels;
18. freeze a random model instead of trained checkpoint;
19. use a different Rizgary test split for each adaptation N;
20. use Rizgary test data for PEFT selection;
21. bootstrap targets instead of patients;
22. flip image left/right without swapping laterality labels.

A methodology test suite that cannot detect these mutations is incomplete.

---

# 27. Real sample DICOM QA plan

The uploaded sample DICOM archive should be used as a **controlled local integration check**, not as a benchmark result.

## Required tests on the sample

### Series inventory

Report:
- number of DICOM files;
- number of series;
- candidate sequence types;
- slice counts;
- geometry completeness.

Do not expose patient identifiers in the QA report.

### Header geometry

For each series:
- orientation;
- origin range;
- pixel spacing;
- through-plane spacing;
- normal vector;
- ordering consistency.

### Sequence classification

Verify that the implementation correctly identifies:
- sagittal T1;
- sagittal T2;
- axial T2.

### Cross-plane correspondence

Select one lumbar level/target position and render:
- sagittal target;
- corresponding axial candidate slices;
- physical distance;
- angular compatibility.

### Laterality

Verify one left/right reference visually and numerically.

### ROI

Render:
- central-canal ROI;
- left foraminal ROI;
- right foraminal ROI;
- subarticular ROI if defined.

Confirm they are not all the same generic crop.

---

## Important privacy rule

If the sample case contains identifiers, do not:
- commit it;
- upload it to public CI;
- include raw DICOM tags containing PHI in reports.

Create a de-identified derivative fixture if institutional policy allows.

---

# 28. Documentation corrections required

Code and documentation must describe the same experiment.

## Required corrections

### ACSSL README

Align the description with Chapter 3:
- primary positives = same patient, same level, different sequence;
- adjacent-level relationship = optional ablation only.

### Track B README

Replace `prospective` with `retrospective`.

### Localisation README

Do not describe synthetic fixed-coordinate code as a real SPIDER model.

### Freeze README

Do not say “certified and released” unless the trained selected checkpoint is behaviorally restored and verified.

### Pipeline README

Clearly distinguish:
- smoke mode;
- scientific real-data mode.

---

# 29. Recommended repository organization after remediation

```text
implementation/
├── configs/
│   ├── data/
│   ├── roi/
│   ├── experiments/
│   └── adaptation/
│
├── data_contracts/
│   ├── public_manifest_schema.md
│   ├── target_schema.md
│   ├── split_schema.md
│   └── rizgary_reference_schema.md
│
├── src/
│   ├── dicom/
│   ├── localisation/
│   ├── roi/
│   ├── encoders/
│   ├── ssl/
│   ├── routing/
│   ├── graph/
│   ├── losses/
│   ├── calibration/
│   ├── evaluation/
│   └── statistics/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── methodology/
│   ├── mutation/
│   └── fixtures/
│
├── scripts/
│   ├── public/
│   ├── external/
│   └── smoke/
│
├── docs/
│   ├── CHAPTER3_TRACEABILITY.md
│   ├── METHODOLOGY_DEVIATIONS.md
│   └── SCIENTIFIC_GATE_STATUS.md
│
└── reports/
```

A major rewrite is not required to reach this layout. Existing modules can be moved gradually.

---

# 30. Minimum experiment configuration contract

Every scientific run should save a machine-readable config such as:

```yaml
experiment_id: E6_seed42
mode: scientific

data:
  dataset: LumbarDISC
  manifest_version: lumbardisc_manifest_v2
  split_version: public_split_v1
  split_hash: ...
  roi_version: roi_v2
  geometry_version: geometry_v2

model:
  backbone: resnet18
  encoder_sharing: separate
  routing: quality_aware
  modality_dropout: true
  graph: heterogeneous
  graph_gate: true
  graph_topology_version: graph_v1
  ordinal_head: false

training:
  model_seed: 42
  epochs: ...
  optimizer: AdamW
  learning_rate: ...
  scheduler: cosine
  precision: bf16

selection:
  metric: macro_f1
  checkpoint_rule: best_validation

provenance:
  git_commit: ...
  environment_hash: ...
```

The exact values may differ. The requirement is that the scientific run can be reconstructed.

---

# 31. Required scientific gate checklist

## Gate A — Data foundation

- [ ] one frozen patient split;
- [ ] zero leakage;
- [ ] split hashes archived;
- [ ] target schema verified;
- [ ] severity distribution reported.

## Gate B — Geometry/localisation/ROI

- [ ] real DICOM geometry path only;
- [ ] sample/validation geometry manually checked;
- [ ] localisation mode explicitly oracle or real automated;
- [ ] ROI uses frozen physical/condition-aware specification;
- [ ] laterality verified.

## Gate C — E0

- [ ] reproducible real-data training;
- [ ] fixed split;
- [ ] several model seeds;
- [ ] patient-target predictions saved;
- [ ] confidence intervals valid.

## Gate D — Routing

- [ ] fixed-fusion controls;
- [ ] cross-attention comparator;
- [ ] availability mask;
- [ ] modality dropout;
- [ ] quality vector;
- [ ] corrupted-modality experiment;
- [ ] routing-weight diagnostics.

## Gate E — ACSSL

- [ ] actual pretraining loop;
- [ ] projector gradients;
- [ ] encoder gradients;
- [ ] test patients excluded;
- [ ] pretrained weights loaded into downstream model;
- [ ] 10/25/50/100% label-efficiency;
- [ ] sequence-preservation probes.

## Gate F — Graph

- [ ] ordered Transformer comparator;
- [ ] homogeneous graph;
- [ ] typed graph;
- [ ] shuffled graph;
- [ ] gated and ungated;
- [ ] evidence-message masking;
- [ ] edge-family ablations;
- [ ] isolated-lesion contamination test.

## Gate G — E7

- [ ] CE comparator;
- [ ] ordinal comparator;
- [ ] cost-sensitivity family;
- [ ] severe FP/FN trade-off;
- [ ] validation-only calibration;
- [ ] calibration applied to held-out test;
- [ ] uncertainty only if retained.

## Gate H — Public freeze

- [ ] selected trained checkpoint loaded;
- [ ] behavioral restore test;
- [ ] full config package;
- [ ] split/calibration/preprocessing versions;
- [ ] checksums;
- [ ] no Rizgary test labels viewed.

## Gate I — Rizgary external

- [ ] approvals/permissions recorded;
- [ ] de-identified controlled research copy;
- [ ] cohort reconciled;
- [ ] reference matrix verified;
- [ ] preferred reader regrading or documented fallback;
- [ ] fixed test/adaptation split;
- [ ] zero-shot result before adaptation.

## Gate J — Few-shot adaptation

- [ ] N=10/25/50/100;
- [ ] repeated draws;
- [ ] same fixed test;
- [ ] module-wise controls;
- [ ] no test-set tuning;
- [ ] recovery curves + uncertainty.

---

# 32. Suggested developer ticket order

## Sprint 1 — Scientific data foundation

### T1
**Frozen split loader**
- owner: data/training
- priority: P0
- definition of done: all E0–E7 seeds/stages load identical test IDs.

### T2
**Canonical DICOM geometry**
- owner: imaging
- priority: P0
- definition of done: old guessed parser removed from scientific runner; sample-case geometry QC passes.

### T3
**Localisation mode separation**
- owner: imaging
- priority: P0
- definition of done: oracle-control vs real-auto localization are explicit; synthetic locator cannot produce scientific pass.

### T4
**ROI v2**
- owner: imaging
- priority: P0
- definition of done: physical, condition-aware, side-aware ROI + QC montage.

---

## Sprint 2 — Reliable public baseline

### T5
**E0 fixed-split reproducibility**
- priority: P0
- definition of done: stable real E0 + repeated seeds + patient-level predictions.

### T6
**Competitive fusion/context baselines**
- priority: P1
- definition of done: concatenation, mean, cross-attention, ordered level Transformer.

---

## Sprint 3 — Contribution runtime proof

### T7
**ACSSL pretraining**
- priority: P0
- definition of done: real pair loader, real SSL training, gradient proof, checkpoint transfer, label fractions.

### T8
**Routing quality/corruption**
- priority: P1
- definition of done: q-vector connected + corruption matrix + diagnostics.

### T9
**Graph controls**
- priority: P1
- definition of done: evidence masking, edge-family ablations, isolated-lesion test.

---

## Sprint 4 — Output methodology

### T10
**Ordinal/cost/calibration**
- priority: P1
- definition of done: CE-vs-ordinal, cost sensitivity, fitted temperature in runtime.

### T11
**Augmentation**
- priority: P1
- definition of done: MRI-safe transforms + laterality property tests.

### T12
**Statistics**
- priority: P1
- definition of done: patient-paired comparison and fixed-split repeated-seed analysis.

---

## Sprint 5 — Freeze and external track

### T13
**Correct public freeze**
- priority: P0
- definition of done: trained checkpoint restore identity verified behaviorally.

### T14
**Track B quarantine/rebuild**
- priority: P0
- definition of done: synthetic scripts cannot create scientific results.

### T15
**Rizgary manifest/reference/split**
- priority: P1
- definition of done: real deidentified cohort, verified reference, frozen local test/adaptation split.

### T16
**True zero-shot**
- priority: P1
- definition of done: frozen public model evaluated without local tuning.

### T17
**Few-shot adaptation**
- priority: P1
- definition of done: repeated N=10/25/50/100 curves with module-wise comparisons.

---

# 33. What must not be done while repairing

Do **not**:

- use the public held-out test set to choose ROI size;
- use Rizgary test labels to choose architecture;
- change test membership with model seed;
- call synthetic localization “SPIDER performance”;
- call a stored random model “frozen trained model”;
- call dummy zero-feature output “zero-shot result”;
- call smoke execution “scientific certification”;
- change Chapter 3 to fit a bug after seeing results;
- silently replace a failed component with another and keep the same experiment ID;
- remove a negative result because it weakens AMOG-Net;
- invent clinical cost values and present them as validated clinical utility;
- treat `NR` as `Normal`;
- report local subarticular/foraminal transfer unless a valid local reference exists;
- move raw identifiable DICOM into student or external/cloud compute without approved governance.

---

# 34. Final definition of “ready for thesis results”

The implementation may begin producing **citable confirmatory Chapter 4 results** only when all of the following are true:

1. scientific runs use a frozen patient split;
2. real DICOM geometry is canonical;
3. localisation mode is scientifically honest and validated;
4. ROI construction matches the frozen Chapter 3 protocol;
5. E0 is reproducible;
6. competitive baselines exist;
7. E4 actually performs ACSSL pretraining and transfers its weights;
8. routing handles both missing and corrupted modalities;
9. graph controls can distinguish anatomical topology from added capacity;
10. calibration is actually fitted/applied if claimed;
11. cost sensitivity is a pre-specified sensitivity experiment;
12. tests include adversarial/mutation checks;
13. the final freeze restores the trained selected public checkpoint exactly;
14. synthetic Track B paths are physically separated from scientific Track B;
15. real Rizgary evaluation uses a reconciled, de-identified, fixed external cohort and valid reference standard;
16. zero-shot happens before local adaptation;
17. few-shot uses a separate adaptation pool;
18. all model comparisons retain patient-level pairing and provenance.

Until then, outputs should be labelled:

> **development / smoke / engineering validation only — not a thesis result.**

---

# 35. Recommended immediate next actions

The development team should begin with exactly these four tasks:

1. **Fix the split architecture.**
2. **Switch the master path to real DICOM geometry.**
3. **Make localisation/ROI scientifically valid and auditable.**
4. **Replace E4 with a true ACSSL pretraining + checkpoint-transfer workflow.**

After those four are complete, rerun the entire test suite **and the mutation tests**, then perform a new independent QA review before starting the large E0–E7 experiment campaign.

The public model freeze and Rizgary work should not be treated as meaningful until that second QA pass approves the public pipeline.

---

# 36. Required evidence package for the next QA handoff

When returning the implementation for review, include:

```text
1. updated implementation source
2. chapter3(1).tex unchanged or a documented deviation log
3. test-suite output
4. mutation-test output
5. frozen public split files + hashes
6. sample DICOM geometry QC report and overlays
7. ROI QC montage
8. E0 real-data run artifacts from at least two model seeds
9. ACSSL gradient/call-path evidence
10. ACSSL pretrained checkpoint + transfer log
11. routing missing/corruption test report
12. graph control/edge-ablation report
13. E7 calibration runtime report
14. freeze behavioral-restore report
15. current known-open list
16. updated CHAPTER3_TRACEABILITY.md
17. updated METHODOLOGY_DEVIATIONS.md
```

This will allow the next reviewer to spend time finding **new** problems instead of rediscovering known ones.

---

## Final QA instruction to the development team

The aim is not to obtain a green test suite at any cost.

The aim is:

> **For every statement Chapter 3 makes about what the experiment will do, make the runtime do exactly that; make the code save evidence that it did it; and make at least one test fail when that behavior is deliberately removed.**

That standard is what will make the implementation defensible at PhD examination rather than merely functional software.
