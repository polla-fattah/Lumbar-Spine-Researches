I reviewed the current thesis argument, Chapters 1–5, the live implementation path, the audit/testing code, the statistical machinery, the DICOM/ROI pipeline, the ACSSL/routing/graph/ordinal components, the evidence-folder documents, the recent project-state/submission documents, and the repository history showing how the current implementation replaced the earlier defective one.


One qualification before the detailed review: **I inspected the code and the committed experimental evidence, but I did not independently rerun the 70 GPU training runs or reconstruct the datasets in my environment.** So when I say an experiment produced a result, I mean that the repository's generated artifacts and code provenance support that result; when I identify a code problem, that is from direct source inspection.

My overall conclusion remains:

> **There is a real and defensible PhD here.**
>
> But I would not consider the thesis scientifically “finished” yet. The main danger is no longer that the implementation is fake or fundamentally broken. The danger is now **overclaiming beyond the experiments actually executed**, plus several important statistical and methodological-control issues that can still be corrected before viva.

I would treat the following as the complete remediation plan.

---

# 1. Overall scientific assessment

| Area                           | My assessment now                                        | Viva risk                        |
| ------------------------------ | -------------------------------------------------------- | -------------------------------- |
| Core research question         | **Strong**                                               | Low                              |
| Prospective hypotheses         | **Strong**                                               | Low                              |
| Honesty about negative results | **Very strong**                                          | Low                              |
| Literature review              | **Strong but needs final 2026 refresh**                  | Medium                           |
| Novelty                        | **Defensible, but must be narrowed**                     | Medium                           |
| DICOM geometry                 | **Much stronger now**                                    | Low–Medium                       |
| Grading pipeline               | **Substantially credible**                               | Low                              |
| RQ1 graph evidence             | **Interesting but current interpretation is too strong** | **High**                         |
| RQ2 ACSSL                      | **Incomplete test of the stated RQ**                     | **High**                         |
| RQ3 routing                    | **Mechanism tested partly; robustness RQ incomplete**    | **High**                         |
| RQ4 external transfer          | **Not executed**                                         | **High but defensible**          |
| RQ5 ordinal/cost               | **Positive result, but two mechanisms are confounded**   | **High**                         |
| Statistical inference          | **Needs another serious pass**                           | **High**                         |
| Test-set independence          | **Needs explicit treatment**                             | **High**                         |
| Reproducibility                | **Much improved**                                        | Medium                           |
| Code QA                        | **Good foundations; incomplete conformance coverage**    | Medium                           |
| Clinical claims                | **Generally appropriately cautious**                     | Low                              |
| Thesis/repository consistency  | **Too many stale documents**                             | Medium                           |
| Ethics/governance              | **Placeholders remain**                                  | **High if local data discussed** |
| Viva readiness today           | **Close, not final**                                     | —                                |

The thesis's aim is scientifically well framed. It explicitly says the PhD is trying to **determine whether** anatomical relationships, cross-sequence alignment and target-conditioned evidence improve grading—not prove in advance that they must. It also pre-specifies substantial objectives for label efficiency, corruption robustness, graph controls, external transfer and uncertainty.

That is one of the thesis's greatest strengths.

The problem is that the final experiment does **not execute all those objectives**.

That distinction needs to become the organizing principle of the final remediation.

---

# 2. The thesis's strongest scientific feature

The strongest part is not the +0.0177 QWK.

It is the fact that the project repeatedly discovered that an apparently positive result disappeared when a proper control was introduced.

The repository documents, for example, that:

* the original shuffled graph was structurally weaker than the anatomical graph;
* evidence masking initially leaked through LayerNorm;
* model selection was saved but not restored;
* the patient split originally changed with training seed;
* E4 originally did not actually perform ACSSL;
* E0 originally read the wrong MRI sequence for 59.5% of targets;
* calibration was originally imported but never applied.

Those are serious historical defects, but the current scientific value comes from **finding and correcting them rather than hiding them**.

The viva story should therefore never be:

> “AMOG-Net is a very successful novel architecture.”

It should be closer to:

> **“This thesis subjected several plausible anatomy-aware mechanisms to increasingly destructive controls. Some apparently worked until the appropriate control was introduced. The resulting contribution is a more precise account of which kinds of structure actually improve lumbar grading and which do not.”**

That is a much more mature doctoral contribution.

---

# 3. RQ1: the graph result needs an important correction

This is probably the most important new finding from my code review.

The thesis currently says:

> **“Typing the relations carries information; the anatomical identity of the relations does not.”**

That conclusion is **partly stronger than the current controls justify**.

The live E5 homogeneous graph uses one transformation per graph layer. E6 uses separate transformations for three edge relations, an additional self transform, and—unless using the ungated variant—a learned residual gate.

Therefore:

**E6 versus E5 does not isolate “semantic knowledge carried by edge types.”**

It tests a package containing:

* relation-specific parameterization,
* greater graph-module capacity,
* self projections,
* relation partitioning,
* and possibly gating.

The ungated control isolates the gate reasonably well.

The shuffled-topology control is also valuable. It uses a node permutation that preserves edge count, relation counts, symmetry and the **degree sequence** while destroying correspondence between target identity and graph topology.

That does support:

> **Specific anatomical connectivity does not appear to matter much.**

But E6 > E5 alone does **not yet prove that the meanings “adjacent level,” “same-level condition,” and “bilateral” carry useful information.**

## The experiment I strongly recommend adding

Add an **E6 type-shuffled control**.

Keep the **exact anatomical endpoints** unchanged but randomly permute the `edge_type` labels while preserving the number of each relation type.

Then compare:

**E6 anatomical types vs E6 random type labels.**

This is the missing test.

If anatomical type labels win, you can legitimately say:

> Relation semantics contribute.

If they do not, the correct conclusion becomes:

> Relation-specific parameterization contributes, but the semantic identity assigned to those parameter groups does not.

That would actually make the thesis even more interesting.

### Also add a capacity-matched homogeneous control

Construct a graph with the same approximate number of graph parameters as E6 but no semantically meaningful relation types.

For example, multiple transform banks assigned randomly or learned without anatomical labels.

Then you can distinguish:

**more parameters → relation-specific parameterization → anatomical type semantics → anatomical topology.**

Right now those four ideas are not completely separated.

---

# 4. The shuffled-graph control should be improved further

The current shuffled graph is much better than the historical version.

However, it preserves the **degree sequence globally**, not necessarily the degree of each semantic target.

And because `build_edges(shuffled=True, seed=seed)` receives the **training seed**, each training seed also receives a different shuffled topology.

That means an E6-shuffled seven-seed comparison contains two sources of randomness:

**training stochasticity + topology stochasticity.**

I would change this.

Use one fixed topology-control seed for the principal comparison:

`topology_seed = fixed value`

independent of:

`model_seed`.

Then, as a secondary experiment, test perhaps 5–10 independently rewired graphs.

That gives you two questions:

> Does the anatomical graph beat one pre-specified matched random graph?

and

> Does it beat the distribution of reasonable random graphs?

Even better, implement degree-preserving **double-edge swaps within each relation family**, rather than only global node relabeling.

Then the semantic node degree and relation distribution can be controlled more tightly.

---

# 5. Run the edge-family ablations Chapter 3 already promised

Chapter 3 explicitly says the full graph will be decomposed by:

* removing adjacent-level relations;
* removing same-level cross-condition relations;
* removing bilateral relations;
* retaining only individual families.

