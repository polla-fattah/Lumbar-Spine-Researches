# Project state, decisions and blockers

Written 2026-08-27. This is the file to re-read first after a break. It records
what is done, what was decided and why, what is waiting on a decision, and the
traps that have already cost time once.

Evidence for every claim lives in `thesis/chapter4/*.md`. Numbers are generated,
not typed.

---

## 1. Where things stand

**Running now:** seven-seed campaign (`run_ladder.py --profile full --seeds
42,43,44,45,46,47,48`), log at `/tmp/ladder_7seed.log`. 40 new runs, ~22 min
each. Skips the 30 that already exist. On completion it regenerates
`data/reports/chapter4_{results,comparisons}.csv` and `chapter4_tables.md`
automatically.

**Complete and committed:**

| Item | Where |
| :-- | :-- |
| Three-seed campaign, 30/30, 0 failures | `thesis/chapter4/ladder_results_full.md` |
| Controlled input ablation (Ch3 promised it, was never run) | `thesis/chapter4/input_ablation.md` |
| Grad-CAM attribution + figures | `thesis/chapter4/attribution{,_figures}.md` |
| Chapter 4 draft | `thesis/chapter4.tex` |
| Chapter 1 placeholders filled | `thesis/chapter1.tex` |
| Viva defence narrative | `thesis/viva_defence.md` |
| Reframing proposal | `thesis/chapter4/reframing_proposal.md` |
| DICOM to NIfTI converter | `implementation/dicom_to_nifti.py` |
| ROI quality control, whole cohort | `thesis/chapter4/roi_quality_control.md` |
| 100 two-plane review sheets, 20 studies x 5 levels | `data/reports/roi_qc/` |
| 113 behavioural tests, all passing | `implementation/99_audit/test_components.py` |

**Headline result:** E7 - E0 = +0.0172 QWK [+0.0064, +0.0285], every seed, the
only pre-specified comparison surviving FDR.

**Per research question:** RQ1 partly (typed edges yes, anatomical topology no),
RQ2 no, RQ3 mechanism yes / benefit no, RQ4 not executed, RQ5 yes.

---

## 2. Decisions taken, with the reasoning

Recorded so they are not silently re-litigated later.

**Predictive localisation is a separate paper, not a thesis chapter.**
Chapter 3 is locked and there is under three months. It needs new methodology,
new validation and 2-3 months of writing. It reuses this infrastructure, so it
will be fast afterwards, and the Rizgary cohort with its reports is its natural
external-validation partner.

**The thesis sells the evaluation, not three architectural components.**
Chapter 1 already called them *proposed* contributions and already carried a
placeholder instructing that failures be reported as negative findings. Filled
as D1 (a verified working system), D2 (a controlled ablation protocol), D3 (the
finding that anatomical priors do not pay at this scale, with a mechanism).

**Hypotheses, research questions and problem statement are NOT rewritten.**
Chapter 1 forbids it in its own words, and the git history dates every
specification. This is also the safe option, not the risky one.

**Contribution III is claimed narrowly.** "Relational typing carries
information; anatomical adjacency does not." An external proposal advised
claiming that beating the homogeneous graph validates anatomical topology --
that is exactly what the degree-preserving shuffle control refutes, and it is
the most damaging single sentence available in the defence.

**Never say "viva-hardened" aloud.** It is a comment in the LaTeX source.
Saying it announces that failure was anticipated and is being managed.

**Clinical system storage: SQLite**, one file, results plus paths to rendered
images. Images on disk, paths in the table.

**Patient identity: assign fresh IDs**, and keep a linkage file mapping new ID
to original study, stored separately and access-controlled. Without it, a case
can never be re-linked to its report or its row in `research LSS 1.xlsx`.

**Model updates: old results stay frozen.** A "re-evaluate" button writes a new
row with the new model hash rather than overwriting. Both versions coexist; the
clinician chooses when to move.

**Do not install anything into the main Python environment while the campaign
runs.** `run_ladder.py` spawns a fresh subprocess per run, so a torch downgrade
mid-campaign would break every remaining run.

---

## 3. Waiting on a decision from Polla

