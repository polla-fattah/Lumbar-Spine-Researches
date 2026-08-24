# Rationale — Options Considered for Medical Novelty

**Written:** 2026-08-23 · **Status:** decided; retained as the record of *why*
**For:** Rizgary Teaching Hospital lumbar MRI project
**Question it answered:** what is the clinical contribution, as distinct from the computer-science contribution?

> [!NOTE]
> **This document is history, not a live decision.** Options 1 and 2 were adopted and
> became MSc Projects 1 and 2; Option 4's report extraction became MSc Project 3; Option 5
> remains a future contribution once a tool exists; Option 3 is not yet staffed — see the
> phenotype strategy appended at the end.
>
> It is kept because it is the only place recording **the options not taken and why**, and
> the weaknesses of the ones that were. That matters when a supervisor, examiner or
> reviewer asks why the scope is what it is. For the live plan, see
> [`00_MASTER_PLAN_SUMMARY.md`](00_MASTER_PLAN_SUMMARY.md).

---

## The distinction that matters

A better F1 score is a **computer-science** result. It belongs in a CS venue and a hospital cannot act on it.

**Medical novelty** means producing knowledge a clinician did not have, which changes what they do, how they understand the disease, or how they decide. For hospital-commissioned work, the clinical question should lead and the AI should be the *method*, not the message. Radiology journals (European Spine Journal, European Radiology, Radiology: Artificial Intelligence) expect exactly that ordering.

The five options below are all achievable from the Rizgary data. They are not mutually exclusive — options 1 and 2 combine naturally.

---

## Quick comparison

| # | Option | Novelty | Effort | Needs data you may not have | Useful to the hospital |
|---|--------|---------|--------|------------------------------|------------------------|
| 1 | Tertiary-hospital cohort characterisation | Medium–High | **Low** | No | Medium |
| 2 | Protocol optimisation | Medium–High | Medium | No | **Very high** |
| 3 | Degeneration phenotypes | **High** | Medium | No | Medium |
| 4 | Reporting-quality audit | Medium | **Low** | Radiologist identity per report | High |
| 5 | Reader study | **Highest** | **High** | Radiologist time + working tool | **Very high** |

---

## Option 1 — Population epidemiology
### *Level-specific MRI characterisation in a tertiary-hospital referral cohort*

**The gap.** Large, level-resolved lumbar MRI cohorts remain dominated by North American, European and East Asian settings. Regional Iraqi/Kurdish MRI studies exist, so the defensible gap is the lack of a carefully audited, level-resolved tertiary-hospital cohort analysis using this 299-report resource. The study must not infer general-population prevalence from a symptomatic/referral cohort.

**What you would report**
- Distribution of disc bulge / protrusion / extrusion by spinal level
- Age of onset and age-stratified prevalence
- Sex differences
- Whether L4-5 and L5-S1 dominance matches published Western and East Asian norms
- Prevalence of canal stenosis, nerve-root pressure, facet arthrosis, ligamentum flavum hypertrophy

**Why it remains useful.** It provides a reproducible, level-resolved description of findings in a regional tertiary-hospital cohort and a benchmark for future local work. The novelty claim should be based on the exact cohort design and variables after a targeted literature review, not on a broad claim that no Iraqi MRI studies exist.

**Strengths**
- Needs **no AI at all** — the 299 reports alone are sufficient
- Fastest route to a publication
- Establishes the cohort as a documented regional research resource
- The AI later scales it to the hospital's entire archive

**Weaknesses**
- Descriptive rather than causal or population-representative
- Reviewers will ask for comparison against published norms, so a careful literature comparison table is required

**Data required:** already held.

---

## Option 2 — Protocol optimisation
### *What finding-specific trade-off follows when the lumbar MRI sequence set is shortened?*

**The reframe.** "Is sagittal T2 alone enough?" is a computer-science question. **"Which findings remain detectable when the lumbar MRI sequence set is shortened, and what measured scanner-time saving accompanies that trade-off?"** is a clinical / operational question. Abbreviated spine MRI protocols already exist, so the contribution is local finding-specific validation rather than invention of rapid MRI.

