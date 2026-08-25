# Protocol Decisions and the Evidence Behind Them

Decisions taken while making the implementation conform to Chapter 3, each with
the measurement or argument that drove it. Chapter 4 can cite these directly;
several are deviations from Chapter 3 and are marked as such, because a
deviation with a stated reason is defensible and a silent one is not.

Every measurement quoted here is reproducible from the commands in the
accompanying documents.

---

## 1. One frozen patient split, independent of the training seed

**Chapter 3** (`sec:method-patient-split`): *"The split record is
version-controlled as a list of pseudonymous IDs. Data loaders consume those
fixed lists rather than performing a new random split each time the training
script is executed."*

**What the code did.** The split was drawn from the training seed, so a
three-seed campaign drew three different cohorts. Measured over the 1,974-study
index:

| | |
|---|---:|
| Test patients shared by seeds 0 and 1 | 12.8% |
| Held out in all three seeds | 1.7% |
| In some test set while trained on in another | 39.5% of the cohort |

**Why this matters for the results.** "Held out" was true of a single run and
false of the campaign. Chapter 3 `sec:method-stats` pairs model comparisons on
the *same* patients; aggregating across seeds that each saw a different test set
mixes optimisation variance with cohort resampling and inflates every confidence
interval.

**Decision.** The split is drawn once from a constant `SPLIT_SEED`, written to
`implementation/splits/rsna_patient_split.csv`, and consumed as a fixed list.
1,381 train / 296 validation / 297 test, sha256 `4763bf66…`. A subset run
intersects those partitions rather than redrawing them, so a partial run and a
full run stay comparable. A study absent from the file raises an error rather
than being assigned, because silently placing new patients would change the
partitions every prior number was computed on.

---

## 2. A fixed epoch budget, and no early stopping

**Deviation from Chapter 3, deliberate.** `sec:method-optimiser` originally
required early stopping. The chapter has been amended to describe a fixed budget
instead; this section records why.

**Reason.** Early stopping makes the training budget data-dependent. If E6 runs
the full schedule and E5 halts at a third of it, part of the difference between
those rungs is training length rather than architecture — the exact confound the
ladder exists to remove. A truncated run also never completes its cosine
annealing, so rungs would be compared at different points on their schedules.

**What was kept.** Model selection is *not* early stopping and remains: the
best-validation-macro-F1 checkpoint is retained and restored before any held-out
evaluation. A run over 8 epochs trains all 8 and still tests the epoch-3 weights
if epoch 3 scored best.

**Cost, stated rather than hidden.** A configuration that converges early keeps
training. That compute is accepted in exchange for budget parity across the
ladder.

---

## 3. The selected checkpoint is restored before testing

**A defect, not a decision, but it changes how earlier numbers should be read.**

The trainer tracked the best validation macro-F1, saved that checkpoint,
re-read it, asserted it was non-empty — and never applied it. `load_state_dict`
appeared nowhere in the file, so the held-out test ran on whatever the final
epoch left in memory. Model selection was computed, written to disk, and
discarded, while the assertion read like a restore.

Combined with the absence of a learning-rate schedule and early stopping, the
final epoch was the most overfit one, and the final epoch was what got tested.
On a real 12-epoch E0 run, training loss fell 0.706 → 0.005 while validation QWK
plateaued after epoch 2; the best epoch was 11 of 12.

This affected every rung equally, so it did not favour any hypothesis. It added
variance to every comparison and made each number depend on where training
happened to stop.

---

## 4. Warm-up and cosine decay, stepped per epoch

`sec:method-optimiser` requires a schedule; none existed. Cosine decay with a
linear warm-up is now the default.

**Stepped per epoch, not per batch.** The graph rungs E5–E7 process far fewer
batches per epoch than E0–E4. A per-batch schedule would decay them along a
different curve, and every graph comparison would then confound topology with an
optimisation difference.

---

## 5. Calibration fitted on validation, reported both ways

`sec:method-calibration` and training phase 4 require temperature scaling fitted
on validation after model selection. `TemperatureScaler` was imported and never
called: ECE was reported but never corrected.

**Both figures are now reported.** Test ECE appears uncalibrated *and*
calibrated. In rehearsal, E0 improved 0.2925 → 0.2308 and E6 improved
0.1530 → 0.0311, but **E7 got worse**, 0.0515 → 0.0796. Reporting only the
calibrated column would have concealed that.

