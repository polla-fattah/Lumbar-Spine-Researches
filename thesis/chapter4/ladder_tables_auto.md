# Chapter 4 — Results (auto-generated)

Generated 2026-08-26 22:17 · profile `full` · mode `real` · 50 epochs · seeds [42, 43, 44]


## Table 4.1 — Ablation ladder, held-out test set

| Run | Acc | Macro-F1 | QWK | ECE | Severe recall | Severe→Normal | d≥2 | Params |
| :-- | --: | --: | --: | --: | --: | --: | --: | --: |
| E0 (s42) | 0.849 | 0.690 | 0.735 | 0.035 | 0.729 | 0.055 | 0.007 | 11.31M |
| E0 (s43) | 0.858 | 0.694 | 0.721 | 0.014 | 0.603 | 0.095 | 0.007 | 11.31M |
| E0 (s44) | 0.853 | 0.698 | 0.727 | 0.052 | 0.550 | 0.065 | 0.005 | 11.31M |
| E1 (s42) | 0.845 | 0.693 | 0.716 | 0.033 | 0.558 | 0.043 | 0.005 | 33.92M |
| E1 (s43) | 0.851 | 0.690 | 0.723 | 0.014 | 0.626 | 0.070 | 0.005 | 33.92M |
| E1 (s44) | 0.845 | 0.698 | 0.727 | 0.016 | 0.611 | 0.020 | 0.003 | 33.92M |
| E2 (s42) | 0.845 | 0.713 | 0.739 | 0.010 | 0.673 | 0.033 | 0.003 | 33.97M |
| E2 (s43) | 0.849 | 0.694 | 0.721 | 0.044 | 0.570 | 0.055 | 0.005 | 33.97M |
| E2 (s44) | 0.843 | 0.685 | 0.709 | 0.129 | 0.568 | 0.065 | 0.005 | 33.97M |
| E3 (s42) | 0.846 | 0.689 | 0.715 | 0.044 | 0.543 | 0.055 | 0.005 | 33.97M |
| E3 (s43) | 0.861 | 0.705 | 0.743 | 0.029 | 0.608 | 0.048 | 0.004 | 33.97M |
| E3 (s44) | 0.840 | 0.704 | 0.720 | 0.056 | 0.590 | 0.048 | 0.004 | 33.97M |
| E4 (s42) | 0.860 | 0.709 | 0.742 | 0.016 | 0.616 | 0.043 | 0.004 | 33.97M |
| E4 (s43) | 0.841 | 0.688 | 0.720 | 0.044 | 0.621 | 0.043 | 0.006 | 33.97M |
| E4 (s44) | 0.855 | 0.694 | 0.732 | 0.008 | 0.558 | 0.043 | 0.004 | 33.97M |
| E5 (s42) | 0.838 | 0.700 | 0.715 | 0.065 | 0.543 | 0.033 | 0.003 | 34.10M |
| E5 (s43) | 0.848 | 0.683 | 0.722 | 0.114 | 0.558 | 0.050 | 0.004 | 34.10M |
| E5 (s44) | 0.854 | 0.698 | 0.731 | 0.104 | 0.568 | 0.043 | 0.004 | 34.10M |
| E6 (s42) | 0.854 | 0.709 | 0.742 | 0.012 | 0.603 | 0.038 | 0.003 | 34.76M |
| E6 (s43) | 0.847 | 0.710 | 0.729 | 0.084 | 0.550 | 0.035 | 0.003 | 34.76M |
| E6 (s44) | 0.849 | 0.710 | 0.733 | 0.012 | 0.636 | 0.040 | 0.003 | 34.76M |
| E6_shuffled (s42) | 0.842 | 0.691 | 0.728 | 0.049 | 0.560 | 0.023 | 0.002 | 34.76M |
| E6_shuffled (s43) | 0.850 | 0.700 | 0.733 | 0.011 | 0.595 | 0.040 | 0.004 | 34.76M |
| E6_shuffled (s44) | 0.844 | 0.712 | 0.728 | 0.013 | 0.528 | 0.025 | 0.002 | 34.76M |
| E6_ungated (s42) | 0.837 | 0.684 | 0.715 | 0.030 | 0.668 | 0.038 | 0.008 | 34.49M |
| E6_ungated (s43) | 0.865 | 0.722 | 0.749 | 0.019 | 0.623 | 0.058 | 0.004 | 34.49M |
| E6_ungated (s44) | 0.852 | 0.707 | 0.743 | 0.011 | 0.678 | 0.038 | 0.005 | 34.49M |
| E7 (s42) | 0.858 | 0.708 | 0.753 | 0.078 | 0.658 | 0.033 | 0.003 | 34.76M |
| E7 (s43) | 0.845 | 0.719 | 0.740 | 0.026 | 0.651 | 0.033 | 0.003 | 34.76M |
| E7 (s44) | 0.847 | 0.714 | 0.741 | 0.035 | 0.641 | 0.035 | 0.003 | 34.76M |