**Why the hospital cares**
- Scanner time is the binding constraint on throughput
- Shorter protocols mean more patients per day and lower cost per study
- Less time in the bore means better patient tolerance and fewer motion-corrupted studies
- In a resource-constrained setting this is directly actionable

**What you would report**
Which MRI sequence carries the diagnostic information for **which specific finding** — for example, whether foraminal findings genuinely require sagittal T1, or whether axial T2 is indispensable for subarticular assessment.

**Key strength.** This produces a clinically interpretable answer even if the shortest protocol underperforms. The primary experiment must train matched models for each sequence configuration rather than zeroing a missing sequence only at test time.

**Weakness.** Must be reported per finding, not as one aggregate number — an average across all findings would hide exactly the structure that matters.

**Data required:** already held. All 25 studies sampled contain all three sequences (sagittal T1, sagittal T2, axial T2).

---

## Option 3 — Degeneration phenotypes
### *Does the lumbar spine degenerate as a system rather than level by level?*

**The question.** The labels are multi-label and level-resolved, which supports a question the literature mostly avoids: do findings **co-occur in recognisable patterns**?

**What you would do**
Cluster the cases by their finding patterns and test whether coherent phenotypes emerge — for example multi-level bulge with preserved disc height, single-level extrusion, or facet-dominant degeneration. Then test whether phenotypes differ by age or sex.

**Why it is medically interesting.** It reframes degeneration as a systemic process rather than independent per-level events. This is the same intuition behind the AMOG-Net graph proposal, but stated as a *medical hypothesis about disease behaviour* rather than an architectural choice — which is what makes it publishable in a spine journal.

**Strengths**
- Genuinely novel framing
- Directly motivates the graph-based modelling if that route is taken later

**Weaknesses**
- 299 cases is modest for clustering; findings will need careful statistical support
- Requires a clinician to judge whether the discovered phenotypes are clinically meaningful rather than statistical artefacts

**Data required:** already held. Depends on Phase 0 report extraction being completed first.

---

## Option 4 — Reporting-quality audit
### *How consistent is lumbar MRI reporting at this hospital?*

**The context.** Published inter-observer agreement is only moderate — around κ 0.73 for central canal stenosis but as low as **κ 0.49 for subarticular stenosis**, even among expert readers. No such figure exists for Rizgary.

**What you would report**
- Which findings are consistently reported and which are frequently omitted
- Whether reporting completeness varies with case complexity
- If more than one radiologist contributed: **intra-institutional agreement**

**Strengths**
- Legitimate health-services research
- Directly improves the hospital's own practice
- Low technical effort

**Weaknesses**
- Requires knowing **which radiologist wrote which report** — this may not be recorded
- Politically sensitive: it measures colleagues' performance, so framing and consent matter

**Data required:** reports already held. **Radiologist identity per report is needed and may be missing.**

---

## Option 5 — Reader study
### *Does AI assistance change how radiologists report?*

**The precedent.** Lim et al. (2022) showed deep-learning assistance cut reporting time from 124–274 s to 47–71 s per study, and raised junior radiologists' agreement on four-class foraminal stenosis from κ 0.39 to **κ 0.71**. Agreement was equal or better across every stenosis grading.

**What you would do.** Run the equivalent at Rizgary, with their own radiologists reading with and without the tool, separated by a washout period.

**Why it is the strongest evidence.** It is prospective and measures clinical impact directly rather than inferring it from model metrics. This is the form of evidence that changes practice.

**Strengths**
- Highest-value clinical contribution available
- Rizgary's involvement makes it feasible where it would not be elsewhere

**Weaknesses**
- Requires a **working tool first** — this is an end-of-project contribution, not a starting one
- Requires meaningful radiologist time
- Needs its own study design and likely separate approval

**Data required:** a functioning model, plus radiologist availability.

---

## Recommendation

**Make the revised options 1 and 2 the medical spine of the programme.**

- Both are achievable with data already in hand
- Both matter to Rizgary
- Both target radiology journals where the clinical question leads
- Option 1 can begin immediately and does not depend on any modelling
- Option 2 reuses the sequence experiment already planned, reframed clinically

Keep **option 3** as the scientific centrepiece if the project has the time, and **option 5** as the final contribution once a tool exists.