One implementation note: the ordinal head emits K−1 cumulative logits, so a
categorical cross-entropy fit fails outright. The temperature is fitted through
the head's own probability transform, so one scalar means the same thing for the
ordinal and categorical rungs alike.

---

## 6. The shuffled-edge control is a node relabelling

**Chapter 3** (`sec:method-graph-baselines`): *"Random/shuffled-edge control:
graph capacity retained while anatomical edges are permuted."* This is the
comparison that decides Contribution III.

**What the code did.** It drew fresh random endpoints rather than permuting,
producing a control that was structurally *weaker* than the anatomical graph in
three measurable ways: asymmetric (independent draws almost never yield both
a→b and b→a, while the anatomical graph adds every edge in both directions);
colliding (160 draws produced only 147 distinct typed edges); and lopsided
(degrees ranged 1–16 against a near-regular 5–7).

**Why this mattered.** E6 would have beaten its own control partly because the
control was a worse-formed graph — precisely the conclusion the control exists
to rule out. The defect biased the study's central claim toward its own
hypothesis.

**Decision.** A node relabelling (`perm[edge_index]`). Edge count, per-type
counts, symmetry, degree sequence and uniqueness are all preserved exactly,
while the correspondence between topology and the (level, condition) meaning of
each node is destroyed. It shares only 40 of 140 edges with the anatomical
graph, so it remains a real control.

---

## 7. Evidence masking is enforced after every graph layer

**Chapter 3** (`sec:method-graph`) requires `h_i = 0` where `e_{p,i} = 0`.

The mask was applied once, to the GNN input. Every layer ends in a LayerNorm and
`LayerNorm(0) = β`, not 0, so a node with no image evidence re-acquired a state
at layer 1 and broadcast it onward. Measured on a two-layer RGCN with one masked
node: output norm **2.68** instead of 0, and all six of its graph neighbours
received the phantom signal (max change 0.06–0.16). Non-neighbours were
unaffected, confirming the route was the edges.

This is the information-contagion failure mode `sec:method-isolated-lesion`
exists to detect. An evidence-free level would have inflated its neighbours and
the graph would have been credited for the correlation it manufactured.

Applied identically in the homogeneous and heterogeneous graphs, because E5 is
the control for E6 — masking one and not the other would introduce a difference
unrelated to edge typing.

---

## 8. ACSSL pretraining is a separate stage

`sec:method-positive-pairs` defines the positive relation as
`(p, l, m_a) ~ (p, l, m_b)`. No pretraining loop existed; E4 built the same
modules as E3 plus a projection head that received no gradient.

**Run once, transferred to every seed.** Pretraining inside each E4 run would
make a three-seed campaign three different representations, and the E4-vs-E3
comparison would confound the representation with the seed it came from.

**Refusal rather than silent degradation.** E4 without the pretrained encoders
is E3 under a different name. The trainer now exits with instructions rather
than producing a Contribution I number that measures nothing, and the transfer
raises if it changed no weight, if the backbone differs, or if the feature
dimension differs.

**Verified to learn, not merely to run.** On constructed data where two
"sequences" render the same site with inverted contrast, InfoNCE fell 75% below
chance and top-1 cross-sequence retrieval reached 48.4% against 1.6% chance.

Pretraining uses the development partition only (`sec:method-ssl-leakage`) with a
runtime assertion that no held-out patient is touched, and modality dropout is
off during it (phase 2), since dropping a sequence would delete the positive
pair the loss is defined on.

---

## 9. ROI geometry was measured, not assumed

See `roi_geometry_ablation.md`. Chapter 3 leaves the crop constants open and
requires them to be reported after sensitivity testing; four geometries were
built over the same studies and compared. One of Chapter 3's three stated
positions was adopted, one was not supported by the measurement, and one remains
open because the experiment tested a specific set of numbers rather than the
idea.

---

## What is still open

Recorded here so Chapter 4 does not claim more than was done.

- **Compartment-specific ROIs.** Required by `sec:method-roi`; the values tested
  were defaults, not tuned, so the requirement is neither met nor refuted.
- **Training augmentation.** `sec:method-augmentation` specifies intensity,
  gamma, bias-field, noise, rotation and laterality-aware flips that must swap
  left/right labels *and* graph node identity. None is implemented.
- **Track B.** Zero-shot transfer and few-shot adaptation still evaluate
  placeholder tensors rather than the Rizgary cohort.
- **Competitive baselines, edge-family ablations, the isolated-lesion test,
  corruption-aware routing, uncertainty and selective prediction.** All specified
  in Chapter 3, none implemented.
