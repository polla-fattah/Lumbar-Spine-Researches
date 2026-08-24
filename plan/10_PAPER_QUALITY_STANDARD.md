# Paper Quality Standard

**What every paper from this programme must satisfy before submission**
Supervisor: Dr. Polla Abdulhamid Fattah · Applies to: Selar's PhD papers and all four MSc projects

---

## Why this document exists

Three systematic reviews in our own bibliography reach the same verdict about this field,
independently:

| Review | Finding |
| :--- | :--- |
| Wang et al.\ 2024 | Pooled sensitivity 0.84, specificity 0.87 across 12 studies and 15,044 patients — **yet "none of them is reliable and practical enough to apply in real clinical practice"**. Heterogeneity I² ≈ 99%; 4 of 12 studies at high risk of bias. |
| Compte et al.\ 2023 | No significant difference between algorithm families. Algorithms **performed worse in replication and external validation than in their development studies**. |
| Mendes et al.\ 2026 | Of 56 segmentation studies, **most used private datasets and lacked external validation**. |

The field does not have an accuracy problem. It has a **credibility problem**. Papers
report excellent numbers that do not survive contact with another hospital, another
reader, or another reviewer.

The standard below is not generic advice. Every requirement is drawn from what the
*strongest* papers in our 108-record bibliography actually did, and every failure mode
from what the weak ones did not.

---

## 1. The five things that get papers rejected in this field

From the reviews above and from reading the full corpus:

1. **Single-institution data with no external test.** The most common weakness, and the
   one reviewers now look for first.
2. **Ground truth from one reader, with no adjudication and no reliability figure.**
3. **A task definition that quietly differs from everyone else's** while using the same
   label vocabulary, making comparison meaningless.
4. **Metrics that flatter an imbalanced problem** — headline accuracy on a dataset that
   is 85% one class.
5. **No ablation.** A final number with no evidence that any individual component earned
   its place.

If a manuscript from this programme has any of these, it is not ready.

---

## 2. Ground truth — the standard to meet

> **Rule: the reference standard must be described precisely enough that a reader can
> judge how much to trust it, and its reliability must be reported as a number.**

Our own bibliography sets the bar:

- **Tumko et al.** graded their 150-study external set with a **panel of seven
  radiologists**, resolving by majority vote with an external radiologist adjudicating
  disagreements.
- **Su et al.** used two clinicians with an expert spine surgeon adjudicating.
- **Al-Kafri et al.** went further and introduced two purpose-built metrics —
  *confidence* and *consistency* — to assess the quality of the **ground truth itself**,
  not just the model.

**Requirements for our papers:**

- [ ] State who annotated, their specialty and years of experience
- [ ] State how disagreements were resolved
- [ ] Report inter-reader agreement (κ) on at least a subset — **if you cannot, say so explicitly and treat it as a limitation**
- [ ] For the Rizgary cohort: state that reports are the primary source, the spreadsheet is a transcription, and that 14 of 195 ages disagree between them
- [ ] State the label-coverage gaps plainly — subarticular findings appear in **0%** of local reports, laterality in only **27%**

**The trap to avoid.** Published inter-reader agreement for lumbar MRI is
κ = 0.73 for central canal but only **0.49 for subarticular stenosis**
(Lurie et al.). A model cannot be shown to exceed the reproducibility of the process that
generated its labels. If a paper from this programme reports agreement above the human
ceiling, the finding is a protocol artefact and a reviewer will say so.

---

## 3. Evaluation — the metric panel

> **Rule: never report a single headline number. Report a panel, and always include the
> clinically decisive class separately.**

Overall accuracy is close to meaningless here. In LumbarDISC, **85.4%** of spinal canal
grades are Normal/Mild — a model that predicts Normal/Mild unconditionally scores 85% and
is clinically worthless.

**Every results table must contain:**

- [ ] **Balanced accuracy or macro-F1** — corrects for prevalence
- [ ] **Agreement statistic** (κ, ideally quadratic-weighted given the ordinal scale) — this is what makes results comparable to the human reliability figures
- [ ] **Per-class recall, reported separately for the Severe class** — the number a clinician actually cares about
- [ ] **The distribution of error magnitudes**, not just the error rate
- [ ] **Confidence intervals** on every headline figure — bootstrap is fine
- [ ] **Statistical comparison** between models (DeLong for AUCs, paired tests otherwise) rather than comparing point estimates by eye