These are scientifically valuable and currently much more important than adding another fancy model.

They answer:

> If typed parameterization helps, **which relation family supplies the gain?**

Imagine the result turns out:

* adjacent-level: nothing;
* bilateral: nothing;
* same-level cross-condition: +0.010.

That would radically sharpen the thesis:

> The model benefits from cross-condition co-occurrence within a motion segment, rather than longitudinal spinal adjacency.

That is considerably more informative than “heterogeneous graph helps.”

I would prioritize this very highly.

---

# 6. Run the isolated-lesion contamination experiment

Chapter 3 explicitly anticipated a danger:

> A severe lesion at one level may contaminate a visually normal neighboring level through message passing.

This is an excellent question, but it needs actual evidence.

The graph implementation now correctly masks evidence-free nodes after every layer, which repaired one earlier information-leak pathway.

But that is not the same as demonstrating that **valid severe nodes do not improperly elevate valid neighboring normal nodes**.

Create a subset containing cases where:

L4–L5 = Severe

while L3–L4 and L5–S1 = Normal/Mild.

Then compare E0/E5/E6 prediction shifts at the neighboring levels.

Report something like:

`P(incorrect neighbor upgrade | isolated severe lesion)`

versus baseline.

That would make RQ1 much stronger clinically.

---

# 7. Implement the ordered-level Transformer baseline—or remove the claim that RQ1 answered it

RQ1 explicitly asks whether the heterogeneous graph improves over:

* independent heads;
* an ordered five-level Transformer;
* a homogeneous graph.

The main live ladder contains E0, homogeneous E5 and heterogeneous E6, but not the promised ordered-level Transformer.

Therefore the final thesis cannot presently say:

> RQ1 is fully answered as written.

Either run the ordered-level baseline or state:

> **RQ1 partially answered; ordered-transformer comparison was not executed.**

I recommend running it.

It is likely not enormously expensive and is an important contemporary comparator given the Chai et al. 2026 anatomy-guided inter-level context work. Chai's June 2026 paper already models inter-level contextual dependence, although its outputs remain distinct level-condition predictions. ([Frontiers][1])

That makes the Transformer baseline particularly important now.

---

# 8. Your graph architecture no longer exactly matches Chapter 3's mathematical formulation

Chapter 3 describes node initialization as something like:

`[visual feature || level embedding || condition embedding]`

and then describes relation-aware attention with query/key/value terms.

The live implementation does not do that.

The condition and level embeddings are used inside the **router**, but the graph receives the resulting fused visual vectors directly. `forward_graph()` constructs the condition and level indices for routing, then reshapes the fused vectors into graph nodes.

The live E6 is also an R-GCN-style mean aggregator, not the relation-aware attention equations written in Chapter 3.

Neither implementation is scientifically bad.

The problem is **methodological conformance**.

You have two choices.

Either implement exactly what Chapter 3 describes—or rewrite Chapter 3's architecture subsection to say:

> The initial proposal considered relation-aware attention; after implementation review, the executed model used relation-specific mean aggregation for computational and control simplicity.

Then record that as a protocol deviation.

Do not leave mathematical equations describing a model that did not generate Chapter 4.

---

# 9. RQ2 is not currently answered as written

This is one of the biggest thesis-level issues.

RQ2 asks whether ACSSL improves:

**grading + label efficiency + transfer**

against:

**ImageNet + generic medical pretraining + ordinary augmentation-based SSL.**

The current thesis mainly tests:

**E4 ACSSL vs E3 without ACSSL at 100% labels.**

It then uses missing-sequence reliance and Grad-CAM as additional probes.

Those are useful experiments.

They do **not** answer the full RQ2.

Chapter 4 itself partly acknowledges this, saying label efficiency and external transfer were not separately evaluated.

Therefore change the verdict from:

> “RQ2: No.”

to something like:

> **“RQ2: Partially answered. ACSSL produced no detectable advantage under full-label internal grading or the executed robustness/attribution probes. Label-efficiency and external-transfer components were not executed.”**

Unless you run the missing experiments.

---

# 10. ACSSL currently has a potentially important baseline confound

This one comes directly from the source.

`SequenceEncoder` defaults to:

`pretrained=False`.

The normal supervised ladder initializes its encoders with ImageNet weights by default. `AMOGNet(... pretrained=True)` then trains E3.

But `ACSSLModel` constructs:

`SequenceEncoder(backbone, dim)`

without explicitly enabling ImageNet initialization.

Therefore ACSSL appears to pretrain **randomly initialized encoders**, which are then loaded into E4, while E3 starts from ImageNet.

That means:

> E4 vs E3 may not purely test “ImageNet + anatomical pretraining versus ImageNet.”

It may test:

> **random → ACSSL → supervised**

against

> **ImageNet → supervised**.

That could unfairly disadvantage ACSSL.

### I consider this a major issue.

Run at least:

| Initialization | ACSSL | Supervised grading |
| -------------- | ----- | ------------------ |
| Random         | No    | Yes                |
| Random         | Yes   | Yes                |
| ImageNet       | No    | Yes                |
| ImageNet       | Yes   | Yes                |

The cleanest test of the incremental contribution is:

**ImageNet + ACSSL vs ImageNet only.**

If ACSSL still does nothing, the negative finding becomes much stronger.

---

# 11. Run the ACSSL label-efficiency experiment

Chapter 3 already defines an excellent experiment:

**10%, 25%, 50%, 100% labels.**

This is probably the most likely setting where SSL would help.

A representation-learning method can be useless at 100% labels while being very valuable at 10%.

Therefore the current conclusion:

> “ACSSL does not help.”

may be too broad.

Run perhaps 3 seeds initially for:

* ImageNet;
* ImageNet + ACSSL.

at:

10 / 25 / 50 / 100%.

If you have computational capacity, add:

* random initialization;
* ordinary SSL.

Plot QWK versus fraction of labels.

This one experiment could either rescue a genuine contribution or make the negative result much stronger.

---

# 12. ACSSL should use deterministic validation pairs

The pair dataset randomly selects two available modalities on every access.

That is reasonable during training.

But it also means the validation objective can change which modality pair it evaluates across epochs.

For model selection, I would make validation deterministic.

Either:

* enumerate every valid modality pair; or
* generate a fixed validation pair manifest once.

Otherwise a small change in validation InfoNCE may partly reflect which pairs happened to be sampled.

---

# 13. Implement multi-positive ACSSL or revise Chapter 3

Chapter 3 says that when more than one valid positive exists, the objective may include the **set of positives** rather than choosing one arbitrarily. It also proposes comparing ordinary InfoNCE against an alternative that reduces the false-negative problem.

The current implementation selects one random pair from the available modalities.

Again, two options:

run a multi-positive variant,

or state transparently:

> The executed ACSSL implementation sampled one cross-sequence positive pair per anatomical site.

Do not leave methodology implying a stronger implementation.

---

# 14. Repeat ACSSL pretraining across several seeds

The current project deliberately pretrains ACSSL once and reuses the same representation for all downstream E4 seeds. The reasoning is understandable: otherwise downstream training seed and pretraining seed become confounded.

But the current design also means:

> the uncertainty reported for ACSSL does **not include SSL pretraining stochasticity**.

A strong solution is a nested experiment.

For example:

3 ACSSL pretraining seeds × 3 supervised seeds.

Then estimate variance attributable to:

* representation pretraining;
* downstream optimization.

You do not need 7×7.

Even 3×3 would substantially improve RQ2.

---

