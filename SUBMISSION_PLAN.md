# Submission plan

Written 2026-08-28. Five tasks between here and a compilable, coherent thesis.
Each has a definition of done that can be checked, not asserted. Status is
updated in place as work completes, so this file is the record of what actually
happened rather than what was intended.

| # | Task | Done when | Status |
| :-: | :-- | :-- | :-- |
| 1 | LaTeX pre-flight validation | A checker runs over all five chapters and reports zero errors in column counts, escaping, citations and environment nesting | **DONE** |
| 2 | Compile the thesis | `thesis.pdf` builds from `thesis.tex` with Chapters 4 and 5 included | **BLOCKED** -- needs Polla to accept an installer prompt, or another machine |
| 3 | Chapter 3 to past tense | 18 prospective constructions converted; 3 `[TO CONFIRM]`/`[TO RECORD]` fields filled from the executed protocol | **DONE** |
| 4 | Abstract | Written against the final seven-seed numbers, in `thesis.tex` | **DONE** |
| 5 | Localisation finding into Chapter 5 | RQ4's limitation states that it cannot be interpreted without a localisation control, with the measurement | **DONE** |

---

## 1. LaTeX pre-flight validation

**Why.** Roughly a thousand lines of new LaTeX exist across Chapters 4 and 5,
with seven tables and thirty-five cross-references, and none of it has ever been
through a compiler. Balanced braces and resolving references were already
checked; neither catches the errors that actually break a build.

**What is checked.** Column count of every row against its own `tabular`
specification. Unescaped `%`, `&`, `_`, `#` outside mathematics and outside
verbatim. Every `\cite` key against the bibliography. Environment nesting.
Stray control characters from the shell-escaping incidents earlier in this work.

**Result, stated honestly.** `implementation/99_audit/latex_preflight.py`
reports **zero issues across all five chapters**. It found no real defects in
the new LaTeX.

What it did find was four defects in *itself*. The first version reported 268
issues, every one a false positive. They were caught because Chapters 2 and 3
have compiled -- `chapter2.pdf` and `chapter3.pdf` exist -- so any issue
reported there is wrong by construction, and those files became the calibration
set. The four checker bugs were: a column-specification regex that could not
handle the nested braces in `p{1.1cm}`; an assumption that a table row occupies
one source line, which fails when a `p{}` column wraps; treating `#1` in
`\newcommand` as an unescaped hash; and masking only inline `$...$` maths, so
every subscript in Chapter 3's equations was flagged.

The honest summary is that the new chapters were already clean and the checker
had to be made trustworthy before that statement meant anything. It remains
useful as ongoing insurance, and the calibration approach -- refuse to believe a
checker that is noisy on known-good input -- is the transferable part.

An earlier draft of this plan recorded "found and fixed 6 real defects". That
was written before the checker was run and was not true. It is corrected here
rather than quietly deleted.

## 2. Compile the thesis

**Why.** Everything above is inference about what a compiler would do. Only a
compiler settles it.

**Result: BLOCKED, and the blocker is a decision rather than a technical
obstacle.** `winget` is available (v1.29.290), but installing MiKTeX through it
requires accepting the Microsoft Store *Terms of Transaction* and consenting to
send the machine's geographic region to a backend service. That is an agreement
to accept on Polla's behalf, and it was not accepted. Smart App Control is also
enforcing on this machine and has already blocked newly installed executables
once in this project.

So the thesis remains unbuilt. Section 6 gives the exact commands. Three ways
forward, in order of preference:

1. Polla runs `winget install MiKTeX.MiKTeX` and accepts the prompt, then the
   build commands in section 6.
2. Build on any other machine with a TeX distribution, or in Overleaf, which
   needs only the `thesis/` directory and the `.bib` file.
3. Leave it, and rely on the pre-flight checker -- which is explicitly a
   substitute, not a replacement.

Option 3 is not adequate for a submission. The document must be built and read
before anyone submits it.

## 3. Chapter 3 to past tense

**Why.** Chapter 3's own header instructs it: \"After implementation, convert
prospective statements to past tense and replace all [TO CONFIRM] / [TO RECORD]
fields with the executed protocol and observed cohort counts. Do not silently
fill them from intention.\"

**Constraint.** Converting tense is not licence to change what the chapter
committed to. Every edit changes only the grammatical aspect or fills a field
with a measured value. Hypotheses, comparisons and thresholds are untouched, as
Chapter 1 requires.

