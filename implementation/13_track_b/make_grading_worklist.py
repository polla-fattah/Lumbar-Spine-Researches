#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the reader worklist for the Rizgary regrade.

Chapter 3 sec:method-report-verification level 2: "two qualified readers ...
independently review the MRI for the fixed Rizgary test set and assign the same
three-grade target used for the cross-institutional comparison (Normal/Mild,
Moderate, Severe) at L1--L2 through L5--S1 using a common grading sheet. Readers
are blinded to model predictions and, where feasible, to the original routine
report during the first pass."

That blinding requirement shapes the output. Two separate artefacts are written:

    grading_sheet_blinded.csv    case id, level, empty grade column. NOTHING
                                 else -- no extracted label, no report phrase,
                                 no folder name. This is what a reader fills in
                                 on the first pass.

    adjudication_sheet.csv       the same cases WITH the extracted status, the
                                 severity wording and the source phrase. For the
                                 second pass and for disagreement resolution
                                 only. Handing this to a first-pass reader would
                                 defeat the blinding.

Priority ordering follows sec:method-report-verification level 3, which permits
"a stratified subset" when regrading everything is not feasible.

    python implementation/13_track_b/make_grading_worklist.py --rizgary_dir <DIR>
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.dirname(HERE)
ROOT = os.path.dirname(IMPL)
REP = os.path.join(HERE, "reports")
OUT = os.path.join(ROOT, "thesis", "chapter4", "regrade_worklist.md")
LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]


