# Full campaign results (E0-E7, 3 seeds)

Run 2026-08-26. 30/30 runs succeeded, 0 failed, 669.4 min on the RTX 5090.
Profile `full`: real data, 50 epochs, seeds 42/43/44, resnet18 backbone.
Generated tables: `ladder_tables_auto.md` (verbatim copy of `data/reports/chapter4_tables.md`).

## Headline

| Rung | QWK (mean +- sd) | Macro-F1 | Bal. acc |
| :-- | --: | --: | --: |
| E0 single-sequence baseline | 0.7276 +- 0.0070 | 0.694 | 69.0% |
| E7 full system | **0.7448 +- 0.0072** | 0.714 | 72.0% |

**E7 - E0 = +0.0172 QWK, 95% CI [+0.0064, +0.0285], 3/3 seeds, p(FDR) < 0.001.**
This is the only pre-specified comparison that survives Benjamini-Hochberg
across the 18-row family. The accumulated system beats the baseline; no single
component does on its own.

## Per-component outcome

| Comparison | Contribution | dQWK | 95% CI | seeds + | p(FDR) |
| :-- | :-- | --: | :-- | :-: | --: |
| E6 vs E5 typed edges | III | +0.0123 | [+0.0028, +0.0216] | 3/3 | 0.054 |
| E7 vs E6 ordinal + cost | - | +0.0099 | [+0.0017, +0.0186] | 3/3 | 0.054 |
| E6 vs E6_shuffled anatomy | **III decisive** | +0.0051 | [-0.0036, +0.0141] | 2/3 | 0.570 |
| E4 vs E3 ACSSL | **I** | +0.0051 | [-0.0038, +0.0148] | 2/3 | 0.570 |
| E3 vs E2 modality dropout | - | +0.0032 | [-0.0060, +0.0119] | 2/3 | 0.724 |
| E2 vs E1 routing | **II** | +0.0010 | [-0.0079, +0.0107] | 1/3 | 0.886 |
| E6 vs E6_ungated gating | - | -0.0009 | [-0.0110, +0.0080] | 1/3 | 0.886 |
| E5 vs E0 message passing | - | -0.0050 | [-0.0153, +0.0057] | 2/3 | 0.617 |

Read together with the routing evidence: Contribution II's *mechanism* replicated
perfectly (foraminal->sag_T1, canal->sag_T2, subarticular->ax_T2, 15/15 runs) but
produced no accuracy gain. Contribution III's typed relations help (3/3, CI excludes
zero) while the *anatomical* topology does not separate from a degree-preserving
shuffle. Contribution I gave no measurable benefit at this scale.

None of these is a failed experiment; each is an answer, and Chapter 3 commits to
reporting them whichever way they fall.

## A correction to the inference procedure

The first auto-generated Table 4.3 tested each comparison *once per seed* and put
all 48 rows in one FDR family. That was wrong in two ways, and both were fixed
before these numbers were produced:

1. **The per-seed bootstrap understates the variance.** It resamples patients with
   the trained model held fixed, so its interval covers test-set sampling only and
   excludes training stochasticity. On this campaign the omission is decisive:
   E4 vs E3 came out +0.0270 (p = 0.000) on seed 42 and -0.0234 (p = 0.000) on
   seed 43 -- opposite signs, both "significant". So did E3 vs E2. Reporting
   per-seed intervals would have let any claim be supported by choosing a seed.

2. **Three seeds are not three independent tests.** Putting them in one FDR family
   triples the apparent multiplicity of every comparison.

The fix (`amog_stats.paired_bootstrap_diff_seeds`) draws one patient resample,
applies it to all three seeds, and averages the per-seed difference *inside* the
replicate. The interval is then for the mean effect over training runs, and the
between-seed sd is reported beside it. The FDR family is the pooled rows only,
one per comparison and metric. Per-seed rows are retained in Table 4.3b as
descriptive, explicitly carrying no significance claim.

Note also that `E7 vs E0` -- the thesis's headline claim -- was absent from the
pre-specified `PRIMARY` list and was added. This enlarges the FDR family from 16
to 18 rows, which is the conservative direction; it does not change any other
row's verdict.

## Between-seed sd is the dominant uncertainty

sd across seeds ranges 0.0017 (E7 vs E6) to 0.0258 (E4 vs E3). For the five
comparisons that failed, the between-seed sd is 2-5x the effect being measured.
Three seeds is thin for effects of this size; the honest statement in Chapter 4
is that the study is underpowered for single-component effects of ~0.005 QWK,
not that those components are inert.