## Table 4.2 — Across seeds (mean ± sd)

| Run | Macro-F1 | QWK |
| :-- | --: | --: |
| E0 | 0.694 ± 0.004 | 0.728 ± 0.007 |
| E1 | 0.693 ± 0.004 | 0.722 ± 0.006 |
| E2 | 0.697 ± 0.014 | 0.723 ± 0.015 |
| E3 | 0.700 ± 0.009 | 0.726 ± 0.015 |
| E4 | 0.697 ± 0.011 | 0.731 ± 0.011 |
| E5 | 0.694 ± 0.009 | 0.723 ± 0.008 |
| E6 | 0.710 ± 0.001 | 0.735 ± 0.007 |
| E6_shuffled | 0.701 ± 0.010 | 0.730 ± 0.003 |
| E6_ungated | 0.704 ± 0.019 | 0.736 ± 0.018 |
| E7 | 0.714 ± 0.006 | 0.745 ± 0.007 |

## Table 4.3 — Pre-specified primary comparisons

Difference averaged over training seeds, with one patient-level bootstrap resample shared across seeds. FDR is controlled across these rows only — one test per comparison and metric.

| Comparison | Tests | Metric | Δ | 95% CI | sd(seeds) | seeds + | p | p(FDR) | Sig |
| :-- | :-- | :-- | --: | :-- | --: | :-: | --: | --: | :-: |
| E7 vs E0 | full system vs single-sequence baseline | macro_f1 | +0.0197 | [+0.0102, +0.0301] | 0.0050 | 3/3 | 0.0000 | 0.0000 | yes |
| E7 vs E0 | full system vs single-sequence baseline | qwk | +0.0172 | [+0.0064, +0.0285] | 0.0029 | 3/3 | 0.0000 | 0.0000 | yes |
| E6 vs E6_shuffled | anatomical topology vs arbitrary topology (CC III) | macro_f1 | +0.0088 | [-0.0007, +0.0186] | 0.0097 | 2/3 | 0.0720 | 0.2160 | no |
| E6 vs E6_shuffled | anatomical topology vs arbitrary topology (CC III) | qwk | +0.0051 | [-0.0036, +0.0141] | 0.0094 | 2/3 | 0.2390 | 0.5700 | no |
| E6 vs E5 | typed heterogeneous vs homogeneous graph | macro_f1 | +0.0160 | [+0.0061, +0.0256] | 0.0096 | 3/3 | 0.0000 | 0.0000 | yes |
| E6 vs E5 | typed heterogeneous vs homogeneous graph | qwk | +0.0123 | [+0.0028, +0.0216] | 0.0129 | 3/3 | 0.0120 | 0.0540 | no |
| E6 vs E6_ungated | gated residual vs ungated | macro_f1 | +0.0052 | [-0.0050, +0.0143] | 0.0185 | 2/3 | 0.2850 | 0.5700 | no |
| E6 vs E6_ungated | gated residual vs ungated | qwk | -0.0009 | [-0.0110, +0.0080] | 0.0250 | 1/3 | 0.8370 | 0.8862 | no |
| E5 vs E0 | relational message passing vs independent heads | macro_f1 | -0.0004 | [-0.0118, +0.0115] | 0.0102 | 1/3 | 0.9660 | 0.9660 | no |
| E5 vs E0 | relational message passing vs independent heads | qwk | -0.0050 | [-0.0153, +0.0057] | 0.0127 | 2/3 | 0.3430 | 0.6174 | no |
| E2 vs E1 | disease-conditioned routing vs fixed fusion (CC II) | macro_f1 | +0.0040 | [-0.0063, +0.0149] | 0.0164 | 2/3 | 0.4560 | 0.6840 | no |
| E2 vs E1 | disease-conditioned routing vs fixed fusion (CC II) | qwk | +0.0010 | [-0.0079, +0.0107] | 0.0208 | 1/3 | 0.7920 | 0.8862 | no |
| E3 vs E2 | modality dropout | macro_f1 | +0.0023 | [-0.0076, +0.0117] | 0.0227 | 2/3 | 0.7060 | 0.8568 | no |
| E3 vs E2 | modality dropout | qwk | +0.0032 | [-0.0060, +0.0119] | 0.0243 | 2/3 | 0.5230 | 0.7242 | no |
| E4 vs E3 | anatomical cross-sequence SSL (CC I) | macro_f1 | -0.0024 | [-0.0121, +0.0082] | 0.0193 | 1/3 | 0.7140 | 0.8568 | no |
| E4 vs E3 | anatomical cross-sequence SSL (CC I) | qwk | +0.0051 | [-0.0038, +0.0148] | 0.0258 | 2/3 | 0.2630 | 0.5700 | no |
| E7 vs E6 | ordinal + clinical cost | macro_f1 | +0.0040 | [-0.0053, +0.0144] | 0.0048 | 2/3 | 0.4000 | 0.6545 | no |
| E7 vs E6 | ordinal + clinical cost | qwk | +0.0099 | [+0.0017, +0.0186] | 0.0017 | 3/3 | 0.0150 | 0.0540 | no |

