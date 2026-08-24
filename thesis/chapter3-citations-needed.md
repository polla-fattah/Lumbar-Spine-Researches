# Chapter 3 — Literature Required

**Audit date:** 2026-08-24 · Chapter 3 currently cites **14** papers across 28 sections
**Purpose:** ground every methodological choice, and defend the three novelty claims

---

## The problem, in one table

Citation density per section, from the current `chapter3.tex`:

| Section | Words | Cites | |
| :--- | ---: | ---: | :--- |
| **Core Contribution II — Adaptive Sequence Routing** | 976 | **0** | 🔴 novelty claim, unsupported |
| **Core Contribution III — Heterogeneous Graph** | 1273 | **0** | 🔴 novelty claim, unsupported |
| Reference Standard and Target Encoding | 920 | 0 | 🔴 |
| Core Contribution I — Cross-Sequence SSL | 927 | 1 | 🟠 thin for a novelty claim |
| Few-Shot Domain Adaptation | 635 | 0 | 🔴 |
| Optimisation and Training Protocol | 527 | 0 | 🟠 |
| Methodological Safeguards / Threats | 526 | 0 | 🟠 |
| Data Partitioning and Leakage Control | 499 | 0 | 🟠 |
| External Validation at Rizgary | 488 | 0 | 🟠 |
| Evaluation Metrics | 463 | 0 | 🔴 |
| Experimental Ladder and Ablation | 430 | 0 | 🟠 |
| Statistical Analysis | 403 | 0 | 🔴 |
| Calibration, Uncertainty, Selective Prediction | 240 | 0 | 🟠 |

> **The exposure:** a viva panel will ask *"what did you build on, and how do you know
> this is novel?"* for each core contribution. Two of the three currently answer with
> silence.

**Verification status.** Four entries below were verified against publisher records on
2026-08-24 and are marked ✅. The remainder are drawn from established knowledge; a
comparable batch of 16 was verified earlier in this project and all 16 proved correct,
but **check volume, pages and DOI before submission**.

---

# PRIORITY 1 — The novelty claims

## Core Contribution III: Heterogeneous Disease–Anatomy Graph

The single most exposed section. It proposes a **typed** graph over 25 level–condition
nodes with three edge types, and cites nothing. Every one of these is foundational and
a panel will expect them.