**The model to copy.** McSweeney et al.\ reported that SpineNet disagreed with human
raters on 20.83% of discs — **but that only 0.85% differed by more than one grade**. That
second number transforms the interpretation, and most papers never compute it.

**Also copy Ishimoto et al.**, who reported *both* exact-grade agreement (65.7%) *and* the
collapsed severe-versus-rest figure (94.1%, κ = 0.75) rather than choosing whichever
looked better.

---

## 4. Validation — splits and external testing

> **Rule: split by patient, never by image. If a paper claims generalisation, it must
> have tested on data from an institution it never trained on.**

- [ ] **Patient-level splitting**, verified — no study_id may appear in more than one split
- [ ] **Site-level splitting** where the data permits it (RSNA spans 8 institutions)
- [ ] Repeated seeds, and report the variance — a single run is an anecdote
- [ ] Cross-validation **or** a held-out test set, with the choice justified
- [ ] External validation on a genuinely independent cohort, or an explicit statement that generalisation was not tested

**Expect the drop, and report it honestly.** This is well documented in our bibliography:

| Study | Internal → external |
| :--- | :--- |
| Zhang et al. | Classification **87.70% → 74.23%** (detection barely moved: IoU 0.82 → 0.70) |
| Su et al. | Roughly **7–10 points** lost across three conditions |
| Yilihamu et al. | 18-category precision **81.21% → 74.50%**; 4-category severity held at 92.51% → 90.07% |

A paper reporting *no* external drop will not be believed. A paper that measures and
explains the drop is more credible than one that avoids testing for it.

---

## 5. Ablation — proving each component earns its place

> **Rule: for a methods paper, the ablation IS the contribution. A final number without
> one is an engineering result, not a scientific one.**

AMOG-Net v2 has three central novelty areas plus several supporting components. Publishing "AMOG-Net achieves 0.91" proves nothing about which idea matters. The E0–E8 ladder in [`07_AMOGNET_TECHNICAL_SPEC.md`](07_AMOGNET_TECHNICAL_SPEC.md) exists for this reason:

```
Baseline → +Aligned ROI → +Adaptive Routing → +Missing-Modality → +Anatomical SSL → +Homogeneous Graph → +Typed Graph → +Calibration
```

- [ ] Each increment reported with confidence intervals
- [ ] Each increment tested for statistical significance, not just eyeballed
- [ ] Components that add nothing **reported as adding nothing**

**Copy Kowlagi et al.**, who ran an ablation of existing methods on a population cohort
and reported performance across subgroups, with public code. **And copy Patil et al.**,
whose twelve supplementary analyses included feature-family ablations, leave-one-scanner-out
generalisation, calibration-depth analysis and decision-curve analysis — and who then
reported the finding that frozen ImageNet ResNet50 features **added no measurable value**
over radiomics. That honesty is why the paper is convincing.

---

## 6. Report negative results

> **Rule: a component that does not work is a finding. Publish it.**

The single most useful result in our bibliography is a negative one. **Niemeyer et al.**
tested soft-kappa loss, ordinal cross-entropy, regression losses, class pooling and
class-weighted losses against plain cross-entropy on 1,599 patients and 7,948 discs — and
found **none of them improved performance**. That result saves every subsequent researcher
months of work.

If our ordinal objectives do not beat cross-entropy, or the graph adds 0.004, **that is
what the paper says**. Reviewers trust papers that report what did not work. A manuscript
in which every component happens to help is less believable, not more.

---

## 7. Reporting standards and reproducibility

- [ ] Follow the appropriate checklist and **submit it with the manuscript**:
      **CLAIM** for AI in medical imaging, **STARD** for diagnostic accuracy,
      **TRIPOD+AI** for prediction models, **STROBE** for the epidemiology paper.
      *(Confirm the current version of each before submission.)*
- [ ] Release code with pretrained weights — Kowlagi, Chen and Batra all did, and it is
      increasingly expected