# 15. RQ3 is only partially answered

RQ3 asks whether the router remains robust to:

**missing sequences AND quality-degraded sequences.**

The current controlled input ablation is good. It explicitly removes modalities and compares the routed model against E1, correctly discovering that the same condition-specific dependency exists without a router.

That is a good scientific result.

But the **corrupted modality** portion is not really executed.

Chapter 3 promised motion-like corruption, increased noise, bias fields, truncation and slice loss, with measurements of both prediction degradation and changes in gate allocation.

Therefore RQ3 should currently be:

> **Mechanism demonstrated; benefit under missing sequences not demonstrated; quality-degradation robustness not tested.**

Not simply “mechanism yes, benefit no.”

---

# 16. The router's “quality-aware” input is not presently quality-aware

The router has a `quality` input.

But when no quality is supplied, the code substitutes a vector of ones.

The normal model forward path does not pass measured motion, truncation, spacing, SNR or coverage quality values.

So, functionally, the current thesis has:

**image + condition + level routing**

not a demonstrated:

**quality-aware router**.

Change the terminology unless you implement real quality features.

---

# 17. Add the routing baselines Chapter 3 promised

Chapter 3 lists:

1. fixed concatenation,
2. equal averaging,
3. ordinary cross-attention,
4. disease-conditioned routing,
5. routing + modality dropout.

The actual E1 path hardcodes `FixedFusion(mode="mean")`, although the class itself supports concatenation.

There is no main-ladder cross-attention comparison.

Run them.

This is important because an examiner may say:

> “Your router failed to beat a very simple mean. But does it beat a strong learned fusion baseline?”

You need that answer.

---

# 18. RQ5's positive result currently combines two interventions

The E7 rung simultaneously changes:

**categorical → ordinal head**

and

**ordinary objective → asymmetric cost-sensitive objective.**

So the +0.0082 QWK is a joint effect.

The thesis already suspects that the clinical cost matrix may explain more of the improvement than ordinality.

But that has not been isolated.

### Add three variants

E7a:
**ordinal only**, `cost_weight=0`.

E7b:
**categorical softmax + clinical cost term**.

E7c:
**ordinal + clinical cost**, current E7.

Then compare all against E6.

This will tell you whether the gain comes from:

* ordinal representation;
* asymmetric clinical cost;
* their interaction.

This is a **very high-value experiment**.

---

# 19. Rename `OrdinalCORNHead`

Your own audit test correctly notes that the loss is **not CORN**.

It is an independent cumulative binary threshold objective, closer to a CORAL/cumulative-link style formulation.

Yet the class is called:

`OrdinalCORNHead`.

That is unnecessary viva ammunition.

Rename it to something neutral and accurate such as:

`CumulativeOrdinalHead`

or

`OrdinalThresholdHead`.

Then describe the exact binary targets mathematically.

---

# 20. Quantify ordinal monotonicity violations before `cummin`

The head independently predicts:

`P(y>0)` and `P(y>1)`.

These are not constrained during training.

At inference the code applies `torch.cummin` to repair violations.

That is legitimate engineering, but scientifically you should know how often the repair is doing work.

Report:

> percentage of predictions for which `P(y>1) > P(y>0)` before correction.

If almost zero, excellent.

If 10–20%, then the post-processing itself is materially affecting predictions.

Also compare E7 performance with and without monotonic correction.

---

# 21. Perform cost-matrix sensitivity analysis

Current defaults include:

Severe→Normal = 4

Severe→Moderate = 2

Moderate→Normal = 1.5

etc.

Those values are plausible but not clinically derived utilities.

Do not let the viva turn into:

> “Why exactly is missing severe disease four times worse?”

Either obtain radiologist/expert justification or call them **relative training penalties**, not clinical utility values.

Then run sensitivity:

`cost_weight = 0, 0.25, 0.5, 1.0`

and perhaps several `c20/c21` ratios.

If the effect survives reasonable ranges, the finding is much stronger.

---

# 22. Report the opposite severe error explicitly

Chapter 3 correctly says a cost-sensitive objective is acceptable only if it does not simply predict Severe more often.

Current Chapter 4 emphasizes:

**Severe → Normal/Mild**.

Add:

**Normal/Mild → Severe**

and:

**Moderate → Severe**

with patient-clustered uncertainty.

Also report Severe precision alongside Severe recall.

That will show the reduction in under-grading is not bought through indiscriminate over-grading.

---

# 23. RQ5's uncertainty/selective-prediction half is incomplete

RQ5 does not merely ask whether ordinal error improves.

It asks whether:

> calibrated uncertainty can support selective prediction.

The current results show temperature scaling, but no full risk–coverage/abstention experiment.

Chapter 3 promised risk–coverage curves, and also discusses MC dropout, ensembles and conformal analysis.

You do not need to implement all of those.

But to answer the actual RQ5, I would at minimum produce:

**confidence/entropy versus correctness**

and a:

**risk–coverage curve**.

For example:

* retain 100% cases → error X;
* retain 90% most confident → error Y;
* retain 80% → error Z.

Then ask whether Severe errors are preferentially rejected.

Without that, RQ5 should be labelled **partially answered**.

---

# 24. The statistics need a significant revision

This is one of my strongest recommendations.

Your patient-level bootstrap idea is correct.

But the implementation generates bootstrap p-values as:

`2 × min(proportion(diff <= 0), proportion(diff >= 0))`

from the ordinary bootstrap distribution.

That is not the cleanest or most defensible null-hypothesis test.

Use bootstrap for **confidence intervals**.

Use a **paired randomization/permutation test** for significance.

For each patient, swap model A and B's entire set of predictions with probability 0.5, preserving all 25 correlated targets, then recompute ΔQWK.

That creates a proper paired null distribution.

---

# 25. Incorporate training-seed uncertainty into the primary interval

The current across-seed bootstrap holds the seven trained seeds fixed, resamples patients, computes the difference for each seed and averages them.

It separately reports between-seed SD.

That is better than the original single-seed analysis, but the CI itself principally represents **patient-sampling uncertainty conditional on these trained models**.

It does not fully propagate optimization stochasticity.

Use a hierarchical bootstrap:

1. sample training seeds with replacement;
2. sample patients with replacement;
3. use the same sampled patients across the sampled seed pairs;
4. compute mean paired ΔQWK.

Report:

* patient-only interval;
* seed-only distribution;
* hierarchical interval.

With only seven seeds, don't pretend this perfectly estimates the population of training runs, but it is better than excluding that source of uncertainty.

---

# 26. Add a simple exact sign test for the 7/7 results

When all seven paired seed differences have the same sign, this is useful descriptive evidence.

Under a 50/50 sign null, a two-sided exact sign test for 7/7 is:

**p = 0.015625.**

It should not replace the patient-level analysis.

But it answers:

> “Is the result dependent on one lucky training run?”

For E7 vs E0, E6 vs E5 and E7 vs E6, this is a useful complementary statistic.

---

# 27. Do not call the current null intervals “equivalence bounds”

This was in my previous answer and remains important.

Chapter 4 calls them “equivalence bounds” and says, for example, anatomy contributes “at most” 1.05%.

Unless you formally pre-specify a smallest effect of interest and perform an equivalence procedure such as TOST, that terminology is too strong.

Rename the section:

**“Confidence bounds on effects compatible with the data”**

or:

**“Upper compatibility bounds for unsupported effects.”**

If you truly want equivalence testing, define a clinically/scientifically meaningful margin, for example ±0.01 QWK, justify it independently, and perform the appropriate analysis.

