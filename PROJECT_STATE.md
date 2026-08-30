# Project state, decisions and blockers

Rewritten 2026-08-29. **Read this first after a break.** It records what is
done, what was decided and why, what is waiting on Polla, and the traps that
have already cost time once.

Every number here is generated, not typed. Evidence lives in
`thesis/chapter4/*.md` and `data/reports/`. Regenerate with
`python implementation/make_figures.py`.

---

## 1. Where things stand

**Nothing is running.** All approved experiments are complete.

**The thesis compiles.** 203 pages, 0 errors, 0 undefined references, five
figures embedded. Build with `cd thesis && ./build.sh`. MiKTeX is installed at
`%LOCALAPPDATA%\Programs\MiKTeX`.

**The campaign:** ten ladder configurations x seven seeds (42-48), plus five
control and variant arms, all on the frozen patient-level test partition of 297
studies and 7,310 scored targets.

### What survives correction

Primary endpoint QWK, nine pre-specified contrasts, BH-FDR **and**
Holm-Bonferroni agreeing on all nine:

| comparison | delta | seeds | p_FDR |
| :-- | --: | :-- | --: |
| E7 vs E0, full system | +0.0177 | 7/7 | <0.001 |
| E6 vs E5, relation-specific banks | +0.0093 | 7/7 | 0.009 |
| E7 vs E6, ordinal + cost | +0.0082 | 7/7 | 0.009 |

Everything else is null, bounded near 1% of baseline.

### What the controls established

The three anatomical mechanisms the thesis proposed do not work, and each was
killed by a matched control rather than by absence of evidence:

- **RQ1 graph.** Typed edges beat a homogeneous graph on every seed. But an
  endpoint shuffle matches them (+0.0020, 4/7) and a **type shuffle** matches
  them too (-0.0022, 4/7, the control ahead on point estimate). Three weight
  banks beat one; neither the anatomy of the topology nor the meaning of the
  relations is load-bearing.
- **RQ2 ACSSL.** Null on accuracy (+0.0030, 4/7), robustness (-0.0061, 4/7) and
  attention. Modality dropout, a one-line augmentation, reduces sequence
  reliance **twelve times more** (-0.0758, 7/7).
- **RQ3 routing.** Gate pattern replicates on every run, but a router-free model
  reproduces it under intervention, so it belongs to the dataset.
- **RQ5 ordinal + cost.** Real (+0.0082, 7/7, largest effect in the study) but
  **neither component works alone**: ordinal alone +0.0042 (5/7), cost alone
  **-0.0032** (2/7). 87% is interaction, t=1.57, not established at n=7.

### Effect sizes are clinically negligible, and the thesis says so

Counted on test predictions: the full system grades **42 more of 7,310** targets
correctly than baseline, one per seven patients. Typed edges rewrite 792
predictions to net **+13**. Section 4.x states this explicitly. The contribution
is the evaluation protocol, not the accuracy.

---

## 2. Waiting on Polla

**Twelve placeholders print in bold in the PDF.** Everything else answerable has
been cleared.

- `thesis.tex`: candidate's registered name, awarding institution and
  department, degree
- `chapter1.tex` and `chapter3.tex`, three each: ethics/IRB approval reference
  and date, consent or waiver basis, whether external cloud/GPU is permitted
- `chapter1.tex`: final institutional thesis structure; Rizgary case-flow counts
  (belongs to MSC1, blocked on de-identification)
- `chapter1.tex`: pre-submission novelty re-check -- **left deliberately**, it is
  a real outstanding task

**One discrepancy I could not resolve.** Chapter 1 says the local inventory holds
299 narrative reports and 294 matched cases. On disk `rizgary/reports` has 195
`.docx` and the case folders resolve to 297 study numbers. MSC1 also says 299.
Either reports live somewhere I have not looked, or the figure is stale. Not
overwritten.

---

## 3. Outstanding work, in priority order

1. **Hierarchical bootstrap** (both reviews). Resample seeds and patients jointly
   for total inferential uncertainty. Moderate work, no new runs.
2. **Adaptive 3-to-7 seed disclosure.** Cheap, and both reviews ask for it.
3. **ROI reader QC pass.** Needs a radiologist. 300 sheets and a checklist are
   rendered and waiting in `data/reports/roi_qc/`.
4. **Adjudicate the nine geometry-exclusion studies.** Also a radiologist.
5. **Retitling.** Both reviews suggest the title oversells what survived. This is
   an institutional decision, not a technical one.

**Deliberately NOT doing before viva:** the cache-invalidating fixes (physical
slice-neighbour selection, series-level normalisation, cross-sequence geometry
for oblique acquisitions, an untouched final holdout). Each forces a full 70-run
re-execution and a re-check of every number in five chapters, for a small
expected effect on conclusions that are already nulls. They belong in future
work as stated limitations.

---

## 4. Traps that have already cost time

**Shell heredocs eat backslashes.** This has now corrupted LaTeX and broken
regexes on at least five separate occasions in one session, including after
being written down. Use the Write/Edit tools for anything containing
backslashes. `python - <<'PYEOF'` is not safe either -- the quoting does not
protect `\%` or `\label`.

**Prose numbers go stale when tables regenerate.** Five separate batches of
stale figures were found and fixed. The fix is structural: tables are now
emitted as `.tex` fragments by `make_figures.py` and `\input` into the chapters.
`table_steps` additionally warns if the ladder steps stop telescoping to E7-E0.
Any number still typed into prose is a future defect.

**A clean compile is not a correct document.** The build reported 0 errors while
the calibration table had two bolded "best" cells and a 91.9pt overfull box.
Render the pages and look at them: `pdftoppm -png -r 110 -f N -l N thesis.pdf`.

**Under-powered results point toward the hypothesis.** Three seeds produced a
clean 3/3 robustness effect at 72% of modality dropout's; seven seeds gave
4/7 and t=-0.40. The per-seed bootstrap produced opposite significant signs on
different seeds. Run the seeds before writing.

**A flag can silently destroy the thing it tests.** `--force` regenerated the
shared ACSSL representation that E4-vs-E3 exists to hold fixed. `cost_weight`
0.25 and 1.0 would both have tagged as plain `E7` and overwritten the canonical
runs. Check tagging before launching a sweep.

**Checkers can lie.** `latex_preflight` reported 268 false positives until it was
calibrated against chapters known to compile. A test written as
`not equal(...) or True` passes unconditionally.

---

## 5. Key commands

```bash
cd thesis && ./build.sh                              # build the thesis
python implementation/make_figures.py                # regenerate figures/tables
python implementation/99_audit/test_components.py    # 122 behavioural tests
python implementation/99_audit/check_refs.py         # refs/inputs/graphics
python implementation/99_audit/latex_preflight.py    # common LaTeX faults
```

---

## 6. Reviews

`thesisReview.md` (round 1 and 2) and `thesisReview2.md`. Round 2's verdict:
*"a clearly defensible doctoral contribution... I would be comfortable sending
this to viva"* once the type-shuffle is done (it is), Chapter 3 is faithful to
the implementation (it is), the statistics get a final pass, and the
placeholders go.

**Treat `thesisReview2.md` with care.** It describes the code accurately but
fabricates operational detail: it directs running a `run_ladder.py
--type-shuffled` flag that does not exist, cites the wrong table numbers, and
asks for removal of a header that is a LaTeX comment and never renders. Verify
its findings before acting; most hold, none of its commands do.