| Paper | Why Chapter 3 needs it | Link |
| :--- | :--- | :--- |
| Kipf & Welling (2017), *Semi-Supervised Classification with GCNs* | The baseline graph convolution your homogeneous-graph control implements | [arxiv.org/abs/1609.02907](https://arxiv.org/abs/1609.02907) |
| Veličković et al. (2018), *Graph Attention Networks* | Learned rather than fixed neighbour weighting | [arxiv.org/abs/1710.10903](https://arxiv.org/abs/1710.10903) |
| Hamilton et al. (2017), *Inductive Representation Learning (GraphSAGE)* | Inductive setting — your graph must generalise to unseen patients | [arxiv.org/abs/1706.02216](https://arxiv.org/abs/1706.02216) |
| **Schlichtkrull et al. (2017), *Modeling Relational Data with GCNs* (R-GCN)** ✅ | **The direct precedent for typed edges.** Your three edge types are relation-specific weight matrices — this is the paper that introduced them | [arxiv.org/abs/1703.06103](https://arxiv.org/abs/1703.06103) |
| Hu et al. (2020), *Heterogeneous Graph Transformer* | Node- and edge-type-aware attention; closest architectural precedent to your typed graph | [arxiv.org/abs/2003.01332](https://arxiv.org/abs/2003.01332) |
| Dwivedi & Bresson (2021), *A Generalization of Transformer Networks to Graphs* | Bridges attention and graphs — the conceptual step your design makes | [arxiv.org/abs/2012.09699](https://arxiv.org/abs/2012.09699) |
| Ying et al. (2021), *Do Transformers Really Perform Bad for Graph Representation?* (Graphormer) | Structural encodings in graph transformers | [arxiv.org/abs/2106.05234](https://arxiv.org/abs/2106.05234) |

**Already in your bib — cite these too:** `baur2024automated` (the only lumbar GNN, and
its graph is *within* a disc, not across levels — this is your novelty argument),
`nguyen2026crossspine` (disc-level priors, levels still independent).

---

## Core Contribution II: Disease-Conditioned Adaptive Sequence Routing

Also zero citations. The routing formulation is a gating/mixture-of-experts mechanism and
the missing-modality behaviour has direct precedent.

| Paper | Why Chapter 3 needs it | Link |
| :--- | :--- | :--- |
| Shazeer et al. (2017), *Outrageously Large Neural Networks* (sparsely-gated MoE) | The gating formulation your router generalises | [arxiv.org/abs/1701.06538](https://arxiv.org/abs/1701.06538) |
| Baltrušaitis et al. (2017), *Multimodal Machine Learning: A Survey and Taxonomy* | Positions early/intermediate/late fusion — your Section 10 taxonomy | [arxiv.org/abs/1705.09406](https://arxiv.org/abs/1705.09406) |
| Havaei et al. (2016), *HeMIS: Hetero-Modal Image Segmentation* | **The canonical missing-modality medical imaging paper.** Your availability-mask design needs this | [arxiv.org/abs/1607.05194](https://arxiv.org/abs/1607.05194) |
| Neverova et al. (2015), *ModDrop: Adaptive Multi-Modal Gesture Recognition* | Modality dropout — the exact training strategy you propose | [arxiv.org/abs/1501.00102](https://arxiv.org/abs/1501.00102) |
| Hu et al. (2018), *Squeeze-and-Excitation Networks* | Channel-wise gating; the mechanism your per-sequence weights resemble | [arxiv.org/abs/1709.01507](https://arxiv.org/abs/1709.01507) |

**Already in your bib:** `nguyen2026crossspine` (cross-sequence attention),
`batra2025mscan` (multi-view cross-attention), `zeng2025gpt4lfs` (multimodal fusion).

---

## Core Contribution I: Cross-Sequence Self-Supervision *(1 citation — thin)*

| Paper | Why Chapter 3 needs it | Link |
| :--- | :--- | :--- |
| He et al. (2020), *Momentum Contrast (MoCo)* | Queue-based contrastive learning; alternative to SimCLR you should justify against | [arxiv.org/abs/1911.05722](https://arxiv.org/abs/1911.05722) |
| Grill et al. (2020), *Bootstrap Your Own Latent (BYOL)* | Negative-free SSL — relevant because your positives are anatomically defined | [arxiv.org/abs/2006.07733](https://arxiv.org/abs/2006.07733) |
| Caron et al. (2021), *Emerging Properties in Self-Supervised ViTs (DINO)* | Teacher–student SSL | [arxiv.org/abs/2104.14294](https://arxiv.org/abs/2104.14294) |
| Radford et al. (2021), *CLIP* | Cross-modal correspondence as a training signal — the closest conceptual analogue to same-level-different-sequence pairing | [arxiv.org/abs/2103.00020](https://arxiv.org/abs/2103.00020) |
| Azizi et al. (2021), *Big Self-Supervised Models Advance Medical Image Classification* | SSL specifically in medical imaging, with label-efficiency curves like yours | [arxiv.org/abs/2101.05224](https://arxiv.org/abs/2101.05224) |

**Already cited:** `chen2020simple` (SimCLR), `jamaludin2017selfsupervised` — keep both;
the latter is your strongest lineage argument.

---

# PRIORITY 2 — Methodological sections with no support

## Reference Standard and Target Encoding

| Paper | Why | Link |
| :--- | :--- | :--- |
| Warfield et al. (2004), *STAPLE* | Principled fusion of multiple raters into one reference standard | [IEEE TMI 23(7):903–921](https://doi.org/10.1109/TMI.2004.828354) |
| Karimi et al. (2020), *Deep learning with noisy labels: a survey for medical imaging* | Directly supports your label-noise-ceiling argument | [arxiv.org/abs/1912.02911](https://arxiv.org/abs/1912.02911) |

**Already in bib:** `lurie2008reliability` (the κ = 0.49 figure), `richards2026the`.

## Data Partitioning and Leakage Control

| Paper | Why | Link |
| :--- | :--- | :--- |
| Kapoor & Narayanan (2023), *Leakage and the Reproducibility Crisis in ML-based Science* | Your patient-level splitting rule needs this authority | [arxiv.org/abs/2207.07048](https://arxiv.org/abs/2207.07048) |

## Optimisation and Training Protocol

| Paper | Why | Link |
| :--- | :--- | :--- |
| Kingma & Ba (2015), *Adam* | Optimiser | [arxiv.org/abs/1412.6980](https://arxiv.org/abs/1412.6980) |
| Loshchilov & Hutter (2019), *Decoupled Weight Decay (AdamW)* | The variant actually used in practice | [arxiv.org/abs/1711.05101](https://arxiv.org/abs/1711.05101) |
| Loshchilov & Hutter (2017), *SGDR: warm restarts* | Cosine schedule | [arxiv.org/abs/1608.03983](https://arxiv.org/abs/1608.03983) |
| Micikevicius et al. (2018), *Mixed Precision Training* | Your compute-mitigation strategy | [arxiv.org/abs/1710.03740](https://arxiv.org/abs/1710.03740) |

## Few-Shot Domain Adaptation

| Paper | Why | Link |
| :--- | :--- | :--- |
| Hu et al. (2022), *LoRA* | The parameter-efficient method your RQ4 curve depends on | [arxiv.org/abs/2106.09685](https://arxiv.org/abs/2106.09685) |
| Houlsby et al. (2019), *Parameter-Efficient Transfer Learning (Adapters)* | The alternative PEFT family | [arxiv.org/abs/1902.00751](https://arxiv.org/abs/1902.00751) |
| Guan & Liu (2021), *Domain Adaptation for Medical Image Analysis: A Survey* | Frames the whole RQ4 contribution | [arxiv.org/abs/2102.09508](https://arxiv.org/abs/2102.09508) |

## Calibration, Uncertainty and Selective Prediction

| Paper | Why | Link |
| :--- | :--- | :--- |
| Gal & Ghahramani (2016), *Dropout as Bayesian Approximation* | MC dropout | [arxiv.org/abs/1506.02142](https://arxiv.org/abs/1506.02142) |
| Lakshminarayanan et al. (2017), *Simple and Scalable Predictive Uncertainty (Deep Ensembles)* | The stronger baseline you must compare against | [arxiv.org/abs/1612.01474](https://arxiv.org/abs/1612.01474) |
| Angelopoulos & Bates (2023), *A Gentle Introduction to Conformal Prediction* | Distribution-free guarantees for selective prediction | [arxiv.org/abs/2107.07511](https://arxiv.org/abs/2107.07511) |

**Already in bib:** `guo2017calibration` — cite it here; currently unused in Ch3.

---

# PRIORITY 3 — Evaluation, statistics and reporting

## Evaluation Metrics

| Paper | Why | Link |
| :--- | :--- | :--- |
| Cohen (1968), *Weighted kappa* | Your primary agreement statistic — cite the origin | [Psychological Bulletin 70(4):213–220](https://doi.org/10.1037/h0026256) |
| Brier (1950), *Verification of forecasts expressed in terms of probability* | Brier score | [Monthly Weather Review 78(1):1–3](https://doi.org/10.1175/1520-0493(1950)078%3C0001:VOFEIT%3E2.0.CO;2) |
| Vickers & Elkin (2006), *Decision curve analysis* | If you report DCA, this is the source | [Med Decis Making 26(6):565–574](https://doi.org/10.1177/0272989X06295361) |

## Statistical Analysis

| Paper | Why | Link |
| :--- | :--- | :--- |
| DeLong et al. (1988), *Comparing areas under two or more correlated ROC curves* | You name the DeLong test — cite it | [Biometrics 44(3):837–845](https://doi.org/10.2307/2531595) |
| Efron & Tibshirani (1993), *An Introduction to the Bootstrap* | Your CI methodology | Chapman & Hall, ISBN 978-0412042317 |

## Planned Reporting Standard

| Paper | Why | Link |
| :--- | :--- | :--- |
| **Tejani et al. (2024), *CLAIM: 2024 Update*** ✅ | The current AI-in-imaging reporting standard. **Note: the 2024 update is Tejani et al., not Mongan et al.** — Mongan is a co-author | [doi:10.1148/ryai.240300](https://pubs.rsna.org/doi/10.1148/ryai.240300) · PMID 38809149 |
| **Collins et al. (2024), *TRIPOD+AI statement*** ✅ | Prediction-model reporting | [BMJ 2024;385:e078378](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11025451/) · PMID 38626948 |
| Bossuyt et al. (2015), *STARD 2015* | Diagnostic accuracy reporting | [BMJ 2015;351:h5527](https://doi.org/10.1136/bmj.h5527) |
| von Elm et al. (2007), *STROBE statement* | For the observational/epidemiology strand | [doi:10.1016/S0140-6736(07)61602-X](https://doi.org/10.1016/S0140-6736(07)61602-X) |

---

# Summary

| Priority | Papers | Effect |
| :--- | ---: | :--- |
| **1 — novelty claims** | **17** | Closes the "what did you build on?" exposure on all three contributions |
| **2 — methodology** | **13** | Grounds design choices that are currently assertions |
| **3 — evaluation/reporting** | **9** | Standard practice; their absence looks careless |
| **Total new** | **~39** | Ch3 goes from 14 → ~53 citations |

Roughly **53 citations for a 15,700-word methodology chapter** is normal. Fourteen is not,
and a panel will notice.

**Also cite these, already in your bib and currently unused in Ch3:** `guo2017calibration`,
`lurie2008reliability`, `mcsweeney2023external`, `zhang2023deep`, `wu2026external`,
`nguyen2026crossspine`, `baur2024automated`, `acharya2026disccentric`, `trinc2026beyond`.
Nine free additions that strengthen the argument at no research cost.

---

## Two notes before you use this

**Check the unverified entries.** Only the four marked ✅ were confirmed against publisher
records. The arXiv identifiers are from established knowledge and are very likely correct,
but titles, years and page ranges should be checked at import — JabRef can pull most by DOI
or arXiv ID in seconds.

**Do not cite what you have not read.** A panel may ask why a specific paper is cited. The
Priority 1 list is genuinely necessary reading for defending the contributions; Priorities 2
and 3 are mostly standard methods where citing the origin is sufficient.