But because you have already seen the results, clearly call any new margin **post hoc** unless it existed beforehand.

---

# 28. Tone down the inter-reader “ceiling” argument

This is another issue from my previous answer.

The thesis compares model QWK with literature inter-reader κ around 0.49–0.73.

Those are not necessarily:

* the same kappa statistic;
* the same population;
* the same label process;
* the same adjudication regime.

Your Chapter 5 itself acknowledges the metrics are not directly comparable.

Therefore avoid:

> “The model cannot improve beyond reader reliability.”

and avoid:

> “Effects below 1.5% are below what the reference standard can adjudicate.”

Use:

> **“Known inter-reader variability limits how strongly small model differences should be interpreted against this reference standard.”**

That is scientifically safe.

---

# 29. Do not use the observed-seed power table as proof

The table estimating that one mechanism would need 205 seeds and another 545 is interesting.

But it is based on effect and variance estimates from only seven seeds.

The thesis already partially acknowledges that these are order-of-magnitude estimates.

Make that even clearer.

Do not argue:

> “545 seeds would be required, therefore ACSSL definitely does nothing.”

Say:

> “The observed effect is small relative to the observed between-seed variance; a conventional experiment would require implausibly many runs to establish an effect of this apparent magnitude.”

That's defensible.

---

# 30. The seven-seed extension introduces adaptive-analysis concerns

This is subtle but important.

The project originally ran three seeds.

After seeing two comparisons close to the corrected threshold, the campaign was extended to seven.

The thesis admirably **discloses** this.

But statistically, the number of training runs was increased after examining interim results.

That is not identical to a fixed seven-seed confirmatory experiment.

Therefore don't oversell the final p-values as though seven seeds were entirely pre-specified.

### Strongest solution

Run an additional **locked replication campaign**.

Before running anything:

freeze:

* model definitions;
* comparisons;
* statistics;
* seed numbers;
* no more architecture changes.

Then run, for example:

seeds 49–55

for only the principal configurations.

You do not need another 70 runs.

Perhaps:

E0

E5

E6

E6 type-shuffle

E7 ordinal-only

E7 cost-only

E7 combined.

This would provide a clean replication after the methodology is frozen.

---

# 31. An even stronger solution: create a truly untouched final internal holdout

This is optional but scientifically powerful.

The current “test” partition has been inspected many times during debugging, campaign extension, attribution analysis and model comparison.

It has never been used for gradient training, which is important.

But it has influenced human decisions.

That makes “pristine confirmatory test set” a stronger claim than I would use.

If resources permit, create a new final confirmatory split **before any further model results are examined**.

Because existing train/validation patients have already been used to train prior models, you must retrain new models with that new holdout excluded.

This is costly.

It is not absolutely necessary for the viva if you transparently describe the existing test set as fixed internal evaluation rather than a one-time untouched test.

But a fresh replication would dramatically strengthen the thesis.

---

# 32. Reconcile the FDR family with what Chapter 3 actually specified

Chapter 3 declares a limited set of primary comparison families.

`run_ladder.py` ultimately analyzes more contrasts and applies formal testing to both QWK and macro-F1.

That is not necessarily wrong; indeed, correcting over a larger family can be more conservative.

But the final thesis must explain:

> What exactly constituted the confirmatory family?

I recommend:

**Primary endpoint: QWK.**

Then identify a fixed list of primary contrasts.

Treat macro-F1 and all subgroup comparisons as secondary/supporting.

Also provide a sensitivity table showing both:

* BH-FDR;
* Holm correction.

If conclusions survive both, excellent.

---

# 33. Increase the bootstrap replicates for final results

Chapter 3 says 2,000.

Parts of the runtime default to 1,000.

For final thesis tables, I would use at least:

**10,000 patient-cluster replicates.**

Compute time is trivial compared with model training.

And never report:

`p = 0.000`.

Report:

`p < 0.0001`

according to the resolution of the permutation distribution.

---

# 34. Report CIs for the clinical error improvements

Don't only say:

Severe→Normal 5.7% → 3.8%.

Calculate paired patient-level uncertainty for the difference.

Same for:

* Severe recall;
* distant-error rate;
* Severe precision;
* Normal→Severe.

Those may become more clinically understandable than QWK.

---

# 35. RQ4 is incomplete—but I would not force a bad experiment

The original PhD explicitly includes zero-shot Rizgary transfer and a few-shot adaptation curve.

They were not completed.

That is the largest structural incompleteness.

However, the project subsequently established an important reason why simply running the frozen grader on automatically derived local coordinates would be scientifically misleading: localization error alone produces approximately **−0.1636 QWK / 22.9% degradation**, vastly larger than the architectural differences the thesis is measuring.

Chapter 5 now recognizes that such an external result would confound domain shift with localisation failure.

That is a defensible reason not to manufacture an RQ4 number.

### Change the thesis framing

Don't say:

> “RQ4 failed.”

Say:

> **“RQ4 remains unanswered because the available local cohort lacks target localization adequate for an identifiable grading-domain transfer experiment. A benchmark-side localization perturbation study quantified that confound and demonstrated that it exceeds the effects under study.”**

That's a legitimate limitation.

---

# 36. Add an RQ completion matrix to Chapter 5

I strongly recommend a table like:

| RQ  | Planned evidence                                                   | Executed? | Verdict                                                   |
| --- | ------------------------------------------------------------------ | --------: | --------------------------------------------------------- |
| RQ1 | independent + transformer + homo + hetero + topology controls      |   Partial | Partial                                                   |
| RQ2 | full-label + label-efficiency + pretraining comparators + transfer |   Partial | Internal result negative                                  |
| RQ3 | missing + corruption + learned allocation                          |   Partial | Routing mechanism yes; benefit under missing no           |
| RQ4 | zero-shot + adaptation                                             |        No | Unanswered                                                |
| RQ5 | asymmetric error + calibration + selective prediction              |   Partial | Error objective positive; selective prediction unresolved |

This is much safer than giving every RQ a simple Yes/No.

---

# 37. Complete the ROI reader QC

The repository already has:

60 studies,

300 sheets,

1,474 targets.

The reader adjudication remains outstanding.

This is precisely the sort of relatively small remaining task that is worth completing before viva.

It turns:

> “We generated QC sheets.”

into:

> “An independent reader reviewed the prespecified QC sample and X% met all criteria; Y studies were excluded for geometry failures.”

Chapter 5 currently acknowledges the reader pass is outstanding.

I would close this.

---

# 38. Adjudicate the nine geometry-exclusion candidates

Do not let them remain ambiguous.

Have an appropriate reader determine:

include / exclude / acquisition abnormality / transformation failure.

Then report whether excluding them changes ACSSL.

A sensitivity analysis:

**all studies vs QC-clean studies**

would help tremendously.

If ACSSL stays null after excluding geometry failures, the negative RQ2 result becomes harder to attack.

---

# 39. Reconsider what Grad-CAM actually demonstrates

The attribution analysis is clever, but the current prose occasionally calls the central region an:

**“annotated lesion.”**

The annotation coordinate is not a pixel-accurate lesion segmentation.

It is a target/localization point.

Therefore Grad-CAM mass within a 15-mm disc demonstrates:

> concentration around the **annotated target neighbourhood**.

It does not prove:

> the network localizes the actual pathology.

This distinction matters.

Rename:

“lesion concentration”

to:

**“target-centred attribution concentration.”**

