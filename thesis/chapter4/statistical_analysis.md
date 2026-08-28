# Statistical analysis, seven-seed campaign

Run 2026-08-27. Script: `implementation/99_audit/chapter4_analysis.py`.
Output: `data/reports/chapter4_effect_sizes.csv`.

The campaign driver produces the ladder table and the pre-specified comparisons.
This adds four things a results chapter needs and those do not supply: effect
sizes, upper compatibility bounds for the nulls, power recomputed at seven seeds, and
the clinical error structure.

## 1. What the seven-seed campaign changed

Three comparisons now survive Benjamini-Hochberg correction, where three seeds
gave one.

| Comparison | 3 seeds | 7 seeds |
| :-- | :-- | :-- |
| Full system vs baseline | +0.0172, p(FDR) < 0.001 | +0.0177, **p(FDR) < 0.001** |
| Typed heterogeneous edges | +0.0123, p(FDR) 0.054 | +0.0093, **p(FDR) 0.009** |
| Ordinal and cost-sensitive head | +0.0099, p(FDR) 0.054 | +0.0082, **p(FDR) 0.009** |
| Anatomical topology vs shuffle | +0.0051, 2/3 seeds | +0.0020, 4/7 seeds |
| Cross-sequence self-supervision | +0.0051, 2/3 seeds | +0.0020, 4/7 seeds |

The additional seeds resolved RQ1 in **both** directions at once. Typed edges
went from "narrowly misses correction" to a demonstrated result on 7/7 seeds
with a third less variance. Anatomical topology, tested against its
degree-preserving shuffle, halved and now wins on barely more than half the
seeds. The two halves of RQ1 separated further apart, not closer.

Two of the three nulls therefore cannot be attributed to insufficient power: the
same four extra seeds that promoted typed edges to significance made the anatomy
comparison weaker.

## 2. Effect sizes

A p-value confounds effect and sample size. Cohen's d on the paired across-seed
differences separates them.

| Comparison | Delta QWK | Cohen's d | Seeds for 80% power |
| :-- | --: | --: | --: |
| Ordinal and cost-sensitive head | +0.0082 | **1.97** | 3 |
| Full system vs baseline | +0.0177 | **1.91** | 3 |
| Typed heterogeneous edges | +0.0093 | **1.06** | 7 |
| Disease-conditioned routing | +0.0053 | 0.39 | 52 |
| Anatomical topology vs shuffle | +0.0020 | 0.20 | 205 |
| Cross-sequence self-supervision | +0.0020 | 0.12 | 545 |
| Gated residual | +0.0014 | 0.07 | 1,615 |
| Modality dropout | -0.0026 | -0.13 | 442 |
| Relational message passing | +0.0002 | 0.01 | 65,489 |

Three effects are large by any convention (d > 0.8) and all three are
significant. Everything else is d < 0.4, and the gap between the two groups is
wide -- there is no comparison sitting awkwardly in between, which is what a
genuinely underpowered study would look like.

**The ordinal head has the largest standardised effect in the study**, larger
than the full-system comparison it is part of, because its between-seed variance
is the smallest of any comparison (0.0042).

Note that the seven-seed power estimates differ from the three-seed ones
reported earlier, because three-seed variance estimates are themselves noisy.
Routing moved from 3,467 seeds to 52, and cross-sequence SSL from 216 to 545.
The ordering is stable; the individual figures should be read as
order-of-magnitude guidance, not precise requirements.

## 3. Upper compatibility bounds: what the nulls actually establish

"p > 0.05" says only that an effect was not detected, which is the weakest form
of a null and invites the reader to assume the study was too small. The paired
interval already bounds the effect. Stating that bound converts "we found
nothing" into "any effect is smaller than X", which is a result.

Each figure below is the far edge of the 95% interval -- the largest effect
still compatible with the data -- against an E0 baseline of 0.7270 QWK.

| Comparison | Upper 95% bound | As % of baseline |
| :-- | --: | --: |
| Gated residual | 0.0064 | **0.89%** |
| Anatomical topology vs shuffle | 0.0076 | **1.05%** |
| Relational message passing | 0.0074 | 1.02% |
| Cross-sequence self-supervision | 0.0089 | 1.22% |
| Modality dropout | 0.0091 | 1.25% |
| Disease-conditioned routing | 0.0112 | 1.55% |

So the claims available are considerably stronger than "not significant":

