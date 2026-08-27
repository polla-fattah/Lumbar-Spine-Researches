#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Option 3: Standalone Deterministic Rule-Based Clinical Radiology NLP Extractor
Candidate / Project: MSc Track 3 (Clinical Radiology NLP Benchmark)
Supervisor: Dr. Polla Abdulhamid Fattah

Parses narrative English lumbar MRI radiology reports (.docx files) in `Data/reports/`,
extracts level-resolved findings across 5 lumbar levels (L1-L2, L2-L3, L3-L4, L4-L5, L5-S1),
handles negation context and multi-level list expansions, and outputs a structured matrix.

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

# Pattern aliases for level binding
LEVEL_PATTERNS = {
    "L1-L2": [r"\bl1[-_ /]*2\b", r"\bl1[-_ /]*l2\b"],
    "L2-L3": [r"\bl2[-_ /]*3\b", r"\bl2[-_ /]*l3\b"],
    "L3-L4": [r"\bl3[-_ /]*4\b", r"\bl3[-_ /]*l4\b"],
    "L4-L5": [r"\bl4[-_ /]*5\b", r"\bl4[-_ /]*l5\b"],
    "L5-S1": [r"\bl5[-_ /]*s1\b", r"\bl5[-_ /]*1\b"]
}


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


def extract_patient_demographics(text: str) -> tuple[str, float, str]:
    """Extract Patient ID, Age, and Sex from narrative report text header."""
    case_match = re.search(r"(?:name|case|patient)\s*[:\-]?\s*(case\s*\d+|\w+)", text, re.IGNORECASE)
    case_id = case_match.group(1) if case_match else "UNKNOWN"
    
    age_match = re.search(r"age\s*[:\-]?\s*(\d{1,3})", text, re.IGNORECASE)
    age = float(age_match.group(1)) if age_match else np.nan
    
    sex_match = re.search(r"\b(female|male|f|m)\b", text, re.IGNORECASE)
    sex_str = "Female"
    if sex_match:
        val = sex_match.group(1).lower()
        if val in ["male", "m"]:
            sex_str = "Male"
            
    return case_id, age, sex_str


def parse_report_sentence_findings(text: str) -> dict:
    """Parse report into sentences and extract level-resolved findings."""
    sentences = re.split(r"[.\n;]", text)
    level_findings = {lvl: {"disc_bulge": 0, "disc_protrusion": 0, "disc_extrusion": 0, "canal_stenosis": 0, "facet_arthrosis": 0, "osteophytes": 0} for lvl in LUMBAR_LEVELS}

    for sent in sentences:
        sent_clean = sent.lower().strip()
        if not sent_clean:
            continue
            
        mentioned_levels = []
        for lvl, patterns in LEVEL_PATTERNS.items():
            for pat in patterns:
                if re.search(pat, sent_clean):
                    mentioned_levels.append(lvl)
                    break

        if not mentioned_levels:
            continue

        is_negated = bool(re.search(r"\b(no|normal|without|absent|denies|negative|unremarkable)\b", sent_clean))

        has_bulge = bool(re.search(r"\b(bulge|bulging|circumferential bulge)\b", sent_clean))
        has_protrusion = bool(re.search(r"\b(protrusion|protruding|focal protrusion)\b", sent_clean))
        has_extrusion = bool(re.search(r"\b(extrusion|extruding|sequestration)\b", sent_clean))
        has_stenosis = bool(re.search(r"\b(stenosis|stenotic|canal narrowing|narrowed canal)\b", sent_clean))
        has_facet = bool(re.search(r"\b(facet|arthrosis|facet joint)\b", sent_clean))
        has_osteophyte = bool(re.search(r"\b(osteophyte|osteophytes|spondylosis)\b", sent_clean))

        for lvl in set(mentioned_levels):
            if is_negated:
                if "no spinal canal stenosis" in sent_clean or "no canal stenosis" in sent_clean:
                    level_findings[lvl]["canal_stenosis"] = 0
                if "normal" in sent_clean and not (has_bulge or has_protrusion or has_extrusion):
                    level_findings[lvl]["disc_bulge"] = 0
            else:
                if has_bulge:
                    level_findings[lvl]["disc_bulge"] = 1
                if has_protrusion:
                    level_findings[lvl]["disc_protrusion"] = 1
                if has_extrusion:
                    level_findings[lvl]["disc_extrusion"] = 1
                if has_stenosis and not ("no spinal canal stenosis" in sent_clean):
                    level_findings[lvl]["canal_stenosis"] = 1
                if has_facet:
                    level_findings[lvl]["facet_arthrosis"] = 1
                if has_osteophyte:
                    level_findings[lvl]["osteophytes"] = 1

    return level_findings


def main():
    print("=" * 75)
    print("  Option 3: Deterministic Rule-Based Clinical Radiology NLP Extractor")
    print("  Candidate: MSc Track 3 | Supervisor: Dr. Polla Abdulhamid Fattah")
    print("=" * 75)

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
    reports_dir = os.path.join(base_dir, "Data", "reports")
    results_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "results"))
    os.makedirs(results_dir, exist_ok=True)

    docx_files = glob.glob(os.path.join(reports_dir, "*.docx"))
    print(f"\n[Step 1] Found {len(docx_files)} narrative .docx report files in: {os.path.relpath(reports_dir, base_dir)}")

    if not docx_files:
        print("[FAIL] No .docx report files found.")
        sys.exit(1)

    extracted_records = []

    for file_path in docx_files:
        filename = os.path.basename(file_path)
        raw_text = read_docx_text(file_path)
        
        if not raw_text:
            continue
            
        case_id, age, sex_str = extract_patient_demographics(raw_text)
        level_data = parse_report_sentence_findings(raw_text)

        for lvl in LUMBAR_LEVELS:
            fdata = level_data[lvl]
            extracted_records.append({
                "source_file": filename,
                "case_id": case_id,
                "age": age,
                "sex": sex_str,
                "disc_level": lvl,
                "disc_bulge": fdata["disc_bulge"],
                "disc_protrusion": fdata["disc_protrusion"],
                "disc_extrusion": fdata["disc_extrusion"],
                "canal_stenosis": fdata["canal_stenosis"],
                "facet_arthrosis": fdata["facet_arthrosis"],
                "osteophytes": fdata["osteophytes"]
            })

    matrix_df = pd.DataFrame(extracted_records)
    out_csv = os.path.join(results_dir, "msc3_regex_extracted_matrix.csv")
    matrix_df.to_csv(out_csv, index=False)

    print(f"\n[Step 2] Extraction completed across narrative reports:")
    print(f"   -> Reports Processed : {len(docx_files)}")
    print(f"   -> Level Records     : {len(matrix_df)} ({len(docx_files)} files × 5 levels)")
    print(f"   -> Extracted Bulges  : {matrix_df['disc_bulge'].sum()} level findings")
    print(f"   -> Extracted Stenosis: {matrix_df['canal_stenosis'].sum()} level findings")
    print(f"   -> Output Matrix     : {os.path.relpath(out_csv, base_dir)}")
    print("=" * 75)


if __name__ == "__main__":
    main()