### Table 4.3b — Per-seed differences (descriptive, not tested)

Each row resamples patients with that seed's trained model held fixed, so its interval covers test-set sampling only and excludes training stochasticity. On this campaign that omission is decisive: several comparisons reverse sign between seeds with narrow intervals on both sides. These rows are shown for transparency and carry no significance claim.

| Comparison | Seed | Metric | Δ | 95% CI | p |
| :-- | :-: | :-- | --: | :-- | --: |
| E7 vs E0 | 42 | macro_f1 | +0.0179 | [-0.0008, +0.0358] | 0.0560 |
| E7 vs E0 | 42 | qwk | +0.0183 | [+0.0025, +0.0326] | 0.0210 |
| E7 vs E0 | 43 | macro_f1 | +0.0253 | [+0.0086, +0.0433] | 0.0000 |
| E7 vs E0 | 43 | qwk | +0.0194 | [+0.0024, +0.0385] | 0.0280 |
| E7 vs E0 | 44 | macro_f1 | +0.0159 | [-0.0011, +0.0344] | 0.0750 |
| E7 vs E0 | 44 | qwk | +0.0140 | [-0.0012, +0.0302] | 0.0840 |
| E6 vs E6_shuffled | 42 | macro_f1 | +0.0177 | [-0.0006, +0.0349] | 0.0620 |
| E6 vs E6_shuffled | 42 | qwk | +0.0146 | [-0.0011, +0.0299] | 0.0730 |
| E6 vs E6_shuffled | 43 | macro_f1 | +0.0102 | [-0.0052, +0.0274] | 0.2000 |
| E6 vs E6_shuffled | 43 | qwk | -0.0041 | [-0.0182, +0.0105] | 0.5870 |
| E6 vs E6_shuffled | 44 | macro_f1 | -0.0016 | [-0.0184, +0.0155] | 0.8950 |
| E6 vs E6_shuffled | 44 | qwk | +0.0049 | [-0.0088, +0.0191] | 0.5010 |
| E6 vs E5 | 42 | macro_f1 | +0.0087 | [-0.0087, +0.0257] | 0.3540 |
| E6 vs E5 | 42 | qwk | +0.0269 | [+0.0110, +0.0420] | 0.0000 |
| E6 vs E5 | 43 | macro_f1 | +0.0268 | [+0.0107, +0.0437] | 0.0020 |
| E6 vs E5 | 43 | qwk | +0.0074 | [-0.0070, +0.0224] | 0.3010 |
| E6 vs E5 | 44 | macro_f1 | +0.0124 | [-0.0055, +0.0312] | 0.1800 |
| E6 vs E5 | 44 | qwk | +0.0025 | [-0.0129, +0.0173] | 0.7370 |
| E6 vs E6_ungated | 42 | macro_f1 | +0.0248 | [+0.0060, +0.0437] | 0.0130 |
| E6 vs E6_ungated | 42 | qwk | +0.0274 | [+0.0113, +0.0424] | 0.0020 |
| E6 vs E6_ungated | 43 | macro_f1 | -0.0120 | [-0.0276, +0.0051] | 0.1700 |
| E6 vs E6_ungated | 43 | qwk | -0.0201 | [-0.0356, -0.0047] | 0.0110 |
| E6 vs E6_ungated | 44 | macro_f1 | +0.0028 | [-0.0156, +0.0206] | 0.7590 |
| E6 vs E6_ungated | 44 | qwk | -0.0099 | [-0.0278, +0.0068] | 0.2340 |
| E5 vs E0 | 42 | macro_f1 | +0.0101 | [-0.0083, +0.0286] | 0.2800 |
| E5 vs E0 | 42 | qwk | -0.0195 | [-0.0341, -0.0045] | 0.0080 |
| E5 vs E0 | 43 | macro_f1 | -0.0103 | [-0.0298, +0.0074] | 0.2570 |
| E5 vs E0 | 43 | qwk | +0.0010 | [-0.0165, +0.0191] | 0.9380 |
| E5 vs E0 | 44 | macro_f1 | -0.0009 | [-0.0181, +0.0161] | 0.9630 |
| E5 vs E0 | 44 | qwk | +0.0035 | [-0.0112, +0.0182] | 0.5980 |
| E2 vs E1 | 42 | macro_f1 | +0.0203 | [+0.0017, +0.0396] | 0.0290 |
| E2 vs E1 | 42 | qwk | +0.0234 | [+0.0078, +0.0397] | 0.0050 |
| E2 vs E1 | 43 | macro_f1 | +0.0041 | [-0.0135, +0.0225] | 0.6150 |
| E2 vs E1 | 43 | qwk | -0.0025 | [-0.0186, +0.0154] | 0.8190 |
| E2 vs E1 | 44 | macro_f1 | -0.0124 | [-0.0308, +0.0067] | 0.1970 |
| E2 vs E1 | 44 | qwk | -0.0178 | [-0.0345, -0.0017] | 0.0320 |
| E3 vs E2 | 42 | macro_f1 | -0.0235 | [-0.0437, -0.0060] | 0.0080 |
| E3 vs E2 | 42 | qwk | -0.0240 | [-0.0404, -0.0092] | 0.0010 |
| E3 vs E2 | 43 | macro_f1 | +0.0112 | [-0.0039, +0.0263] | 0.1610 |
| E3 vs E2 | 43 | qwk | +0.0228 | [+0.0081, +0.0371] | 0.0000 |
| E3 vs E2 | 44 | macro_f1 | +0.0192 | [+0.0009, +0.0381] | 0.0420 |
| E3 vs E2 | 44 | qwk | +0.0108 | [-0.0059, +0.0266] | 0.2020 |
| E4 vs E3 | 42 | macro_f1 | +0.0196 | [+0.0015, +0.0386] | 0.0350 |
| E4 vs E3 | 42 | qwk | +0.0270 | [+0.0105, +0.0441] | 0.0000 |
| E4 vs E3 | 43 | macro_f1 | -0.0166 | [-0.0341, +0.0025] | 0.0800 |
| E4 vs E3 | 43 | qwk | -0.0234 | [-0.0375, -0.0096] | 0.0020 |
| E4 vs E3 | 44 | macro_f1 | -0.0100 | [-0.0269, +0.0072] | 0.2660 |
| E4 vs E3 | 44 | qwk | +0.0117 | [-0.0027, +0.0262] | 0.1060 |
| E7 vs E6 | 42 | macro_f1 | -0.0009 | [-0.0173, +0.0161] | 0.9300 |
| E7 vs E6 | 42 | qwk | +0.0109 | [-0.0018, +0.0241] | 0.1020 |
| E7 vs E6 | 43 | macro_f1 | +0.0087 | [-0.0081, +0.0245] | 0.3250 |
| E7 vs E6 | 43 | qwk | +0.0110 | [-0.0035, +0.0256] | 0.1370 |
| E7 vs E6 | 44 | macro_f1 | +0.0043 | [-0.0119, +0.0212] | 0.5970 |
| E7 vs E6 | 44 | qwk | +0.0079 | [-0.0055, +0.0225] | 0.2580 |

## Reading Table 4.3

The decisive row is **E6 vs E6_shuffled**. E6_shuffled has the same 25 nodes and the same 160 edges, with endpoints permuted. If the two do not separate, the finding is that additional message-passing capacity helped and anatomical topology did not — which answers RQ1 and belongs in the thesis exactly as stated.

A negative or null result on any row is an answer, not a failure. Chapter 3 commits to reporting each comparison whichever way it falls.