> Anatomically correct graph topology contributes at most 1.05% of baseline
> performance over a degree-preserving random shuffle.

> Anatomically aligned cross-sequence self-supervision contributes at most 1.22%
> of baseline performance over the same architecture without it.

> Disease-conditioned routing contributes at most 1.55% over fixed fusion.

Set against inter-reader agreement on these grades -- Lurie et al. report kappa
0.49 to 0.73 depending on compartment -- an effect bounded below 1.5% of
baseline is not merely undetectable here; it is below the level at which the
reference standard can meaningfully adjudicate it.

## 4. Clinical error structure

Aggregate agreement hides the errors that matter. Severe-to-Normal confusion is
the clinically consequential direction, and RQ5's objective was selected to
suppress it.

| Rung | Severe recall | Severe -> Normal | Distance >= 2 |
| :-- | --: | --: | --: |
| E0 | 61.1% | 5.7% | 0.526% |
| E1 | 61.1% | 4.9% | 0.500% |
| E2 | 60.7% | 4.7% | 0.414% |
| E3 | 61.4% | 4.6% | 0.420% |
| E4 | 58.8% | 4.0% | 0.453% |
| E5 | 59.0% | 4.1% | 0.389% |
| E6 | 62.9% | 4.1% | 0.375% |
| E6 shuffled | 59.3% | 3.7% | 0.330% |
| E6 ungated | **65.1%** | 4.3% | 0.500% |
| **E7** | 63.1% | **3.8%** | **0.344%** |

**Severe-to-Normal errors fall from 5.7% at E0 to 3.8% at E7, a 33% relative
reduction**, while severe recall rises from 61.1% to 63.1%. Distant errors
(two or more grades) fall by a third, from 0.526% to 0.344%. The system does not
buy aggregate agreement by trading away the errors clinicians care most about --
it improves both.

One honest complication: the ungated variant achieves the highest severe recall
of any configuration (65.1%) while also carrying more distant errors (0.500%
against E7's 0.344%). Higher sensitivity at the cost of more severe misplacement
is the trade the cost matrix was designed to avoid, and E7 makes it in the
intended direction.

## 5. Calibration

The top-level `ece` field records the **uncalibrated** test value. Temperature
scaling is fitted on the validation partition and its test metrics are stored
separately, so reporting only the top-level field would suggest the ladder gets
progressively worse calibrated when the correction the protocol actually applies
reverses that.

| Rung | ECE uncalibrated | ECE calibrated | Temperature |
| :-- | --: | --: | --: |
| E0 | 0.0293 | 0.0130 | 1.161 |
| E1 | 0.0214 | 0.0129 | 1.131 |
| E2 | 0.0428 | 0.0168 | 1.601 |
| E3 | 0.0326 | 0.0145 | 1.200 |
| E4 | 0.0266 | **0.0110** | 1.187 |
| E5 | 0.1024 | 0.0397 | 2.019 |
| E6 | 0.0426 | 0.0209 | 1.422 |
| E7 | 0.0508 | 0.0245 | 1.306 |

Temperature scaling roughly halves ECE at every rung and the fitted temperatures
are all above 1, meaning every configuration is overconfident before correction.

Two observations that should be reported rather than smoothed over. **E5, the
homogeneous graph, is by far the worst calibrated** at 0.1024 uncalibrated and a
fitted temperature of 2.019 -- it is the rung that also fails to improve
accuracy, and its overconfidence is a second symptom. And **the accumulating
ladder does not improve calibration**: E7 at 0.0245 is worse than E0 at 0.0130,
so the gains in agreement come with less reliable probabilities. RQ5 asked
whether calibrated uncertainty could support selective prediction; on this
evidence the calibration half of that question is not answered affirmatively.

## 6. What this adds to the chapter

- Three significant results rather than one, with typed edges and the ordinal
  head both crossing correction at seven seeds.
- Effect sizes that separate cleanly into two groups with nothing in between,
  which is evidence against "underpowered" as a blanket explanation.
- Confidence bounds rather than absences for the nulls: every unsupported
  mechanism is constrained below 1.6% of baseline. These are not equivalence
  bounds -- no smallest effect of interest was pre-specified, so no
  equivalence procedure was run.
- A clinical error result: distant and Severe-to-Normal errors both fall by
  roughly a third from baseline to full system.
- An honest calibration finding that runs against the system: agreement improves
  up the ladder, reliability of the probabilities does not.