def imaging_ids(rizgary_dir):
    ids = {}
    base = os.path.join(rizgary_dir, "cases")
    for folder in sorted(os.listdir(base)):
        d = os.path.join(base, folder)
        if not os.path.isdir(d):
            continue
        for c in sorted(os.listdir(d)):
            m = re.search(r"case\s*\.*\s*(\d+)", c, re.I)
            if m:
                ids.setdefault(int(m.group(1)), []).append(os.path.join(folder, c))
    return ids


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rizgary_dir", required=True)
    ap.add_argument("--negative_sample", type=int, default=40,
                    help="how many explicit-negative cases to include for "
                         "specificity; 0 = all of them")
    ap.add_argument("--seed", type=int, default=20260826)
    args = ap.parse_args()

    case = pd.read_csv(os.path.join(REP, "rizgary_canal_case_level.csv"))
    cmp_p = os.path.join(REP, "canal_sheet_vs_report.csv")
    cmp_df = pd.read_csv(cmp_p) if os.path.exists(cmp_p) else pd.DataFrame()

    img = imaging_ids(args.rizgary_dir)
    case["has_imaging"] = case.case_id.isin(img)
    ev = case[case.has_imaging].copy()

    disagree = set()
    if len(cmp_df) and "agree" in cmp_df.columns:
        disagree = set(cmp_df[~cmp_df.agree].case_id) & set(ev.case_id)

    sev = ev.canal_severity.fillna("").astype(str)
    ev["priority"] = 4
    ev["reason"] = "explicit negative"
    ev.loc[ev.canal_status == "present", ["priority", "reason"]] = [2, "report asserts stenosis"]
    ev.loc[ev.case_id.isin(disagree), ["priority", "reason"]] = [1, "spreadsheet and report disagree"]
    ev.loc[ev.canal_status.isin(["unresolved", "not_stated"]), ["priority", "reason"]] = \
        [1, "report phrase ambiguous or silent"]

    # priority 3: a stratified sample of explicit negatives, for specificity
    rng = np.random.default_rng(args.seed)
    negs = ev[(ev.priority == 4)].case_id.values
    if args.negative_sample and len(negs) > args.negative_sample:
        pick = set(rng.choice(negs, size=args.negative_sample, replace=False))
    else:
        pick = set(negs)
    ev.loc[ev.case_id.isin(pick), "priority"] = 3
    ev.loc[ev.case_id.isin(pick), "reason"] = "negative, sampled for specificity"

    ev = ev.sort_values(["priority", "case_id"])

    # ---- the two sheets ----------------------------------------------------
    core = ev[ev.priority <= 3]
    blind_rows = []
    for r in core.itertuples(index=False):
        for lv in LEVELS:
            blind_rows.append({
                "case_id": r.case_id, "level": lv,
                "canal_grade": "",           # Normal/Mild | Moderate | Severe
                "not_assessable": "",
                "reader_initials": "", "date": "", "notes": "",
            })
    pd.DataFrame(blind_rows).to_csv(
        os.path.join(REP, "grading_sheet_blinded.csv"), index=False)

    adj = core[["case_id", "priority", "reason", "canal_status",
                "canal_severity", "level_stated"]].copy()
    adj["imaging_path"] = adj.case_id.map(lambda c: " | ".join(img.get(c, [])))
    mat = pd.read_csv(os.path.join(REP, "rizgary_canal_matrix.csv"))
    phrase = (mat[mat.source_phrase.notna() & (mat.source_phrase != "")]
              .groupby("case_id").source_phrase.first())
    adj["report_phrase"] = adj.case_id.map(phrase).fillna("")
    adj.to_csv(os.path.join(REP, "adjudication_sheet.csv"), index=False)

    # ---- the document ------------------------------------------------------
    counts = ev.priority.value_counts().to_dict()
    L = []
    L.append("# Rizgary Regrade — reader worklist")
    L.append("")
    L.append("Generated by `make_grading_worklist.py`. Chapter 3 "
             "`sec:method-report-verification` level 2 specifies two qualified "
             "readers independently assigning Normal/Mild, Moderate or Severe "
             "at L1-L2 through L5-S1, blinded to model predictions and, where "
             "feasible, to the routine report on the first pass.")
    L.append("")
    L.append("## Why a regrade is needed")
    L.append("")
    L.append("The routine reports give a usable *binary* signal but not a usable "
             "*graded* one. Across 195 reports only 5 state \"moderate\" and 9 "
             "state \"severe\" unambiguously, and only 54 attribute canal "
             "stenosis to a named level, leaving 84% of case-by-level cells "
             "unstated. A three-class transfer result computed on that many "
             "graded positives would carry a confidence interval spanning most "
             "of its range.")
    L.append("")
    L.append("## Two sheets, and why they are separate")
    L.append("")
    L.append("| File | Use |")
    L.append("| :--- | :--- |")
    L.append("| `grading_sheet_blinded.csv` | **First pass.** Case id and level "
             "only, with an empty grade column. No extracted label, no report "
             "text, no folder name. |")
    L.append("| `adjudication_sheet.csv` | **Second pass and disagreements "
             "only.** Carries the extracted status, severity wording, source "
             "phrase and imaging path. |")
    L.append("")
    L.append("Handing the adjudication sheet to a first-pass reader would defeat "
             "the blinding Chapter 3 asks for, which is why they are written "
             "separately rather than as one annotated file.")
    L.append("")
    L.append("Note that the morphology folder a case sits in (`normal`, "
             "`disc bulge`, ...) is itself a label and is deliberately omitted "
             "from the blinded sheet.")
    L.append("")

    L.append("## Priority order")
    L.append("")
    L.append("Every case listed has imaging. If the whole set cannot be graded, "
             "work down the priorities — level 3 of the same section permits a "
             "stratified subset.")
    L.append("")
    L.append("| Priority | What | Cases | Why first |")
    L.append("| ---: | :--- | ---: | :--- |")
    L.append("| **1** | Ambiguous, silent, or spreadsheet/report disagreement | "
             "{} | These cannot be resolved from text at all. They need an "
             "image read regardless of what else is done. |".format(
                 counts.get(1, 0)))
    L.append("| **2** | Report asserts stenosis | {} | The scarce class. Every "
             "graded positive materially widens what can be claimed. |".format(
                 counts.get(2, 0)))
    L.append("| **3** | Explicit negatives, sampled | {} | Needed to estimate "
             "specificity; a positives-only set cannot. |".format(
                 counts.get(3, 0)))
    L.append("| 4 | Remaining explicit negatives | {} | Only if time allows. "
             "|".format(counts.get(4, 0)))
    L.append("")
    L.append("**Priorities 1-3 total {} cases**, {} case-by-level rows at five "
             "levels each.".format(len(core), len(core) * 5))
    L.append("")

    for p, title in [(1, "Priority 1 — must be adjudicated"),
                     (2, "Priority 2 — report asserts stenosis"),
                     (3, "Priority 3 — negatives sampled for specificity")]:
        ids = sorted(ev[ev.priority == p].case_id.tolist())
        if not ids:
            continue
        L.append("### {} ({} cases)".format(title, len(ids)))
        L.append("")
        L.append("```")
        for i in range(0, len(ids), 15):
            L.append("  " + "  ".join("{:>4}".format(x) for x in ids[i:i + 15]))
        L.append("```")
        L.append("")
        if p == 1:
            sub = ev[ev.priority == 1]
            L.append("Reason breakdown:")
            L.append("")
            for k, v in sub.reason.value_counts().items():
                L.append("- {}: {}".format(k, v))
            L.append("")

    L.append("## Grading instructions")
    L.append("")
    L.append("1. Grade **central canal stenosis only**. Chapter 3 "
             "`sec:method-schema-alignment` excludes foraminal targets unless "
             "laterality and grade are adequate, and subarticular entirely, "
             "because the routine reports do not support them.")
    L.append("2. Use the same three grades as the RSNA target: **Normal/Mild**, "
             "**Moderate**, **Severe**. Normal and Mild are one class in the "
             "source task, so a mild finding is Normal/Mild — this is the "
             "boundary that makes the two cohorts comparable.")
    L.append("3. Grade every level L1-L2 through L5-S1, including the ones the "
             "report never mentioned. Recovering those cells is much of the "
             "point.")
    L.append("4. If a level cannot be assessed, mark `not_assessable` rather "
             "than guessing a grade.")
    L.append("5. Do not consult the routine report on the first pass.")
    L.append("")
    L.append("Two readers grade independently; disagreements go to a senior "
             "reader. Weighted kappa, exact agreement and the split of one-grade "
             "versus two-grade disagreements are reported, per Chapter 3.")
    L.append("")
    L.append("## Regenerating")
    L.append("")
    L.append("```bash")
    L.append("python implementation/13_track_b/make_grading_worklist.py "
             "--rizgary_dir <DIR>")
    L.append("```")
    L.append("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")

    print("cases with imaging      : {}".format(len(ev)))
    for p in (1, 2, 3, 4):
        print("  priority {}            : {}".format(p, counts.get(p, 0)))
    print("\n  {}".format(os.path.relpath(OUT, ROOT)))
    print("  {}".format(os.path.relpath(
        os.path.join(REP, "grading_sheet_blinded.csv"), ROOT)))
    print("  {}".format(os.path.relpath(
        os.path.join(REP, "adjudication_sheet.csv"), ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
