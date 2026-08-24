# Publication Plan — Candidate Papers from the AMOG-Net Programme

**Companion to** [`01_SELAR_PHD_ROADMAP.md`](01_SELAR_PHD_ROADMAP.md) **and** [`07_AMOGNET_TECHNICAL_SPEC.md`](07_AMOGNET_TECHNICAL_SPEC.md)

If the PhD is developed around the anatomy-aware, multi-view, graph and ordinal framework, the work decomposes into six original research papers plus an optional review. They are deliberately cumulative: each solves one scientific problem, and the final paper combines them.


---

# Publication realism — read this before using the targets below

The seven papers below are a **menu of what the work could yield**, not a plan to
publish seven papers. This section states what is realistically achievable, because the
original targets were optimistic in three specific ways.

## 1. Too many top-tier targets

Four of the seven papers below name *Medical Image Analysis* or *IEEE TMI*. Both have
acceptance rates around 20–25%, expect large-scale validation against many baselines, and
run 6–12 month review cycles with multiple rounds.

**A PhD that lands one TMI or MedIA paper has done very well.** Naming them for four
papers sets an expectation that will not survive contact with review.

## 2. Nobody has accounted for review time

This is the arithmetic that matters on a 21–24 month programme:

| | Month |
| :--- | :---: |
| Paper 1 submitted | ~10 |
| First decision (major revision typical) | ~16–22 |
| Revision returned and re-reviewed | ~20–26 |
| Acceptance | **often after the viva** |

**Submission is within the candidate's control. Acceptance is not.** Every graduation
criterion should be phrased against submission, with acceptance as the stretch goal.
See the KPI note in [`01_SELAR_PHD_ROADMAP.md`](01_SELAR_PHD_ROADMAP.md).

## 3. Conference deadlines are a scheduling constraint, not a venue choice

MICCAI has one deadline a year, typically late February, with the conference in October.
Miss it and the next opportunity is twelve months away. It is an excellent venue for a
single-component paper — ~30% acceptance, 8 pages, a decision in about three months — but
it must be planned around, not opportunistically targeted.

---

## Realistic tiering

Every paper should have three named venues before writing begins, not one:

| Tier | Role | Examples |
| :--- | :--- | :--- |
| **Reach** | Submit here first if the result is strong | *IEEE TMI*, *MedIA*, *Radiology: AI* |
| **Target** | Where the paper most likely belongs | *Computers in Biology and Medicine*, *Artificial Intelligence in Medicine*, *European Radiology*, *IEEE JBHI* |
| **Floor** | Guarantees the work is published, not lost | *Scientific Reports*, *BMC Medical Imaging*, *Diagnostics*, *European Spine Journal* |

The floor tier is not failure. An indexed, citable paper that exists beats an excellent
manuscript circulating between reach venues for two years.

## What a realistic PhD output looks like

| Outcome | Assessment |
| :--- | :--- |
| **2 papers submitted, 1 accepted** | The graduation minimum. Achievable. |
| **3–4 papers submitted, 2 accepted** | A good PhD. This should be the working target. |
| **All 7 papers** | Not realistic for one candidate in 21–24 months. |

Aim for **three or four** of the seven below. Choose them by which components actually
work, not in advance.

## One easy win that is not in the list below

**A data descriptor for the Rizgary cohort.** A de-identified, report-linked Middle
Eastern lumbar MRI collection does not exist publicly. *Scientific Data* or *Data in
Brief* publish exactly this, acceptance is high because the contribution is the resource
rather than a claim, and every subsequent paper from the group cites it for cohort
description.

It requires the de-identification and report extraction that Phase 1 produces anyway, so
the marginal cost is the manuscript. **This is the highest certainty-per-hour publication
available to the project** and should be written as soon as the cohort is clean.

---

# The seven candidate papers

*Targets below are revised to the three-tier scheme above.*

1. **Anatomy-Aware Automatic Localization of Lumbar Spine Structures for Disease Grading**
   **Core question:** Can automatic segmentation/localization reliably identify L1–L2 through L5–S1 and extract disease-specific ROIs from multisequence MRI?
   **Method:** 3D/2.5D segmentation or heatmap localization using vertebrae, discs, canal and DICOM spatial coordinates, followed by automatic ROI extraction.
   **Novelty requirement:** I would *not* publish merely "we used U-Net for segmentation." Segmentation of the lumbar spine is already mature, and a very recent August 2026 study specifically showed that segmentation pretraining improves label-efficient lumbar degeneration grading. ([arXiv][1]) Therefore our contribution should be **disease-aware localization and cross-sequence anatomical alignment**, not segmentation by itself.
   **Targets** — Reach: MICCAI (main track). Target: *Computers in Biology and Medicine*. Floor: *Biomedical Signal Processing and Control*.
   **Publication strength:** ★★★☆☆

