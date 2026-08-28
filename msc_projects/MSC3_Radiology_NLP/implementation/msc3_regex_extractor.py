#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Option 3: Deterministic Rule-Based Clinical Radiology NLP Extractor (Re-architected)
Candidate / Project: MSc Track 3 (Clinical Radiology NLP Benchmark)
Supervisor: Dr. Polla Abdulhamid Fattah

Features & Scientific Improvements:
 1. 4-State Semantic Encoding:
    - 1  : PRESENT
    - 0  : EXPLICITLY_NEGATED
    - 2  : UNCERTAIN / HEDGED
    - -1 : NOT_MENTIONED (Distinguishes unmentioned levels from normal/negated levels)
 2. Clause-Bound Negation Scoping:
    - Splits sentences on clause boundary delimiters ('but', 'however', ', although', ';')
      so negation triggers do not leak across clauses.
 3. Exact Level-Distance Binding:
    - Restricts level binding to target clauses containing exact level tokens (L1-L2 to L5-S1).
 4. Strict Demographics Resolution:
    - Matches patient cases with master Excel registry to extract exact age/sex without defaulting missing sex to Female.

Output:
    msc_projects/MSC3_Radiology_NLP/results/msc3_regex_extracted_matrix.csv
"""

import os
import sys
import re
import glob
import zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import numpy as np

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

LUMBAR_LEVELS = ["L1-L2", "L2-L3", "L3-L4", "L4-L5", "L5-S1"]

LEVEL_PATTERNS = {
    "L1-L2": [r"\bl1[-_ /]*2\b", r"\bl1[-_ /]*l2\b"],
    "L2-L3": [r"\bl2[-_ /]*3\b", r"\bl2[-_ /]*l3\b"],
    "L3-L4": [r"\bl3[-_ /]*4\b", r"\bl3[-_ /]*l4\b"],
    "L4-L5": [r"\bl4[-_ /]*5\b", r"\bl4[-_ /]*l5\b"],
    "L5-S1": [r"\bl5[-_ /]*s1\b", r"\bl5[-_ /]*1\b"]
}

# Clause boundary splitters
CLAUSE_BOUNDARIES = r"(?:\bbut\b|\bhowever\b|\balthough\b|\bnevertheless\b|;|:)"


def read_docx_text(file_path: str) -> str:
    """Extract raw text from a .docx file using standard library zipfile & XML parsing."""
    try:
        with zipfile.ZipFile(file_path) as z:
            xml_content = z.read("word/document.xml")
            tree = ET.fromstring(xml_content)
            text = "".join(tree.itertext())
            return re.sub(r"\s+", " ", text).strip()
    except Exception:
        return ""


def resolve_demographics_from_excel(excel_df: pd.DataFrame, case_idx: int) -> tuple[float, str]:
    """Resolve exact patient age and sex from master Excel registry."""
    if case_idx < len(excel_df):
        row = excel_df.iloc[case_idx]
        raw_age = row.get("age ", row.get("age", np.nan))
        try:
            age = float(str(raw_age).strip())
            age = age if (10 <= age <= 100) else np.nan
        except (ValueError, TypeError):
            age = np.nan
            
        raw_gender = str(row.get("gender", "")).lower().strip()
        if "female" in raw_gender:
            sex_str = "Female"
        elif "male" in raw_gender:
            sex_str = "Male"
        else:
            sex_str = "UNKNOWN"
        return age, sex_str
    return np.nan, "UNKNOWN"


def parse_report_clause_findings(text: str) -> dict:
    """
    Parse report text into clause blocks and extract level-bound 4-state findings.
    States: 1 (PRESENT), 0 (NEGATED), 2 (UNCERTAIN), -1 (NOT_MENTIONED)
    """
    # Initialize all findings for all levels to NOT_MENTIONED (-1)
    level_findings = {
        lvl: {
            "disc_bulge": -1,
            "disc_protrusion": -1,
            "disc_extrusion": -1,
            "canal_stenosis": -1,
            "facet_arthrosis": -1,
            "osteophytes": -1
        }
        for lvl in LUMBAR_LEVELS
    }

    # Split document into sentences
    sentences = re.split(r"[.\n]", text)

    for sent in sentences:
        sent_clean = sent.strip()
        if not sent_clean:
            continue
            
        # Split sentence into clause blocks on conjunction boundaries
        clauses = re.split(CLAUSE_BOUNDARIES, sent_clean, flags=re.IGNORECASE)

        for clause in clauses:
            clause_clean = clause.lower().strip()
            if not clause_clean:
                continue

            # Identify levels mentioned in THIS specific clause
            clause_levels = []
            for lvl, patterns in LEVEL_PATTERNS.items():
                for pat in patterns:
                    if re.search(pat, clause_clean):
                        clause_levels.append(lvl)
                        break

            if not clause_levels:
                continue

            # Check clause-bound negation
            is_negated = bool(re.search(r"\b(no|normal|without|absent|denies|negative|unremarkable|free of)\b", clause_clean))
            is_uncertain = bool(re.search(r"\b(possible|suspected|equivocal|questionable)\b", clause_clean))

            # Detect specific pathologies in clause
            has_bulge = bool(re.search(r"\b(bulge|bulging|circumferential bulge)\b", clause_clean))
            has_protrusion = bool(re.search(r"\b(protrusion|protruding|focal protrusion)\b", clause_clean))
            has_extrusion = bool(re.search(r"\b(extrusion|extruding|sequestration)\b", clause_clean))
            has_stenosis = bool(re.search(r"\b(spinal canal stenosis|canal stenosis|canal narrowing|narrowed dural sac)\b", clause_clean))
            has_facet = bool(re.search(r"\b(facet joint arthrosis|facet arthrosis|facet joint hypertrophy|facet hypertrophy)\b", clause_clean))
            has_osteophyte = bool(re.search(r"\b(osteophyte|osteophytes|spondylosis)\b", clause_clean))

            for lvl in set(clause_levels):
                if is_negated:
                    if "no spinal canal stenosis" in clause_clean or "no canal stenosis" in clause_clean or "normal canal" in clause_clean:
                        level_findings[lvl]["canal_stenosis"] = 0
                    if "normal" in clause_clean or "no disc" in clause_clean:
                        if level_findings[lvl]["disc_bulge"] == -1:
                            level_findings[lvl]["disc_bulge"] = 0
                        if level_findings[lvl]["disc_protrusion"] == -1:
                            level_findings[lvl]["disc_protrusion"] = 0
                else:
                    status = 2 if is_uncertain else 1
                    if has_bulge:
                        level_findings[lvl]["disc_bulge"] = status
                    if has_protrusion:
                        level_findings[lvl]["disc_protrusion"] = status
                    if has_extrusion:
                        level_findings[lvl]["disc_extrusion"] = status
                    if has_stenosis and not ("no canal stenosis" in clause_clean or "no spinal canal stenosis" in clause_clean):
                        level_findings[lvl]["canal_stenosis"] = status
                    if has_facet:
                        level_findings[lvl]["facet_arthrosis"] = status
                    if has_osteophyte:
                        level_findings[lvl]["osteophytes"] = status

    # Binary reduction for evaluation standard: PRESENT (1) vs ABSENT (0)
    # NOT_MENTIONED (-1) and EXPLICITLY_NEGATED (0) resolve to 0 in binary mode
    return level_findings


def main():
    print("=" * 75)
    print("  Option 3: Deterministic Rule-Based Clinical Radiology NLP Extractor")
    print("  Re-architected Engine: Clause Scoping, 4-State Encoding & Demographics Fix")
    print("  Candidate: MSc Track 3 | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    reports_dir = os.path.join(base_dir, "Data", "reports")
    excel_path = os.path.join(base_dir, "Data", "research LSS 1.xlsx")
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(results_dir, exist_ok=True)

    excel_df = pd.read_excel(excel_path) if os.path.exists(excel_path) else pd.DataFrame()

    docx_files = sorted(glob.glob(os.path.join(reports_dir, "*.docx")))
    print(f"\n[Step 1] Loaded {len(docx_files)} narrative report files.")
    print(f"   -> Master Registry Ingested: {len(excel_df)} patient cases")

    if not docx_files:
        print("[FAIL] No .docx files found.")
        sys.exit(1)

    extracted_records = []

    for idx, file_path in enumerate(docx_files):
        filename = os.path.basename(file_path)
        raw_text = read_docx_text(file_path)
        
        if not raw_text:
            continue
            
        case_id = f"RIZGARY_P_{idx+1:03d}"
        age, sex_str = resolve_demographics_from_excel(excel_df, idx)
        level_data = parse_report_clause_findings(raw_text)

        for lvl in LUMBAR_LEVELS:
            fdata = level_data[lvl]
            extracted_records.append({
                "source_file": filename,
                "case_id": case_id,
                "age": age,
                "sex": sex_str,
                "disc_level": lvl,
                # Binary mapping for standard evaluation (1 = Present, 0 = Absent/Not Mentioned)
                "disc_bulge": 1 if fdata["disc_bulge"] == 1 else 0,
                "disc_protrusion": 1 if fdata["disc_protrusion"] == 1 else 0,
                "disc_extrusion": 1 if fdata["disc_extrusion"] == 1 else 0,
                "canal_stenosis": 1 if fdata["canal_stenosis"] == 1 else 0,
                "facet_arthrosis": 1 if fdata["facet_arthrosis"] == 1 else 0,
                "osteophytes": 1 if fdata["osteophytes"] == 1 else 0,
                # 4-State raw codes for advanced semantics
                "raw_state_bulge": fdata["disc_bulge"],
                "raw_state_stenosis": fdata["canal_stenosis"]
            })

    matrix_df = pd.DataFrame(extracted_records)
    out_csv = os.path.join(results_dir, "msc3_regex_extracted_matrix.csv")
    matrix_df.to_csv(out_csv, index=False)

    females = (matrix_df.groupby("case_id")["sex"].first() == "Female").sum()
    males = (matrix_df.groupby("case_id")["sex"].first() == "Male").sum()

    print(f"\n[Step 2] Clause-Bound Extraction Completed Successfully:")
    print(f"   -> Reports Processed : {len(docx_files)}")
    print(f"   -> Level Records     : {len(matrix_df)} ({len(docx_files)} files × 5 levels)")
    print(f"   -> Demographics Audit: {females} Females, {males} Males (NO DEFAULTING)")
    print(f"   -> Extracted Bulges  : {matrix_df['disc_bulge'].sum()} level findings")
    print(f"   -> Extracted Stenosis: {matrix_df['canal_stenosis'].sum()} level findings")
    print(f"   -> Output Matrix     : {os.path.relpath(out_csv, base_dir)}")
    print("=" * 75)


if __name__ == "__main__":
    main()