---

# 40. Strengthen the attribution experiment

Add three simple controls:

**Radius sensitivity**:
10 mm / 15 mm / 20 mm.

**Spatial displacement control**:
compare attribution mass in the true target-centred circle with circles shifted by e.g. ±20 mm.

**Center-bias matched control**:
an untrained network helps already, but also compare trained maps against randomly translated target centres.

If trained models strongly prefer the correct coordinate beyond mere image-center bias, your mechanistic claim becomes considerably stronger.

---

# 41. Keep Grad-CAM as supporting evidence, not causal evidence

Chapter 3 actually states this correctly: saliency is a gross sanity check, not proof of reasoning.

Keep that caution in Chapter 5.

Use wording:

> “consistent with the explanation that…”

not:

> “proves the reason is…”

---

# 42. Fix physical slice-neighbour selection in the ROI pipeline

This is a code-level issue.

`decode_roi()` gets neighboring slices through:

`instance_number + off`.

But Chapter 3's whole geometry philosophy is that physical order comes from DICOM geometry rather than filenames or nominal numbering.

`InstanceNumber` is not guaranteed to be continuous physical order.

Build a per-series ordered slice list using:

**ImagePositionPatient projected onto the slice normal.**

Then select previous/next physical slices by ordered index.

This should replace `instance_number ± 1`.

---

# 43. Do not silently fall back to pixel crops when PixelSpacing is missing

Current ROI decoding uses the physical FOV when spacing exists, but if spacing is absent it falls back to a pixel crop.

That means two samples can enter the supposedly 60-mm experiment under different geometry rules.

I would instead:

* flag missing spacing;
* count it;
* exclude it from confirmatory physical-FOV analysis, or have a clearly separate fallback category.

At minimum report exactly how often it occurred.

---

# 44. Report duplicated-neighbor fallbacks

If a neighbouring slice is absent or shape-mismatched, the code duplicates the center slice.

That's preferable to crashing, but a 2.5D input with:

`[center, center, center]`

is different from a real three-slice stack.

Record a per-ROI flag:

* 0 genuine neighbours missing;
* 1 missing;
* 2 missing.

Then assess whether failures are concentrated in a particular condition or severity.

---

# 45. Consider series-level instead of per-slice intensity normalization

The current normalization computes the 1st and 99th percentiles per slice.

That can cause adjacent slices of the same 2.5D stack to be rescaled independently.

This may introduce artificial contrast variation.

Consider:

* one normalization from the entire 3-slice stack;
* or ideally one robust normalization per series/volume.

Then run a small sensitivity comparison.

Not necessarily a fatal issue, but worth improving.

---

# 46. Strengthen the cache provenance

The cache design is good, but it can become safer.

`load_cache()` presently verifies crop dimensions but does not comprehensively verify that:

* FOV;
* radius;
* per-condition setting;
* source index ordering;
* DICOM source;
* split;
* code version

all match what the model expects.

Add to metadata:

* SHA256 of index CSV;
* SHA256 of source coordinate CSV;
* SHA256 of series-description CSV;
* FOV;
* radius;
* normalization version;
* geometry-code commit;
* cache schema version.

Then reject mismatches.

---

# 47. Strengthen cross-sequence geometry for varying orientation

`build_crosssequence_index.py` takes the orientation from the first slice of the destination series and uses that normal for the whole series.

Most ordinary DICOM series should have consistent orientation.

But verify this instead of assuming it.

Calculate maximum within-series IOP deviation.

If above tolerance:

* use each slice's own plane geometry;
* or reject the series as geometrically inconsistent.

---

# 48. Use a physical rather than pixel margin for cross-sequence acceptance

The cross-sequence projector currently uses a fixed margin such as 16 pixels to decide whether a projected point lies safely inside the image.

Pixel dimensions differ across scanners.

A 16-pixel margin therefore represents different physical widths.

Use the intended physical FOV and PixelSpacing to determine whether the crop can be validly extracted.

---

# 49. Audit duplicate target rows explicitly

`build_target_table()` groups by patient/level/condition and takes the first label/first index.

That assumes duplicates are equivalent.

Before collapsing, produce a duplicate audit:

* number of duplicated target keys;
* whether labels disagree;
* whether coordinates differ;
* whether multiple series are involved.

If conflicts exist, resolve them using a deterministic rule.

---

# 50. Clarify the meaning of “LumbarDISC” versus the 1,974-study experimental subset

The official 2026 LumbarDISC release contains **2,697 patients and 8,593 MRI series from eight institutions across six countries and five continents**. ([RSNA Publications Online][2])

Your experiment uses the **1,974 cases/48,657 targets available in the competition training-label portion used by the current pipeline**.

Make this explicit everywhere.

Do not write:

> “LumbarDISC contains 1,974 patients.”

Write:

> “The full LumbarDISC release contains 2,697 patients; the present experiment uses the 1,974 labelled studies available in the development/training subset used for model development.”

This will avoid an examiner thinking the dataset description is factually wrong.

---

# 51. Add a CLAIM-style participant/data flow diagram

Current medical-imaging reporting recommendations strongly emphasize data source, inclusion/exclusion, preprocessing, reference standard, partitioning and reproducibility. CLAIM 2024 also specifically recommends using **“reference standard”** rather than “ground truth,” and favors “internal testing”/“external testing” over the ambiguous word “validation.” ([RSNA Publications Online][3])

Add a flowchart:

2,697 full dataset

↓

1,974 available labelled development studies

↓

DICOM/metadata eligibility

↓

ROI geometry success/failure

↓

1,381 training

296 validation/development

297 internal test

↓

number of scored targets.

Also provide:

* sex;
* age;
* severity;
* sequence availability;
* scanner/site information if available.

TRIPOD+AI similarly recommends transparent reporting of model-development/evaluation data and now contains 27 main reporting items. ([BMJ][4])

---

# 52. Do a final CLAIM 2024 checklist audit

Create:

`CLAIM_2024_COMPLIANCE.md`

with:

CLAIM item | page/section | compliant? | action.

This is a very good pre-viva exercise.

It will expose missing items before an examiner does.

---

# 53. Do the same for TRIPOD+AI where applicable

This is not purely a clinical prediction-model study, so not every TRIPOD+AI item will apply.

But use:

Yes / No / N/A.

This is especially helpful for:

* participant flow;
* intended use;
* evaluation data;
* missing data;
* calibration;
* model availability;
* reproducibility.

---

# 54. Refresh the novelty review immediately before submission

Chapter 1 literally contains a placeholder saying the novelty boundary must be refreshed before submission.

Do it.

Chai et al. 2026 is already extremely close conceptually: anatomy-guided localization, multisequence inputs and inter-level context on LumbarDISC. ([Frontiers][1])

Baur's graph work is different—it represents the 3D disc surface and grades Pfirrmann degeneration, not target relations across the spine. ([PubMed][5])

My current spot-check did **not** surface an identical published heterogeneous graph whose nodes are all 25 level-condition-laterality grading targets.

But do not rely on my spot-check alone.

Run final searches in:

Scopus

PubMed

Web of Science if available

IEEE Xplore

Google Scholar

for 2025–August 2026.

Then add a short table:

prior work | graph/context unit | target | multisequence | laterality | how this thesis differs.

---

# 55. Do not oversell “first”

Prefer:

> “No study identified in the final structured search…”

rather than:

> “This is the first ever…”

unless you can prove it.

---

# 56. The thesis should explicitly separate three kinds of novelty