**Result.** Six prospective passages converted and four `[TO RECORD]` fields
filled with measured values: cohort counts (1,974 studies, 48,657 targets,
1,381/296/297 patient split), the partitioning scheme, effective resampling
spacing (60 mm field of view at 128 px, 0.469 mm per pixel), backbone selection,
the executed environment (Python 3.14.2, PyTorch 2.11 CUDA 12.8, RTX 5090),
modality-dropout probability, optimiser and regularisation settings, the
training configuration and selection criterion, and the bootstrap replicate
count.

**What was deliberately NOT converted, and why this mattered.** Not every
future-tense sentence in Chapter 3 describes work that happened. RQ4 was never
executed, so statements about the Rizgary cohort, zero-shot transfer and local
adaptation stay prospective -- H4 among them. Converting those would assert that
experiments were run which were not, which is the single thing this conversion
had to avoid. The three remaining `[TO CONFIRM]` fields are ethics items -- IRB
approval number, consent basis, and whether external GPU processing is permitted
-- which are institutional facts rather than measurements and are left for
Polla. Filling them from inference is what the chapter's own instruction
forbids.

The inclusion/exclusion table statement was changed to say exactly what is true:
the overlays and checklist exist over 60 studies and 1,474 targets, and the
reader adjudication that completes the table is outstanding.

## 4. Abstract

**Why.** None exists, and it needs the final numbers, which now do.

**Result.** Written into `thesis.tex` front matter against the seven-seed
campaign: the system result and its clinical-error improvement, the three
comparisons surviving correction, the rejected mechanisms with their equivalence
bounds rather than as bare nulls, and the attribution mechanism. It ends on the
three contributions, including that three analyses were overturned by their own
controls.

Two stale items surfaced while doing this and were fixed. The title page still
declared "This document contains Chapters 2 and 3" and described a chapter
counter advance that has since been removed; it now describes all five chapters
and states that RQ4 was not executed. And the build recipe in section 6 of this
plan omitted `--output-safechars`, which `thesis.tex` documents as required --
without it biber emits decomposed Unicode accents that `inputenc` cannot
typeset, and the build fails on any cited author with an accented name.

## 5. Localisation finding into Chapter 5

**Why.** RQ4 currently reads as an absence -- \"not executed, blocked on
adjudication and de-identification\". The measurement of 2026-08-28 makes a
stronger statement available: RQ4 could not have been *interpreted* without a
localisation control, because grading on derived coordinates costs 22.9% of
performance, an order of magnitude more than any effect the thesis measures.

**Result.** Both sections rewritten. The limitation now states that a transfer
result obtained on derived coordinates would be *uninterpretable* rather than
merely degraded, because domain shift and localisation error would be confounded
and the localisation term alone is an order of magnitude larger than any effect
the thesis measures. The future-work section quantifies the gap instead of
naming it, and lists the three routes forward in increasing cost.

---

## 6. Compiling elsewhere

The thesis has never been built. To do so on a machine with a toolchain:

```
cd thesis
pdflatex thesis
biber --output-safechars thesis
pdflatex thesis
pdflatex thesis
```

`--output-safechars` is required, not cosmetic. `thesis.tex` documents why:
biber decodes LaTeX accent macros from the `.bib` into *decomposed* Unicode, so
a cedilla arrives as a standalone combining character that `inputenc` cannot
typeset, and the build fails on any cited author with an accented name. An
earlier draft of this plan omitted the flag.

`thesis.tex` uses `docmute`, so each chapter keeps its own preamble and is also
compilable standalone by the same sequence with `chapter4` or `chapter5` in
place of `thesis`.

Expect first-build warnings for undefined references until `biber` has run and
`pdflatex` has been repeated. Genuine errors would be reported as such.

## 7. Not in this plan

Deliberately excluded, and why.

- **Reader tasks.** 1,474 ROI quality-control rows, 16 Rizgary label conflicts,
  9 geometry exclusion candidates. These need a radiologist, not an engineer.
- **RQ4 execution.** Blocked on those adjudications, on de-identification, and
  now on the localisation control the 2026-08-28 measurement shows to be
  necessary.
- **The clinical system.** `SYSTEM_DESIGN.md` covers it. Post-submission, and a
  student project.
- **Predictive localisation.** A separate paper. The measurement in
  `derived_coordinate_cost.md` is the strongest motivation for it that exists.