1. **DONE 2026-08-27.** Tier 1 QC viewer built; correspondence verified over
   9,542 projections at 93.6% within one slice, dev partition 94%. RQ2's null
   is therefore interpretable. Outstanding: a reader must complete
   `data/reports/roi_qc/roi_qc_checklist.csv` to produce the
   inclusion/exclusion table Chapter 3 promised, and adjudicate the nine
   studies in `geometry_exclusion_candidates.csv`.
2. **QC sample: random or enriched?** Random gives an unbiased geometry error
   rate; enriched finds problems faster but yields no rate. Recommendation:
   random, with a stratified supplement.
3. **Ask the two students for their TotalSpineSeg code and configuration?**
   Their cohort is very likely the same Rizgary data (`data/rizgary_unpacked/`
   is organised as bulge / extrusion / normal / protrusion -- their exact four
   classes). Their pipeline may be directly reusable.
4. **CAM peak for the viewer: extend to E7 (~2 h) or take grades from E7 and
   the crosshair from E2?** The latter is defensible but must be stated.
5. **Which cases for radiologist review?** All 297 test patients is too many to
   review. A stratified sample -- severe cases, disagreements, confident errors
   -- is far more informative.

---

## 4. Blockers, by severity

**RQ4 / E8 not executed.** Three separate obstacles, not one:
- 16 Rizgary cases have conflicts between report-derived and spreadsheet labels,
  awaiting reader adjudication. IDs: 6, 25, 53, 54, 60, 64, 82, 125, 149, 157,
  162, 170, 172, 179, 193, 195.
- De-identification is not solved (below).
- **Rizgary has no localisation at all.** The manifest carries `disc_level` but
  no x/y coordinates, so zero-shot transfer is blocked on missing model *input*,
  not merely on admin. This was under-reported earlier and is the largest of the
  three.

**`deidentify_dicom.py` is not fit for use.** It keys on `PatientID`, which has
45 distinct values across 346 cases -- a site or scanner code, not a patient
identifier. Using it would merge roughly eight patients per pseudonym.

**PHI exposure, measured on 379 sampled files:** PatientName, PatientID,
BirthDate, Sex, Age, StudyDate present in 100%; InstitutionName 99%; private
vendor tags 100%; three Enhanced SR (structured report) objects found. The
`BurnedInAnnotation` tag is **absent in every file**, which means the scanner
declared nothing -- not that the pixels are clean. Burned-in text is the real
exposure and needs an OCR or visual sweep. Use `dicognito` or RSNA CTP; do not
hand-roll.

**Smart App Control is enforcing on this machine**
(`VerifiedAndReputablePolicyState = 1`). It blocks newly installed unsigned
compiled extensions **in newly created venvs** -- both under Temp and under the
user profile. The **main environment is unaffected**: `blosc2`, the exact
package that failed in the venv, installs and imports fine there. So
TotalSpineSeg can run natively; install into the main environment after the
campaign, with torch pinned. WSL is not installed. Disabling Smart App Control
is a system security setting and was not attempted.

**TotalSpineSeg is unvalidated on this data.** Its 99% labelling accuracy is its
own published figure on its own benchmark. The students almost certainly quoted
the paper rather than measuring it locally. RSNA is where to measure it, because
ground-truth coordinates exist there.

**No LaTeX toolchain on this machine.** `chapter4.tex` has never been compiled.
Braces and environments balance and all `\ref` resolve, but it needs a real
build before anyone trusts it.

**Chapter 3 specifies the ladder as E0-E8.** Only E0-E7 were executed; E8 is the
complete system under external transfer, i.e. RQ4. Recorded in Chapter 4.

---

## 5. Why the QC viewer matters more than it looks

It is not primarily a figure generator. Contribution I rests entirely on
"DICOM-defined anatomical correspondence", and **there is currently no
data-grounded evidence that this correspondence is correct.** `geometry.py`
records that the previous implementation never read `ImageOrientationPatient`
and substituted textbook cosines chosen by a substring match on the series
description, and that its validation -- a 3D round-trip returning 0.00000000 mm
-- was vacuous, because inverting a matrix returns the original point whatever
the matrix contains.