I would organize originality as:

**Methodological novelty**

Target-level heterogeneous representation and controlled anatomical-prior testing.

**Empirical novelty**

Evidence that relation-specific graph modeling may help while specific anatomical topology does not.

**Scientific/methodological finding**

Several plausible anatomy-aware mechanisms do not produce measurable benefits under strong controls, with evidence for why.

That is more defensible than trying to make every module novel.

---

# 57. Rephrase Contribution D1

“Verified anatomy-aware multi-sequence grading system” may slightly overstate what was verified.

It is verified **internally on the labelled benchmark subset under supplied/geometry-derived localization**.

I'd phrase:

> **A reproducible internally tested multi-sequence grading pipeline under controlled target localization.**

Do not suggest autonomous end-to-end clinical diagnosis.

---

# 58. Rephrase Contribution D2's “capacity-matched” wording

The thesis says every mechanism is tested against a capacity-matched control.

That is not completely true for E6 versus E5 because the heterogeneous graph has additional relation-specific parameterization.

Use:

> **“mechanism-focused controls designed to reduce capacity and topology confounding”**

unless you add the parameter-matched graph control I recommended.

---

# 59. Rephrase D3

Current D3 is conceptually strong.

But use:

> “did not improve grading **under the executed LumbarDISC setting and architecture**”

instead of a broad:

> “anatomical priors do not improve grading.”

You have one dataset family, one backbone family, one ROI representation and one task.

Negative findings should be scoped accordingly.

---

# 60. Remove or soften “the encoder already localizes the lesion”

Use:

> **“The encoder already concentrates evidence around the supplied target coordinate.”**

That's exactly what the current experiment supports.

Then say this **may reduce the marginal value of additional structural priors**.

---

# 61. Be careful with “clinical significance”

The system measures agreement with an imaging reference standard.

It does not measure:

* symptoms;
* surgery;
* outcomes;
* reporting speed;
* radiologist assistance;
* patient benefit.

Chapter 5 already acknowledges this.

Maintain that boundary everywhere.

---

# 62. Finish the ethics placeholders

Chapter 3 still contains institutional fields such as:

* IRB/hospital approval number;
* consent waiver/basis;
* external processing permission.

These cannot remain in a submitted thesis.

Either fill them with verified facts or state explicitly that the local cohort was **not used for any result requiring ethical approval** and remove prospective claims that would imply otherwise, according to the institution's rules.

---

# 63. Verify the public repository has never contained PHI in its Git history

`.gitignore` protecting data today is not enough.

Run history-level checks.

Search all commits for:

* PatientName;
* PatientID;
* BirthDate;
* accession numbers;
* local filenames;
* DICOM;
* report text.

Use a secret/data-history scan.

If any patient data were historically committed, simply deleting the current file is insufficient.

You would need proper history rewriting and incident handling.

---

# 64. Harden local DICOM de-identification before any RQ4 publication

The project has already discovered why `PatientID` alone is unsafe.

The improved tool is much better, but the project state also notes UIDs are not yet remapped and structured-report objects exist.

Before publication/deployment, use a recognized DICOM confidentiality profile/tool and independently audit:

* public/private tags;
* UIDs;
* accession numbers;
* dates;
* structured reports;
* burned-in pixels.

The pixel-based burned-in-text check is useful, but should remain one component of the audit, not the entire de-identification claim.

---

# 65. Fix the live integrity checker versus legacy-code contradiction

This is a repository-engineering issue.

`SUPERSEDED.md` correctly says the old numbered scripts are retained as historical evidence.

But `verify_integrity.py` scans essentially the whole implementation tree—including historical scripts containing deliberately fabricated old results.

Meanwhile the runtime banner says real results are citable only if that checker passes.

Those two ideas conflict.

Create an explicit machine-readable:

`LIVE_PIPELINE_MANIFEST.json`

listing the current citable files.

Make:

`verify_live_pipeline.py`

audit only those.

Keep the historical audit separately.

Then you can truthfully state:

> Live scientific implementation: clean.

> Historical superseded implementation: intentionally preserved and fails legacy-integrity checks.

---

# 66. Move superseded code into a clearly marked legacy directory

Not delete.

Preserve history.

But reorganize:

`implementation/legacy_non_citable/`

with a large README:

> NOT PART OF THESIS RESULTS.

The current `SUPERSEDED.md` is already good evidence, but examiners should not have to infer which of 67 Python files produced Chapter 4.

---

# 67. Update the test report

`component_verification.md` still reports:

**93 passed / 3 failed**

and says augmentation is missing.

But later code and project state say:

**113 tests passing**

and augmentation now exists.

Regenerate it.

Do not let the repository contain an old report that appears to contradict the thesis.

---

# 68. Update `protocol_decisions.md`

It still lists:

> Training augmentation: none implemented.

That is stale; `amog_augment.py` now contains a substantial implementation.

It also calls various experiments open that have since happened.

Update or archive it with:

> superseded on DATE by PROJECT_STATE.md.

---

# 69. Update the Chapter 4 evidence README

It still says:

> “Nothing in this folder is a confirmatory thesis result yet” and “full E0–E7 campaign has not been run.”

That is plainly stale.

Fix immediately.

---

# 70. Update `SUBMISSION_PLAN.md`

It says the thesis has never compiled and compilation is blocked.

Recent repository history says the thesis was later compiled twice to resolve references.

Synchronize it.

---

# 71. Update `viva_defence.md`

The earlier viva narrative still contains three-seed numbers and says the seven-seed campaign is in progress.

Regenerate every number directly from current CSV/JSON outputs.

Never manually copy them.

---

# 72. Fix stale Chapter 4 numbers

I have seen different versions in current thesis material such as:

Severe recall 62.7 → 65.0

versus later seven-seed table values around:

61.1 → 63.1.

This appears to be document synchronization, not a model problem.

But it must be fixed.

Generate **every table and inline number** from the same locked results file.

I would write a script:

`validate_thesis_numbers.py`

that searches expected LaTeX values against the canonical CSV.

If one number differs, CI fails.

---

# 73. Fix malformed prospective/past-tense residue in Chapter 3

There are still awkward passages created during conversion from prospective protocol to executed methodology.

For example, around the training protocol there is wording like:

> “No final hyperparameter value is fabricated in this protocol chapter; each is Every rung…”

That needs human editing.

Read Chapter 3 from beginning to end as prose, not source code.

---

# 74. Remove remaining `[TO CONFIRM]`, `[TO RECORD]` and `[LATER INTEGRATION]` markers

The novelty refresh marker in Chapter 1 still exists.

Ethics placeholders remain.

Before final submission run an automated search for:

`TO CONFIRM`

`TO RECORD`

`LATER INTEGRATION`

`TODO`

`FIXME`

`PLACEHOLDER`

`3-SEED`

`campaign is running`

`not yet run`

and manually resolve every occurrence.

---

# 75. Remove “VIVA-HARDENED” from final source comments

This isn't a scientific problem.

But the repository is public.

A final thesis file carrying comments such as:

`PROTOCOL-GRADE VERSION -- VIVA-HARDENED`

can look as though the document was rhetorically engineered around anticipated examination.

Use neutral source comments.

---

# 76. Document AI assistance explicitly

This is particularly important because the Git history itself records many commits with:

`Co-Authored-By: Claude Opus 5`.

Do **not** attempt to hide this.

Check the awarding institution's current policy and include whatever declaration is required.

I would prepare an AI-assistance statement saying, accurately:

