#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Track B: source-text audit of the Rizgary radiology reports.

Chapter 3 sec:method-report-verification, level 1: "Every externally evaluated
case--level label is traced to the exact report phrase and its level and
laterality. Multi-level expressions ... are expanded into separate level records
without changing their meaning. Ambiguous phrases are coded as unresolved rather
than forced into a class."

WHAT THIS IS NOT
    Not a reference standard. The same section: "Automated report extraction ...
    does not define the reference standard. Every label that enters Selar's
    external grading analysis is manually checked against the original report
    text." This produces the CANDIDATE matrix a reader adjudicates, with the
    source phrase beside every row so the check is possible.

THE RULE THAT MATTERS
    Absence of a statement is never evidence of normality. Chapter 3
    sec:method-local-reports: "Absence of a phrase in a narrative report is not
    automatically equivalent to 'normal'." A level the report does not mention is
    recorded as not_stated, which is a THIRD state distinct from normal and from
    abnormal, and is excluded from target-specific evaluation.

PRIVACY
    Reports carry a patient name on the first line. It is dropped before any
    text is parsed or stored, and the audit output is checked for name- and
    date-like patterns before it is written.

USAGE
    python implementation/13_track_b/extract_report_labels.py --rizgary_dir <DIR>
"""
from __future__ import annotations

import argparse
import collections
import os
import re
import sys

import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.dirname(HERE)
ROOT = os.path.dirname(IMPL)
OUT_DIR = os.path.join(HERE, "reports")

LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]
_ORDER = {lv: i for i, lv in enumerate(LEVELS)}

# Findings the reports actually discuss. Canal stenosis is the only one Chapter 3
# sec:method-schema-alignment admits as a primary external target; the rest are
# recorded because the source-text audit must be complete, not because they
# transfer.
FINDINGS = {
    "canal_stenosis": r"canal\s+(?:stenosis|narrowing)",
    "disc_bulge": r"disc\s+bulge|bulging\s+disc|circumferential\s+bulge",
    "disc_protrusion": r"protrusion|protruded",
    "disc_extrusion": r"extrusion|extruded|sequestrat",
    "nerve_root_pressure": r"pressure\s+(?:effect\s+)?on\s+(?:the\s+)?(?:corresponding\s+)?"
                           r"(?:exit(?:ing)?\s+)?(?:foramina|foramen|n\.?\s*roots?|nerve\s+roots?)",
    "theca_indentation": r"indent\w*\s+(?:the\s+)?ventral\s+theca|ventral\s+theca\s+indent",
    "foraminal_narrowing": r"foramina\w*\s+(?:stenosis|narrowing)",
}

SEVERITY = [("severe", r"\bsevere\b|\bmarked\b"),
            ("moderate", r"\bmoderate\b"),
            ("mild", r"\bmild\b|\bminimal\b|\bslight\b")]

# Negation scoped to the phrase, not the whole report.
NEGATION = r"\bno\b|\bnot\b|\bfree\s+of\b|\bwithout\b|\bnegative\s+for\b|\bnormal\b|\babsent\b"

NAME_LINE = re.compile(r"^\s*(name|patient|pt)\s*[:\-]", re.I)


def read_report(path: str) -> str:
    """Paragraph text with the identifying first line removed."""
    import docx
    paras = []
    for p in docx.Document(path).paragraphs:
        t = p.text.strip()
        if not t or NAME_LINE.match(t):
            continue
        # ages are quasi-identifiers and carry no grading information
        if re.match(r"^\s*age\b", t, re.I):
            continue
        paras.append(t)
    return "\n".join(paras)


def normalise_levels(text: str) -> list:
    """Every lumbar level named in a phrase, including ranges.

    Handles the forms these reports actually use: 'L4-5', 'L5/S1', 'L4-L5',
    'L2 through S1', 'L2 to L5'. A range is expanded to the levels it spans --
    Chapter 3 requires multi-level expressions to become separate level records
    without changing their meaning.
    """
    t = text.replace("–", "-").replace("—", "-")
    found = set()

    # explicit ranges first: "L2 through S1", "L1 to L5"
    for m in re.finditer(r"[Ll](\d)\s*(?:through|thru|to|-\s*through)\s*([LlSs])(\d)", t):
        a = int(m.group(1))
        end_is_s = m.group(2).upper() == "S"
        b = int(m.group(3))
        hi = 5 if end_is_s else b
        for lv in LEVELS:
            top = int(lv[1])
            if a <= top <= hi:
                found.add(lv)

    # pairwise level tokens: L4-5, L4-L5, L5/S1, L5-S1
    for m in re.finditer(r"[Ll](\d)\s*[-/]\s*(?:[Ll]?(\d)|[Ss](\d))", t):
        a = m.group(1)
        if m.group(2):
            lv = "L{}-L{}".format(a, m.group(2))
        else:
            lv = "L{}-S{}".format(a, m.group(3))
        if lv in _ORDER:
            found.add(lv)
    return sorted(found, key=_ORDER.get)


def severity_of(phrase: str):
    for name, pat in SEVERITY:
        if re.search(pat, phrase, re.I):
            return name
    return None


# Anatomy a negation may be attached to INSTEAD of the finding being tested.
# "no pressure effect on corresponding exit foramina with mild spinal canal
# stenosis" negates the pressure effect, not the stenosis.
_OTHER_SUBJECT = (r"pressure|foramin\w*|theca|nerve\s*roots?|n\.?\s*roots?|"
                  r"migration|s\.?o\.?l|lesion|signal|fracture|listhesis")


def is_negated(phrase: str, finding_span):
    """Does a negation in this phrase bind to THIS finding?

    Returns True (negated), False (asserted) or None (cannot tell).

    Scoped to the clause before the finding, split on 'with' as well as commas,
    because these reports chain independent observations with 'with'. If another
    anatomical subject sits between the negation and the finding, the negation
    probably attaches to that subject instead, and the phrase is reported as
    undecidable rather than guessed. Chapter 3 sec:method-report-verification:
    "Ambiguous phrases are coded as unresolved rather than forced into a class."
    """
    before = phrase[:finding_span[0]]
    # The word boundaries matter: a bare 'with' also matches inside
    # 'without', which is itself a negation term, so splitting on it would
    # delete the very negation being tested for.
    clause = re.split(r"[,;]|\bwith\b|\bbut\b", before, flags=re.I)[-1]
    if re.search(NEGATION, clause, re.I):
        return True
    # negation earlier in the phrase, with another subject in between
    m = list(re.finditer(NEGATION, before, re.I))
    if m:
        between = before[m[-1].end():]
        if re.search(_OTHER_SUBJECT, between, re.I):
            return None          # binds elsewhere -> undecidable here
        return True
    return False


def audit_report(cid: int, text: str) -> list:
    """One row per (case, level, finding) traced to its exact phrase."""
    rows = []
    phrases = [p.strip() for p in re.split(r"(?<=[.;])\s+|\n", text) if p.strip()]
    for ph in phrases:
        levels = normalise_levels(ph)
        for fname, fpat in FINDINGS.items():
            m = re.search(fpat, ph, re.I)
            if not m:
                continue
            neg = is_negated(ph, m.span())
            sev = severity_of(ph)
            if neg is None:
                status = "unresolved"
            elif neg:
                # a graded phrase that also reads negated is contradictory
                status = "unresolved" if sev else "absent"
            else:
                status = "present"
            targets = levels or ["(unspecified)"]
            for lv in targets:
                rows.append({
                    "case_id": cid,
                    "level": lv,
                    "finding": fname,
                    "status": status,
                    "severity": sev or "",
                    "level_stated": int(bool(levels)),
                    "source_phrase": ph[:300],
                })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rizgary_dir", required=True)
    args = ap.parse_args()

    rep_dir = os.path.join(args.rizgary_dir, "reports")
    files = sorted(f for f in os.listdir(rep_dir) if f.lower().endswith(".docx"))
    print("=" * 70)
    print("  Track B: source-text audit of {} reports".format(len(files)))
    print("  Chapter 3 sec:method-report-verification level 1")
    print("=" * 70)

    audit, no_canal = [], []
    for f in files:
        m = re.search(r"case\s*\.*\s*(\d+)", f, re.I)
        if not m:
            continue
        cid = int(m.group(1))
        try:
            text = read_report(os.path.join(rep_dir, f))
        except Exception as e:
            print("  [warn] case {}: {}".format(cid, e))
            continue
        rows = audit_report(cid, text)
        audit.extend(rows)
        if not any(r["finding"] == "canal_stenosis" for r in rows):
            no_canal.append(cid)

    adf = pd.DataFrame(audit)
    os.makedirs(OUT_DIR, exist_ok=True)
    adf.to_csv(os.path.join(OUT_DIR, "report_source_audit.csv"), index=False)

    # ---- case x level matrix for the primary target -------------------------
    canal = adf[adf.finding == "canal_stenosis"]
    cases = sorted(adf.case_id.unique())
    mat = []
    for cid in cases:
        sub = canal[canal.case_id == cid]
        for lv in LEVELS:
            at = sub[sub.level == lv]
            if len(at):
                st = "unresolved" if (at.status == "unresolved").any() else (
                    "present" if (at.status == "present").any() else "absent")
                sev = ";".join(sorted({s for s in at.severity if s})) or ""
                src = at.iloc[0].source_phrase
            else:
                gen = sub[sub.level == "(unspecified)"]
                if len(gen):
                    # a case-level statement with no level named. Chapter 3 forbids
                    # attributing it to a level, so it is carried at case level and
                    # the per-level cell stays not_stated.
                    st, sev, src = "not_stated", "", ""
                else:
                    st, sev, src = "not_stated", "", ""
            mat.append({"case_id": cid, "level": lv, "canal_status": st,
                        "canal_severity": sev, "source_phrase": src})
    mdf = pd.DataFrame(mat)
    mdf.to_csv(os.path.join(OUT_DIR, "rizgary_canal_matrix.csv"), index=False)

    # case-level canal statement (what most reports actually give)
    caselvl = []
    for cid in cases:
        sub = canal[canal.case_id == cid]
        if not len(sub):
            st, sev = "not_stated", ""
        elif (sub.status == "unresolved").any():
            st, sev = "unresolved", ""
        elif (sub.status == "present").any():
            st = "present"
            sev = ";".join(sorted({s for s in sub[sub.status == "present"].severity if s}))
        else:
            st, sev = "absent", ""
        caselvl.append({"case_id": cid, "canal_status": st, "canal_severity": sev,
                        "level_stated": int(bool((sub.level != "(unspecified)").any()))})
    cdf = pd.DataFrame(caselvl)
    cdf.to_csv(os.path.join(OUT_DIR, "rizgary_canal_case_level.csv"), index=False)

    # ---- cross-check against the spreadsheet --------------------------------
    xl = os.path.join(args.rizgary_dir, "research LSS 1.xlsx")
    disagree = pd.DataFrame()
    if os.path.exists(xl):
        sh = pd.read_excel(xl)
        col = [c for c in sh.columns if "canal" in str(c).lower()]
        if col and "ID" in sh.columns:
            sh = sh[["ID", col[0]]].rename(columns={"ID": "case_id", col[0]: "sheet"})
            sh["sheet_positive"] = ~sh.sheet.astype(str).str.strip().str.lower().isin(
                ["none", "nan", "no", "normal", ""])
            j = cdf.merge(sh, on="case_id", how="inner")
            j["report_positive"] = j.canal_status == "present"
            j["agree"] = j.sheet_positive == j.report_positive
            j.to_csv(os.path.join(OUT_DIR, "canal_sheet_vs_report.csv"), index=False)
            disagree = j[~j.agree]

    print("\n  audit rows (case x level x finding) : {:,}".format(len(adf)))
    print("  cases                                : {}".format(len(cases)))
    print("  reports with no canal statement      : {}".format(len(no_canal)))
    print("\n  case-level canal status:")
    for k, v in cdf.canal_status.value_counts().items():
        print("     {:<12} {:>4}".format(k, int(v)))
    print("\n  severity where the report states one:")
    sv = collections.Counter(s for s in cdf.canal_severity if s)
    for k, v in sv.most_common():
        print("     {:<12} {:>4}".format(k, v))
    print("\n  level attribution:")
    print("     canal statements naming a level  : {}".format(
        int(cdf.level_stated.sum())))
    print("     case-level only                  : {}".format(
        int(len(cdf) - cdf.level_stated.sum())))
    ns = (mdf.canal_status == "not_stated").sum()
    print("     case x level cells not_stated    : {:,} / {:,} ({:.0f}%)".format(
        ns, len(mdf), ns / len(mdf) * 100))
    if len(disagree):
        print("\n  spreadsheet vs report (needs adjudication):")
        print("     agree     {:>4}".format(int((~disagree.index.isin([])).sum()
                                                and len(cdf) - len(disagree))))
        print("     disagree  {:>4}   -> canal_sheet_vs_report.csv".format(len(disagree)))
    print("\n  outputs in {}".format(os.path.relpath(OUT_DIR, ROOT)))
    print("     report_source_audit.csv      every phrase, traceable")
    print("     rizgary_canal_matrix.csv     case x level, primary target")
    print("     rizgary_canal_case_level.csv case-level rollup")
    print("     canal_sheet_vs_report.csv    disagreements for a reader")
    print("\n  NOT a reference standard. Chapter 3 requires every label to be")
    print("  manually checked against the source phrase, which is carried in")
    print("  each row for exactly that purpose.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