- [ ] State hyperparameters, augmentation, hardware and training time
- [ ] State the exact dataset version and split indices so the experiment can be repeated
- [ ] Declare what the model was **not** tested on

---

## 8. Framing — the clinical question leads

For a hospital-commissioned programme, the framing decides the audience. A radiology
journal wants the clinical question first and the architecture second.

- [ ] Open with the clinical problem, not the model
- [ ] State what a clinician could do differently if the result holds
- [ ] Be explicit about what the work does **not** establish — model performance is not
      clinical benefit, and only a prospective reader study can demonstrate the latter
      (Lim et al.)
- [ ] Avoid presenting saliency maps as evidence of reasoning. An attention map shows
      *where* the network responded, not *why*, and reviewers in this field now say so

---

## 9. Committee and proposal integrity — before a project is advertised

A technically good project can still be rejected at proposal stage if its framing is
incorrect. Add these checks before publishing a student project title:

- [ ] **Sampling frame is stated correctly.** A tertiary-hospital symptomatic/referral
      cohort must not be presented as population prevalence.
- [ ] **"First" / "novel" claims have been checked with a targeted current literature
      search.** If regional studies exist, narrow the claim instead of pretending they do
      not.
- [ ] **Every requested outcome actually exists in the data.** Age at MRI is not age of
      disease onset; imaging severity is not surgical urgency; absent follow-up cannot be
      replaced with synthetic outcomes.
- [ ] **Ablation experiments change one scientific variable at a time.** For sequence
      ablation, matched models trained for each input configuration are the primary design;
      zeroing an unseen modality only at inference is an out-of-distribution stress test,
      not clean evidence that the modality is unnecessary.
- [ ] **Project dependencies are non-blocking.** An MSc student's graduation must not
      depend on a PhD component being completed first unless the dependency is unavoidable
      and formally scheduled.
- [ ] **Student-facing text does not guarantee publication or a performance threshold.**
      State "manuscript prepared for submission" and treat negative results as valid.
- [ ] **Shared datasets have a stewardship / authorship policy.** Dataset access alone does
      not imply authorship; ownership language should refer to programme / institutional
      stewardship, not personal student ownership.

### Updated AMOG-Net novelty rule

Chai et al. (2026) already combine anatomy-guided localisation, multi-sequence ROIs,
biomarkers, inter-level Transformer context and ordinal grading. Therefore AMOG-Net papers
must not claim those ingredients as new by themselves. The revised novelty tests are:

1. typed heterogeneous disease–anatomy graph vs simple level Transformer / homogeneous graph;
2. disease-conditioned sequence routing + arbitrary missing-modality robustness;
3. anatomically aligned cross-sequence self-supervision;
4. independent zero-shot / few-shot cross-institutional transfer.

---

# Pre-submission checklist

Run this before any manuscript leaves the group.

**Ground truth**
- [ ] Annotator qualifications, adjudication procedure and reliability figure all stated
- [ ] Label-coverage limitations stated plainly

**Evaluation**
- [ ] Balanced accuracy / macro-F1, weighted κ, per-class Severe recall all reported
- [ ] Confidence intervals on every headline number
- [ ] Model comparisons tested statistically

**Validation**
- [ ] Patient-level splits verified programmatically
- [ ] External or site-held-out results reported, or their absence stated as a limitation
- [ ] Multiple seeds, variance reported

**Contribution**
- [ ] Ablation isolates every claimed component
- [ ] Components that did not help are reported as such

**Reporting**
- [ ] Reporting checklist completed and attached
- [ ] Code and weights released
- [ ] Limitations section names the reference-standard ceiling

**Framing**
- [ ] Clinical question leads
- [ ] No claim of clinical benefit without a prospective study

---

> **The one-line test.** Before submitting, ask: *if a sceptical reviewer from another
> hospital tried to reproduce this, what would they find that we have not already
> disclosed?* Whatever the answer is, put it in the paper first.

---

## Current closest-work reference for AMOG-Net proposal review

Chai Z, Liu C, Qin R, Zhao D, Shi A. (2026). *Anatomy-guided context-aware deep learning for lumbar degenerative disease grading and burden-aware risk assessment on MRI*. Frontiers in Medicine, 13:1848548. https://doi.org/10.3389/fmed.2026.1848548