* where AI tools assisted code drafting;
* where they assisted review/testing;
* where they assisted prose;
* who verified outputs;
* that scientific decisions and final responsibility remain with the researchers;
* that all reported numerical results trace to executable artifacts rather than generated prose.

Also ensure Selar can personally explain every central piece of code.

A viva examiner may ask.

---

# 77. Create a Chapter-3-to-code traceability matrix

This was already recommended in the original QA plan and remains one of the best things you can do.

Columns:

| Chapter 3 commitment   | Implemented in  | Test   | Evidence             | Status       |
| ---------------------- | --------------- | ------ | -------------------- | ------------ |
| fixed patient split    | `rsna_data.py`  | test X | split hash           | COMPLETE     |
| ACSSL same-level pair  | `amog_acssl.py` | test X | pretraining JSON     | COMPLETE     |
| ACSSL label efficiency | —               | —      | —                    | NOT EXECUTED |
| corruption routing     | —               | —      | —                    | NOT EXECUTED |
| ordered Transformer    | —               | —      | —                    | NOT EXECUTED |
| type-shuffle           | —               | —      | —                    | RECOMMENDED  |
| external transfer      | —               | —      | localization blocker | NOT EXECUTED |

This table may be the single best defensive artifact for the viva.

---

# 78. Create a proper methodology-deviation log

For every deviation record:

original specification;

executed method;

date changed;

reason;

whether public test results had already been inspected;

effect on interpretation.

This matters because some changes were made after seeing intermediate results.

Transparency is your protection.

---

# 79. Expand run fingerprints

Current `run_config` records stage, backbone, dimension, epochs, mode, augmentation boolean, pretraining, cache name, shuffled/ungated, cost weight and ACSSL presence.

It should also contain:

* LR;
* scheduler;
* warmup;
* batch size;
* modality-drop probability;
* balance-loss weight;
* all augmentation values;
* AMP mode;
* deterministic mode;
* calibration;
* split hash;
* annotation-cache hash;
* cross-sequence-cache hash;
* ACSSL checkpoint hash;
* graph topology seed/hash;
* cost matrix;
* source commit hash;
* dirty repository status.

Then stale-run reuse becomes much safer.

---

# 80. Record exact model/environment dependency lock

Chapter 3 lists Python/PyTorch/CUDA versions.

Add one reproducible environment artifact:

`environment.yml`

or

`requirements-lock.txt`

or container definition.

For the final result, capture:

PyTorch

torchvision

CUDA

cuDNN

NumPy

pandas

pydicom

OpenCV

scipy

scikit-learn.

The TotalSpineSeg work already demonstrated how fragile medical-imaging dependency versions can be.

---

# 81. Run at least one deterministic/full-precision sensitivity experiment

Chapter 3 promises that reduced precision will be checked.

Run one central comparison, perhaps:

E0 and E7

under:

BF16 default

versus FP32/deterministic.

You are not trying to reproduce weights exactly.

You are asking whether the scientific conclusion changes.

---

# 82. Report parameter counts by component, not only model total

This will help defend the graph capacity issue.

For each rung report:

encoder parameters;

fusion/router;

graph;

head;

total.

Then an examiner can see whether +0.0093 QWK came with substantial additional parameterization.

---

# 83. Add computational-efficiency reporting only if accurate

Chapter 3 promises VRAM, training time, etc.

If all runs were on the same RTX 5090 under the same setup, report:

training time per seed;

inference time per study;

parameter count;

peak VRAM.

Do not compare historical runs made under different hardware/software conditions.

---

# 84. Do not count the number of automated tests as scientific proof

“113 tests pass” is useful engineering evidence.

But don't present it as:

> therefore the model is scientifically valid.

Several tests are static source-string checks, while others are genuine behavioral tests.

Describe them appropriately:

> **113 software/conformance checks cover specified implementation properties.**

Then separately present experimental validation.

---

# 85. Convert core tests to pytest and add mutation tests

Some current tests are very good.

Some merely detect that a symbol or text exists in source code.

For each central scientific guarantee, create behavioral tests:

* fixed split;
* ACSSL transfer;
* graph edge use;
* masking;
* calibration fitted on validation;
* cost matrix;
* modality removal;
* cache provenance.

Then deliberately break each property and ensure the test fails.

This was the original QA philosophy and should be completed.

---

# 86. Add a tiny real-DICOM integration fixture

Not patient-identifiable.

Use de-identified/public DICOM from the RSNA dataset, perhaps one or two studies.

CI should be able to run:

DICOM → geometry → ROI → multi-sequence target → model forward → metric.

That bridges the gap between unit tests and the full dataset.

---

# 87. Update the terminology to CLAIM conventions

CLAIM 2024 specifically recommends:

**reference standard**

instead of:

**ground truth**,

and:

**internal testing / external testing**

instead of ambiguous uses of:

**validation**. ([RSNA Publications Online][3])

Your thesis already often uses “reference standard.”

Make it consistent.

---

# 88. Clearly distinguish model validation data from model evaluation data

Currently “validation” means the set used to choose checkpoints.

Good.

Then call the 297-patient set:

**internal test set** or **internal evaluation set**.

Call Rizgary, if eventually used:

**external test set**.

That will prevent terminology confusion.

---

# 89. Add a limitations subsection specifically about annotation-coordinate dependence

This is important.

The model receives a crop centered around reference coordinates.

Therefore the primary thesis is **grading given target localization**, not end-to-end autonomous disease discovery.

Say that prominently.

This is not a weakness if framed correctly.

In fact the −0.1636 localization experiment proves why isolating grading is scientifically necessary.

---

# 90. Do not compare directly with Kaggle leaderboard performance

The evidence-folder README already correctly warns against it.

Maintain that.

Leaderboard models solve a somewhat different end-to-end challenge/evaluation setup.

---

# 91. Consider a second backbone replication

The whole scientific result currently depends heavily on one final backbone setting, apparently ResNet18.

You do not need another full 70-run campaign.

But run key comparisons with one second strong backbone such as:

ResNet50

or ConvNeXt-Tiny.

Maybe 3 seeds:

E0

E6

E7.

If the central pattern survives, you can say:

> not unique to a single encoder.

This would be an excellent strengthening experiment.

---

# 92. Consider a volumetric/through-plane foraminal experiment only as future work

The current finding that foraminal grading behaves differently is interesting.

Chapter 5 hypothesizes that through-plane representation may be the cause.

Do not turn that into another giant pre-viva project.

Keep it clearly as a testable future hypothesis unless you have abundant time.

---

# 93. Keep predictive localization as a separate paper

I agree with the repository's current decision.

Trying to build a new direct detector now risks turning a nearly defensible PhD into an unfinished one.

For the thesis, the localization-failure measurement is enough to justify RQ4's limitation.

---

# 94. If possible, use the new 2026 public foraminal dataset as future external evidence

A 2026 Scientific Data resource has 500 patients with lumbar foraminal stenosis localization/severity annotations. ([GitHub][6])

Its task and sequences are not identical to LumbarDISC, so it is not a drop-in RQ4 replacement.

But it may be useful for future:

* localization;
* foraminal transfer;
* laterality robustness.

Mention it in future work after checking licensing/task compatibility.

---

# 95. Update the abstract to reflect partial RQs

The abstract is currently scientifically attractive, but I would ensure it does not imply that all five planned questions were completed.

Add one concise limitation such as:

> “External institutional transfer was not estimated because the local cohort lacked sufficiently accurate target localization; benchmark-side experiments showed that automatic coordinate derivation would introduce a substantially larger confound than the architectural effects under study.”

That's much stronger than hiding RQ4.

---

# 96. Make Chapter 5 conclusion narrower but stronger

I would aim for something like:

> **Within the LumbarDISC grading setting under controlled target localization, relation-specific graph modeling and a cost-sensitive ordinal objective improved agreement, while explicit anatomical topology, anatomical cross-sequence self-supervision and disease-conditioned routing did not provide reproducible incremental benefits under the executed tests. Target-centred attribution suggests that a strong local encoder already extracts much of the spatial information the anatomical priors were intended to provide. External transport remains unresolved because localization error could not be separated adequately from domain shift.**

That is a very defensible PhD conclusion.

---

# 97. Prepare a “what changed after protocol” viva slide

The examiner may ask:

> “Was all of this planned in advance?”

Do not answer vaguely.

Show:

**Prospectively fixed**

RQ1–RQ5

H1–H6

patient independence

shuffled graph idea

negative result policy.

Then:

**Changed after implementation**

ROI geometry

fixed epoch schedule

specific RGCN implementation

additional controls

seed extension.

Then explain why each changed.

Transparency beats pretending nothing evolved.

---

# 98. Prepare a “failed hypotheses” viva slide

Show:

| Proposed mechanism  | Result                                      | Correct interpretation                     |
| ------------------- | ------------------------------------------- | ------------------------------------------ |
| anatomical topology | unsupported                                 | relation endpoints not beneficial          |
| ACSSL               | unsupported under executed tests            | pretext learned, downstream benefit absent |
| adaptive routing    | gate learns pattern, no incremental benefit | allocation ≠ causal dependence             |
| typed graph         | positive vs homogeneous                     | needs semantic-type control                |
| cost/ordinal output | positive                                    | needs decomposition                        |

This turns a potentially hostile line into the centerpiece of the defence.

---

# 99. Make Selar able to explain five pieces of code at whiteboard level

I would expect a technical examiner to ask how these work:

**DICOM mapping**

pixel → patient coordinates → target series.

**ACSSL**

what exactly is the positive pair and InfoNCE denominator?

**Router**

what makes unavailable modality weight exactly zero?

**RGCN**

how are messages aggregated and what does edge type do?

**Ordinal/cost head**

what are the two logits and how is expected cost calculated?

If Selar cannot explain those without opening the repository, the quality of the code will not save the viva.

---

# 100. Final priority order

If you cannot do everything, I would work in this order:

| Priority  | Work                                                                                               |
| --------- | -------------------------------------------------------------------------------------------------- |
| **P0.1**  | Fix statistical inference: permutation tests + hierarchical seed/patient uncertainty               |
| **P0.2**  | Graph type-shuffle + capacity-matched control                                                      |
| **P0.3**  | Separate ordinal effect from cost-sensitive effect                                                 |
| **P0.4**  | Fix ACSSL ImageNet/random initialization confound                                                  |
| **P0.5**  | Correct RQ1–RQ5 verdicts to partial/full based on executed evidence                                |
| **P0.6**  | Finish independent ROI reader QC                                                                   |
| **P0.7**  | Synchronize every thesis/evidence/status document and number                                       |
| **P0.8**  | Resolve ethics/novelty/placeholders                                                                |
| **P0.9**  | Explicitly disclose adaptive seven-seed extension/test-set reuse                                   |
| **P0.10** | Freeze a final analysis protocol before any more results                                           |
| **P1.1**  | Run ACSSL label-efficiency 10/25/50/100                                                            |
| **P1.2**  | Run routing corruption/quality experiment                                                          |
| **P1.3**  | Add concat + cross-attention fusion baselines                                                      |
| **P1.4**  | Run graph edge-family ablations                                                                    |
| **P1.5**  | Run isolated-lesion contamination stress test                                                      |
| **P1.6**  | Add ordered-level Transformer baseline                                                             |
| **P1.7**  | Run RQ5 risk–coverage/selective prediction                                                         |
| **P1.8**  | Add second-backbone replication                                                                    |
| **P1.9**  | Improve DICOM physical neighboring-slice selection/cache validation                                |
| **P2**    | New localization model, full Rizgary RQ4, PEFT curve, multi-centre transfer, clinical reader study |

---

# My revised viva verdict

After this deeper inspection, I would phrase my assessment slightly differently from before.

**The PhD's intellectual core is defensible now.**

What is **not yet defensible is claiming that the complete prospective methodology in Chapters 1–3 has been executed.** It hasn't. The repository itself proves that several planned experiments remain absent.

That is fixable.

I would **not** try to “save” the thesis by forcing every missing objective into a few weeks of rushed experiments.

Instead:

1. correct the statistical weaknesses;
2. run the handful of controls that materially affect the central positive claims;
3. run the most important missing RQ2/RQ3 experiments if time permits;
4. explicitly downgrade unexecuted portions to **partially answered/unanswered**;
5. make Chapter 3 describe the method that actually produced Chapter 4;
6. synchronize the repository so there is one authoritative scientific state.

If you complete the **P0 group**, I would be reasonably comfortable letting Selar walk into the viva.

If you additionally complete most of **P1**, I think the thesis moves from merely “defensible despite incompleteness” toward a **quite strong methodological PhD**, because its most interesting contribution becomes not a marginal +0.0177 improvement but a controlled experimental dissection of which anatomical assumptions survive rigorous testing.

The two experiments I would personally start with **first** are the **graph edge-type shuffle/capacity control** and the **E7 ordinal-vs-cost decomposition**. They are relatively contained and directly determine whether two of the thesis's strongest positive conclusions are correctly interpreted.

[1]: https://www.frontiersin.org/journals/medicine/articles/10.3389/fmed.2026.1848548/full?utm_source=chatgpt.com "Frontiers | Anatomy-guided context-aware deep learning for lumbar degenerative disease grading and burden-aware risk assessment on MRI"
[2]: https://pubs.rsna.org/doi/10.1148/ryai.250480?utm_source=chatgpt.com "The RSNA Lumbar Degenerative Imaging Spine Classification (LumbarDISC) Dataset | Radiology: Artificial Intelligence"
[3]: https://pubs.rsna.org/doi/10.1148/ryai.240300?utm_source=chatgpt.com "Checklist for Artificial Intelligence in Medical Imaging (CLAIM): 2024 Update | Radiology: Artificial Intelligence"
[4]: https://www.bmj.com/content/385/bmj-2023-078378?utm_source=chatgpt.com "TRIPOD+AI statement: updated guidance for reporting clinical prediction models that use regression or machine learning methods | The BMJ"
[5]: https://pubmed.ncbi.nlm.nih.gov/39266913/?utm_source=chatgpt.com "Automated Three-Dimensional Imaging and Pfirrmann Classification of Intervertebral Disc Using a Graphical Neural Network in Sagittal Magnetic Resonance Imaging of the Lumbar Spine."
[6]: https://github.com/AISSLab2025/LSS-MRI-AISSLab-Dataset?utm_source=chatgpt.com "GitHub - AISSLab2025/LSS-MRI-AISSLab-Dataset: LSS MRI AISSLab: IRB-approved sagittal lumbar spine MRI of 500 patients (8,500 slices) with 3,885 L1–S1 foraminal stenosis boxes. Right/left labels, Normal–Severe (Mild most, Severe rare). Includes expert masks and DICOM/PNG for research. · GitHub"