2. **Anatomically Aligned Cross-Sequence Self-Supervised Learning for Lumbar MRI**
   This is one of my favourite papers from the PhD. Instead of conventional ImageNet pretraining, we create a new contrastive/self-supervised algorithm in which Sagittal T1, Sagittal T2/STIR and Axial T2 regions corresponding to the **same patient and same spinal level** are treated as anatomically related views. The model learns that different-looking MRI sequences are representations of the same underlying anatomy. LumbarDISC provides exactly the type of multisequence, multilevel data that makes this possible. ([arXiv][2])
   **Possible title:** *Cross-Sequence Anatomical Contrastive Learning for Label-Efficient Lumbar Spine MRI Analysis*.
   This could investigate 10%, 20%, 50% and 100% label availability and determine whether anatomical pretraining reduces dependence on expert grading. The recent segmentation-pretraining work makes label efficiency especially current, but our **cross-sequence anatomical correspondence objective would be substantially different**. ([arXiv][1])
   **Targets** — Reach: *Medical Image Analysis*. Target: *IEEE JBHI* or MICCAI. Floor: *Artificial Intelligence in Medicine*.
   **Publication strength:** ★★★★☆

3. **Disease-Specific Adaptive Multi-View MRI Fusion with Missing-Sequence Robustness**
   **Core question:** Do different lumbar diseases require different MRI sequences, and can the network learn this automatically?
   Instead of assuming that every condition benefits equally from T1, sagittal T2 and axial T2, the model learns condition-specific weights:
   [
   F_c=\sum_m g_{c,m}F_m
   ]
   where (g_{c,m}) represents the importance of modality (m) for condition (c). During training, we deliberately remove modalities using **modality dropout**, so the model remains operational when a sequence is unavailable.
   Existing work such as M-SCAN already shows that sagittal/axial multi-view cross-attention is powerful for spinal canal stenosis, so merely implementing cross-attention would no longer be novel enough. ([arXiv][3]) Our contribution would instead be **condition-dependent adaptive fusion + arbitrary missing-sequence robustness across all degenerative targets**.
   **Possible title:** *Disease-Adaptive Multi-Sequence Fusion with Missing-Modality Robustness for Lumbar Degenerative MRI Classification*.
   **Targets** — Reach: *Medical Image Analysis*. Target: *Artificial Intelligence in Medicine*. Floor: *Scientific Reports*.
   **Publication strength:** ★★★★☆

4. **A Heterogeneous Anatomical Graph Transformer for Multi-Level Lumbar Disease Grading**
   **This would probably be the main algorithmic PhD paper.**
   Rather than predicting 25 outputs independently, create a graph containing the five lumbar levels × five anatomical conditions. Nodes represent conditions such as L4–L5 canal stenosis or left L4–L5 foraminal narrowing. Different edge types represent:

   * neighbouring spinal levels,
   * diseases at the same level,
   * left/right anatomical relationships.

   A relation-aware Graph Transformer then learns how pathology at one location relates to pathology elsewhere. Current work already includes multiview and multimodal transformer grading, so simply applying a transformer to MRI is increasingly crowded. ([Oxford Research Archive][4]) The stronger contribution is explicitly encoding the **known anatomical topology of the lumbar spine as a heterogeneous graph**.

   **Possible title:** *SpineGraph: Heterogeneous Anatomical Graph Transformers for Joint Multi-Level Multi-Condition Lumbar MRI Grading*.
   **Targets** — Reach: *IEEE TMI* or *Medical Image Analysis*. Target: *IEEE JBHI*. Floor: *Computers in Biology and Medicine*. **This is the paper most worth aiming high with** -- the anatomical graph is the central novelty claim.
   **Publication strength:** ★★★★★

5. **Clinically Cost-Sensitive Ordinal Learning and Uncertainty-Aware Lumbar Disease Grading**
   Here we address something scientifically important that the MSc thesis handles poorly: **Normal/Mild, Moderate and Severe are ordered categories**, not unrelated classes.
   The model therefore learns ordinal boundaries rather than ordinary three-way softmax classification, while a cost-sensitive component makes errors such as Severe → Normal more costly than Severe → Moderate. We then add calibrated uncertainty so the model can say, effectively, **"I am uncertain—refer this examination for human assessment."**
   This needs careful differentiation because ordinal lumbar grading is already becoming an active research direction in 2026; there are now dedicated ordinal lumbar stenosis studies and a recent preprint performing simultaneous ordinal classification across multiple lumbar conditions. ([MDPI][5]) Therefore the publishable contribution should combine **clinical misclassification costs + structured anatomical consistency + uncertainty/selective prediction**, rather than merely using ordinal regression.
   **Possible title:** *Clinically Cost-Aware Ordinal and Uncertainty-Calibrated Learning for Lumbar Degenerative Disease Grading*.
   **Targets** — Reach: *Radiology: Artificial Intelligence*. Target: *Artificial Intelligence in Medicine*. Floor: *Diagnostics* or *BMC Medical Imaging*.
   **Publication strength:** ★★★★☆