So RQ2's rejection carries an unexamined assumption: that ACSSL was given a fair
test. Three outcomes:

- Correspondence checks out -> RQ2's null becomes properly interpretable and much
  harder to attack. Likely, and a real strengthening.
- Correspondence is systematically off -> RQ2 is uninterpretable and must be
  reported as such. Bad news, far better found now.
- Left/right orientation wrong anywhere -> also bears on the lateralisation
  observation and may explain the unexplained +12 px foraminal offset.

The honest validation is external, not a round-trip: different conditions at the
same level are annotated on *different* sequences (canal on sagittal T2,
subarticular on axial T2), so project one into the other's plane and check it
lands a plausible distance from that plane's own annotations.

---

## 6. The clinical system: fast vs not fast

**Buildable in about two days:** FastAPI backend, drag-and-drop frontend, job
queue, SQLite schema, and the chain wired end to end -- `dicom_to_nifti` ->
TotalSpineSeg -> model -> two-plane render. A working demo.

**Does not compress, and none of it is typing speed:**

- *De-identification verification.* Wiring `dicognito` is thirty minutes.
  Verifying nothing leaks means sampling pixels, auditing private tags across
  vendors, handling the SR objects. The failure mode is a data breach.
- *Whether TotalSpineSeg works on this data.* Empirical, not codeable.
- *The level to 25-target mapping.* Untested. May reveal that foraminal offsets
  vary too much between patients to derive from disc centres at all.
- *Real PACS exports.* RSNA is curated; hospital exports are not. Multi-frame,
  missing tags, odd orientations, compressed transfer syntaxes. Each a
  twenty-minute fix, discovered one at a time over weeks.
- *Radiologist feedback cycles.* Runs at their availability.
- *Ethics approval, hospital IT security review, hardware inside the network.*
  Not doable at any speed by anyone here.

**Architecture note that removes most of the difficulty:** localisation and
grading are separate stages with a coordinate CSV between them -- the same shape
as `train_label_coordinates.csv`. TotalSpineSeg is preprocessing, never part of
the training loop or of inference, so it need not share an environment with the
model. A human clicking five disc levels writes the same CSV, which is what makes
the semi-automatic tier possible.

**Important framing correction:** neither the baseline nor the proposal performs
localisation. Both are *given* coordinates. A viewer offering "localisation by
baseline vs by our proposal" is not possible; localisation would come from
TotalSpineSeg identically for both. What differs is the **grading**.

---

## 7. Traps that have already cost time

- **Shell heredocs eat one level of backslash.** This corrupted `chapter1.tex`
  three times -- `\ref` became CR+"ef", `\textbf` became TAB+"extbf", `\begin`
  became BSP+"egin", leaving an `\end{description}` with no opener. Use the Write
  or Edit tool for anything containing backslashes, never a heredoc.
- **Per-seed bootstrap intervals reverse sign.** E4 vs E3 was +0.0270 (p=0.000)
  on seed 42 and -0.0234 (p=0.000) on seed 43. Always use
  `amog_stats.paired_bootstrap_diff_seeds`.
- **Any routing claim needs the E1 control.** E2's 5/5 agreement between gate
  weights and intervention looked like proof until E1, which has no router,
  scored the same.
- **Grad-CAM must hook the encoder that read the target.** Hooking `encoders[0]`
  reads the sagittal T1 encoder on axially-graded targets and reports the
  opposite sign.
- **Never validate a geometric transform by round-trip.** See section 5.
- **All three of the above initially pointed toward the hypothesis under test.**

---

## 8. Suggested order of work

1. Campaign finishes -> refresh every `[3-SEED]` figure in `chapter4.tex`.
2. Install TotalSpineSeg into the main environment, torch pinned; run against
   the four converted studies in the scratchpad; measure landmark error in mm
   against RSNA coordinates. ~2 h. Decides whether localisation is viable.
3. Tier 1 QC viewer. ~1 day. Discharges the Ch3 commitment and tests the
   correspondence underpinning RQ2.
4. Compile `chapter4.tex` somewhere with a LaTeX toolchain.
5. Everything else -- clinical system, localisation paper, Rizgary transfer --
   is post-submission or a student project.
