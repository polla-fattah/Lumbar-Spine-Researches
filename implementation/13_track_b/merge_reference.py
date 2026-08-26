#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Merge the report audit with the clinical spreadsheet, recording provenance.

Chapter 3 sec:method-local-reports makes the narrative report primary and the
spreadsheet "a secondary historical transcription aid rather than ... unquestioned
ground truth". This applies that ordering literally:

    report states it            -> report wins, source = "report"
    report silent or ambiguous  -> spreadsheet fills it, source = "spreadsheet"
    the two disagree            -> NEITHER wins, source = "conflict", and the
                                   case goes to a reader

Every row carries where its label came from, so a later analysis can include or
exclude spreadsheet-derived labels and see whether the conclusion moves.

WHAT IS DELIBERATELY NOT DONE
    'ventral theca indentation' correlates with the disagreements and could be
    used to break them, but theca indentation is a DIFFERENT finding: a disc
    bulge can indent the theca without narrowing the canal. Chapter 3
    sec:method-schema-alignment forbids converting one finding into another by
    rule ("No local disc-herniation morphology is converted into a stenosis
    grade by heuristic rule"). It is therefore recorded as a corroborating
    observation for the reader and never used to assign a label.

    python implementation/13_track_b/merge_reference.py --rizgary_dir <DIR>
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.dirname(HERE)
ROOT = os.path.dirname(IMPL)
REP = os.path.join(HERE, "reports")
LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]

SEV_RE = re.compile(r"\b(mild|moderate|severe)\b", re.I)


def sheet_positive(v) -> bool:
    return str(v).strip().lower() not in ("none", "nan", "no", "normal", "")


def sheet_levels(v) -> list:
    """Levels named in a spreadsheet cell: 'L3-4,L4-5 mild' -> [L3-L4, L4-L5]."""
    out = []
    for m in re.finditer(r"[Ll](\d)\s*[-/]\s*(?:[Ll]?(\d)|[Ss](\d))", str(v)):
        a = m.group(1)
        lv = "L{}-L{}".format(a, m.group(2)) if m.group(2) else \
             "L{}-S{}".format(a, m.group(3))
        if lv in LEVELS:
            out.append(lv)
    return sorted(set(out), key=LEVELS.index)


def sheet_severity(v):
    m = SEV_RE.search(str(v))
    return m.group(1).lower() if m else ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rizgary_dir", required=True)
    args = ap.parse_args()

    rep = pd.read_csv(os.path.join(REP, "rizgary_canal_case_level.csv"))
    sh = pd.read_excel(os.path.join(args.rizgary_dir, "research LSS 1.xlsx"))
    sh = sh.rename(columns={"ID": "case_id"})
    canal_col = [c for c in sh.columns if "canal" in str(c).lower()][0]
    theca_col = [c for c in sh.columns if "theca" in str(c).lower()][0]

    j = rep.merge(sh[["case_id", canal_col, theca_col]], on="case_id", how="left")
    j["sheet_pos"] = j[canal_col].map(sheet_positive)
    j["sheet_levels"] = j[canal_col].map(lambda v: ";".join(sheet_levels(v)))
    j["sheet_severity"] = j[canal_col].map(sheet_severity)
    j["theca_positive"] = j[theca_col].map(sheet_positive)

    status, source, sev, lvls, note = [], [], [], [], []
    for r in j.itertuples(index=False):
        rs = r.canal_status
        rep_sev = str(r.canal_severity or "")
        if rs in ("present", "absent"):
            rep_pos = rs == "present"
            if rep_pos == bool(r.sheet_pos):
                status.append(rs)
                source.append("report+sheet agree")
                sev.append(rep_sev or r.sheet_severity)
                lvls.append(r.sheet_levels if not r.level_stated else "")
                note.append("")
            else:
                status.append("conflict")
                source.append("conflict")
                sev.append("")
                lvls.append("")
                note.append("report={} sheet={} theca={}".format(
                    "pos" if rep_pos else "neg",
                    "pos" if r.sheet_pos else "neg",
                    "pos" if r.theca_positive else "neg"))
        else:
            # report silent or ambiguous -> the secondary source fills it
            status.append("present" if r.sheet_pos else "absent")
            source.append("spreadsheet")
            sev.append(r.sheet_severity)
            lvls.append(r.sheet_levels)
            note.append("report was {}".format(rs))

    out = pd.DataFrame({
        "case_id": j.case_id, "canal_status": status, "label_source": source,
        "severity": sev, "levels": lvls,
        "report_status": j.canal_status, "sheet_positive": j.sheet_pos,
        "theca_positive": j.theca_positive, "note": note,
    })
    out.to_csv(os.path.join(REP, "rizgary_canal_reference.csv"), index=False)

    print("=" * 68)
    print("  Merged canal reference  (report primary, spreadsheet secondary)")
    print("=" * 68)
    print("\n  status:")
    for k, v in out.canal_status.value_counts().items():
        print("     {:<10} {:>4}".format(k, int(v)))
    print("\n  provenance:")
    for k, v in out.label_source.value_counts().items():
        print("     {:<20} {:>4}".format(k, int(v)))
    det = out[out.canal_status != "conflict"]
    print("\n  determinate labels: {} of {}".format(len(det), len(out)))
    print("     present {}   absent {}".format(
        int((det.canal_status == "present").sum()),
        int((det.canal_status == "absent").sum())))
    # "nan" arrives as a literal string from the spreadsheet merge and is not a
    # severity; filtering on string length alone would count it as one.
    sev_str = det.severity.fillna("").astype(str).str.strip().str.lower()
    sv = det[~sev_str.isin(["", "nan", "none"])]
    print("     with a severity grade: {}".format(len(sv)))
    for k, v in sv.severity.value_counts().items():
        print("        {:<10} {}".format(k, int(v)))
    print("\n  needing a reader: {} conflicts".format(
        int((out.canal_status == "conflict").sum())))
    print("     {}".format(sorted(out[out.canal_status == "conflict"].case_id.tolist())))
    print("\n  -> {}".format(os.path.relpath(
        os.path.join(REP, "rizgary_canal_reference.csv"), ROOT)))
    print("\n  theca_positive is recorded but NEVER used to assign a label:")
    print("  theca indentation is a different finding, and Chapter 3 forbids")
    print("  converting one local finding into another by rule.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