6. **External Validation and Domain Generalization of Anatomy-Aware Lumbar MRI AI**
   This paper would move the PhD from algorithm development toward genuine clinical credibility. LumbarDISC already contains data from eight institutions across six countries, which is unusually valuable for studying generalization. ([arXiv][2]) We could perform institution-held-out validation and, ideally, add an independent hospital cohort never seen during development.
   The research becomes: **Does the system retain performance across scanner vendors, MRI protocols, populations and institutions?** We could compare ordinary training against intensity harmonization, domain adaptation/generalization and the anatomy-aware representations developed earlier in the PhD.
   **Possible title:** *Cross-Institutional Generalization of Anatomy-Aware Deep Learning for Lumbar Spine MRI*.
   If an independent clinical cohort and radiologist collaboration are available, this could potentially become one of the strongest translational papers in the PhD.
   **Targets** — Reach: *Radiology: Artificial Intelligence*. Target: *European Radiology*. Floor: *European Spine Journal*. **Strongest clinical paper of the set**, because no published evaluation covers a Middle Eastern cohort.
   **Publication strength:** ★★★★★ with good external data.

7. **The final flagship paper: the complete system**
   This integrates everything:
   [
   \text{MRI}
   \rightarrow
   \text{localization}
   \rightarrow
   \text{anatomical SSL}
   \rightarrow
   \text{adaptive multi-view fusion}
   \rightarrow
   \text{graph reasoning}
   \rightarrow
   \text{ordinal grading}
   \rightarrow
   \text{uncertainty}.
   ]
   It would include a full ablation demonstrating exactly how much each PhD contribution adds. The output would be all lumbar levels and all relevant conditions, rather than a single generic severity label. Because current research is already moving toward simultaneous multi-condition ordinal classification, the integrated system must distinguish itself through **anatomical relational reasoning, modality adaptability and calibrated uncertainty** rather than simply claiming "multi-disease classification." ([Research Square][6])
   **Possible title:** *AMOG-Net: Anatomy-Aware Multi-View Ordinal Graph Learning for Comprehensive Lumbar Spine Degenerative Disease Assessment*.
   **Targets** — Reach: *IEEE TMI* or *Medical Image Analysis*. Target: *Radiology: Artificial Intelligence* if the clinical validation is strong. Floor: *Computers in Biology and Medicine*.
   **Realism note:** this paper only exists if papers 1–6 largely worked. Treat it as the
   thesis's synthesis chapter first and a publication second — if it never gets submitted,
   the dissertation still stands on the component papers.
   **Publication strength:** ★★★★★

There is also an **optional early review/systematic-review paper** on *anatomy-aware AI for lumbar MRI: segmentation, localization, classification and structured disease grading*. But I would not count that as one of the PhD's principal scientific contributions; a broad 2025 survey has already covered modern medical-image segmentation with lumbar-spine emphasis, so ours would need a much narrower structured-diagnosis focus to add value. ([arXiv][7])

### How I would organize the PhD

I would aim for **five essential original papers**, with Papers 2–6 above forming the scientific core. Paper 1 is useful groundwork and Paper 7 is the integrative flagship paper. Importantly, I would **not force seven publications by slicing one experiment into tiny papers**. If some components are not independently substantial, combine them.

The strongest publication trajectory in my view is:

**Anatomical SSL → Adaptive Multi-View Fusion → Graph Transformer → Ordinal/Uncertainty → External Validation → Integrated AMOG-Net.**

That gives the PhD a very clear intellectual story: it starts by learning **where the anatomy is**, then **how different MRI sequences describe it**, then **how the anatomical regions interact**, then **how severity should be reasoned about**, and finally asks whether the resulting system actually generalizes to new clinical populations. That is much more coherent academically than producing six unrelated AI models.

[1]: https://arxiv.org/abs/2608.04810?utm_source=chatgpt.com "Segmentation Pre-training for Label-Efficient Lumbar Spine Degeneration Grading"
[2]: https://arxiv.org/abs/2506.09162?utm_source=chatgpt.com "The RSNA Lumbar Degenerative Imaging Spine Classification (LumbarDISC) Dataset"
[3]: https://arxiv.org/abs/2503.01634?utm_source=chatgpt.com "M-SCAN: A Multistage Framework for Lumbar Spinal Canal Stenosis Grading Using Multi-View Cross Attention"
[4]: https://ora.ox.ac.uk/objects/uuid%3A48b4514d-f427-4b32-ba4e-46ca06bd3ffd/files/spk02cd13n?utm_source=chatgpt.com "Multi-View and Multimodal Radiological Grading Using Spinal ..."
[5]: https://www.mdpi.com/2313-433X/12/8/388?utm_source=chatgpt.com "Ordinal Deep Learning for Lumbar Foraminal Stenosis ..."
[6]: https://www.researchsquare.com/article/rs-9836362/v1.pdf?c=1784572985000&utm_source=chatgpt.com "Single-Stage Deep Learning Pipeline for Multi"
[7]: https://arxiv.org/abs/2510.03318?utm_source=chatgpt.com "Advances in Medical Image Segmentation: A Comprehensive Survey with a Focus on Lumbar Spine Applications"