---

## The one question that would raise the ceiling

Ask the hospital whether they can supply **clinical data alongside the imaging**:

- presenting symptoms and duration
- examination findings
- whether the patient proceeded to surgery
- outcome after treatment

**Why this matters more than anything else on this list.** The single most-cited weakness in the whole lumbar AI literature is that imaging severity correlates poorly with symptoms — anatomical stenosis is demonstrable in many asymptomatic people. Linking imaging findings to *what actually happened to the patient* would be a materially stronger medical contribution than any option above.

As hospital-commissioned research, you are one of very few teams positioned to obtain this. **Worth asking before data collection closes.**

---

## Data facts this rests on (verified 2026-08-23)

| Item | Value |
|------|-------|
| Eligible local imaging case folders currently identified | 294 |
| Radiology reports (.docx) | **299**, one per case, ids 2–300 |
| Spreadsheet rows | 195 — covers only 195 of 299 cases |
| Sequences per study | sagittal T1, sagittal T2, axial T2 — **all three present in 25/25 sampled** |
| Scanner | Siemens Avanto, 1.5 T, single institution |
| Study size | 54–97 slices, ~20 MB per case |

**Three data cautions**

1. The spreadsheet's **case-ID column was removed** in the update. Linkage is now positional. This was tested and `row N = case N` holds with **zero drift** across all 195 rows.
2. The spreadsheet is a **hand transcription with errors** — 14 of 195 ages disagree with the source report. The reports are primary; the spreadsheet is derived.
3. The four-class folder split (`normal / bulge / protrusion / extrusion`) is **lossy and contains at least one error**. Patients have multiple findings at multiple levels — case.87 has bulge, protrusion *and* extrusion at different levels. Case.50 appears in both `extrusion` and `normal` while its record shows no herniation at all. **Do not use the folder names as labels.**

---

## Other decisions also pending

1. **SPIDER dataset** — download and check licence terms? It supplies pixel-level segmentation masks that RSNA does not, and is multi-centre.
2. **Sequencing of work** — report-extraction pipeline first, or de-identification script first?
3. **Chapter 2 retarget** — flagged in a comment above section 2.13 of `thesis/chapter2.tex`. The current research questions (CNN vs Swin; multi- vs single-sequence) follow the MSc brief, which `suggested_methodology.md` recommends replacing. Not actioned; awaiting confirmation of the target degree and student.

---


---

## Committee-facing publication wording

None of the options should promise publication. Student-facing documents should state
**"manuscript prepared for peer-reviewed submission"**. Journal names are planning
targets, not guarantees. Claims such as *first*, *novel*, *population prevalence* or
*clinically deployable* must be re-checked against the literature and the actual sampling
frame immediately before submission.

## Appendix — Phenotype discovery strategy (rescued)

*Preserved from `REALISTIC_DATA_ROADMAP_AND_DECISIONS.md` before that file was deleted.
It is the only substantive idea in it that appears nowhere else, and it resolves the main
weakness of Option 3 above.*

**The problem with Option 3 as written:** 299 cases is a solid sample for descriptive
prevalence (Option 1), but thin for discovering co-occurrence phenotypes by clustering.
Clusters found in 299 cases risk being statistical artefacts.

**The fix — discover on the large cohort, validate on the local one:**

1. Use the **RSNA benchmark (N = 1,975)** to *discover* co-occurrence phenotypes --
   level-coupling, facet-dominant versus disc-dominant degeneration, and so on. Enough
   statistical power for the clustering to mean something.
2. Use the **Rizgary cohort (N = 299)** to *validate regional prevalence* of those
   phenotypes in a Kurdish/Iraqi population.

This gives statistical power and local novelty at the same time, and it turns Option 3
from an underpowered exploratory study into a discovery-then-validation design -- a much
stronger structure for a spine journal.

**Caveat to check before adopting:** RSNA labels stenosis *severity* while the local
reports describe herniation *morphology*. Phenotypes discovered on RSNA are therefore
phenotypes of stenosis co-occurrence, and only the spinal-canal component transfers
cleanly to the local cohort. Scope the validation step accordingly.
