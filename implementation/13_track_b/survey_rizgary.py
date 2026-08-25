#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Track B, step 0: unpack and characterise the Rizgary cohort.

Chapter 3 sec:method-reconciliation requires a case-flow table before any local
evaluation: for each candidate case, whether a report exists, whether each
sequence exists and is usable, whether DICOM geometry is internally consistent,
and the reason for any exclusion. This script produces the imaging half of it.

PRIVACY
    The raw archives carry unredacted PatientName, PatientBirthDate, PatientSex
    and StudyDate. This script reads headers to COUNT and VALIDATE them and
    never writes an identifier to its output: names are reduced to a salted
    hash prefix purely to test uniqueness, dates to a year, ages to a decade.
    Its output is safe to commit; the unpacked DICOMs are not, and land under
    data/ which is gitignored.

USAGE
    python implementation/13_track_b/survey_rizgary.py --rizgary_dir <DIR>
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
import zipfile
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.dirname(HERE)
ROOT = os.path.dirname(IMPL)
sys.path.append(IMPL)

WORK = os.path.join(ROOT, "data", "rizgary_unpacked")
OUT_DIR = os.path.join(HERE, "reports")

# Folder name -> the morphology label the hospital filed the case under. This is
# NOT a stenosis grade; Chapter 3 sec:method-schema-alignment keeps local
# herniation morphology as a separate task and forbids converting it to an RSNA
# severity by rule.
FOLDER_LABEL = {
    "normal": "normal",
    "disc bulge": "bulge",
    "disc protrusion": "protrusion",
    "dics extrusion": "extrusion",      # spelling as it appears on disk
}


def salted(s: str) -> str:
    return hashlib.sha256(("rizgary_survey_" + str(s)).encode()).hexdigest()[:10]


def classify_series(desc: str, iop) -> str:
    """Map a Siemens series description to the three sequences Chapter 3 needs."""
    d = (desc or "").lower()
    plane = None
    if iop is not None and len(iop) == 6:
        try:
            n = np.cross(np.array(iop[:3], float), np.array(iop[3:], float))
            axis = int(np.argmax(np.abs(n)))
            plane = {0: "sagittal", 1: "coronal", 2: "axial"}[axis]
        except Exception:
            plane = None
    if "sag" in d:
        plane = "sagittal"
    elif "tra" in d or "ax" in d:
        plane = "axial"
    elif "cor" in d:
        plane = "coronal"

    t1 = "t1" in d
    t2 = "t2" in d or "tse" in d
    stir = "stir" in d or "tirm" in d

    if plane == "sagittal" and t1:
        return "sag_t1"
    if plane == "sagittal" and (stir or t2):
        return "sag_t2"
    if plane == "axial" and t2:
        return "ax_t2"
    return "other_{}".format(plane or "unknown")


def unpack(rizgary_dir: str, force: bool = False) -> int:
    n = 0
    for folder, label in FOLDER_LABEL.items():
        src = os.path.join(rizgary_dir, "cases", folder)
        if not os.path.isdir(src):
            continue
        for case in sorted(os.listdir(src)):
            cdir = os.path.join(src, case)
            if not os.path.isdir(cdir):
                continue
            dst = os.path.join(WORK, label, case)
            if os.path.isdir(dst) and not force:
                n += 1
                continue
            os.makedirs(dst, exist_ok=True)
            for f in os.listdir(cdir):
                p = os.path.join(cdir, f)
                if f.lower().endswith(".zip"):
                    try:
                        with zipfile.ZipFile(p) as z:
                            z.extractall(dst)
                    except Exception as e:
                        print("  [warn] {}/{}: {}".format(label, case, e))
                elif os.path.isfile(p) and not f.lower().endswith(".ini"):
                    import shutil
                    shutil.copy2(p, os.path.join(dst, f))
            n += 1
    return n


def survey_case(case_dir: str):
    """Header-only pass over one case. Returns a PHI-free record."""
    import pydicom
    series = collections.defaultdict(list)
    pid_hashes, name_hashes, dates, scanners, ages, sexes = set(), set(), set(), set(), set(), set()
    n_files = n_dicom = 0
    for root, _d, files in os.walk(case_dir):
        for f in files:
            if f.lower().endswith((".zip", ".ini")):
                continue
            n_files += 1
            p = os.path.join(root, f)
            try:
                ds = pydicom.dcmread(p, stop_before_pixels=True)
            except Exception:
                continue
            n_dicom += 1
            uid = str(getattr(ds, "SeriesInstanceUID", "?"))
            series[uid].append(ds)
            pid_hashes.add(salted(getattr(ds, "PatientID", "")))
            name_hashes.add(salted(str(getattr(ds, "PatientName", ""))))
            sd = str(getattr(ds, "StudyDate", ""))
            if len(sd) >= 4:
                dates.add(sd[:4])
            scanners.add("{} {}".format(getattr(ds, "Manufacturer", "?"),
                                        getattr(ds, "ManufacturerModelName", "?")).strip())
            a = str(getattr(ds, "PatientAge", "") or "")
            if a[:3].isdigit():
                ages.add(int(a[:3]) // 10 * 10)
            sexes.add(str(getattr(ds, "PatientSex", "") or "?"))

    kinds = collections.Counter()
    geom_ok = 0
    for uid, inst in series.items():
        d0 = inst[0]
        kind = classify_series(getattr(d0, "SeriesDescription", ""),
                               getattr(d0, "ImageOrientationPatient", None))
        kinds[kind] += 1
        has_geom = all(hasattr(d0, t) for t in
                       ("ImageOrientationPatient", "ImagePositionPatient", "PixelSpacing"))
        if has_geom:
            geom_ok += 1

    return {
        "n_files": n_files, "n_dicom": n_dicom, "n_series": len(series),
        "n_series_with_geometry": geom_ok,
        "distinct_patient_ids": len(pid_hashes),
        "distinct_patient_names": len(name_hashes),
        # kept so cohort-wide uniqueness can be tested; salted, never the value
        "pid_hash": ";".join(sorted(pid_hashes)),
        "name_hash": ";".join(sorted(name_hashes)),
        "study_years": ",".join(sorted(dates)),
        "scanners": ";".join(sorted(x for x in scanners if x and x != "? ?")),
        "age_decades": ",".join(str(a) for a in sorted(ages)),
        "sex": ",".join(sorted(x for x in sexes if x and x != "?")),
        "has_sag_t1": int(kinds.get("sag_t1", 0) > 0),
        "has_sag_t2": int(kinds.get("sag_t2", 0) > 0),
        "has_ax_t2": int(kinds.get("ax_t2", 0) > 0),
        "n_other_series": sum(v for k, v in kinds.items() if k.startswith("other")),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rizgary_dir", required=True)
    ap.add_argument("--force_unpack", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    print("=" * 70)
    print("  Track B step 0: Rizgary cohort survey (headers only, PHI-free output)")
    print("=" * 70)

    print("\n[1/3] unpacking archives -> {}".format(os.path.relpath(WORK, ROOT)))
    n = unpack(args.rizgary_dir, args.force_unpack)
    print("      {} case directories".format(n))

    print("\n[2/3] reading headers")
    rows = []
    for label in sorted(set(FOLDER_LABEL.values())):
        ldir = os.path.join(WORK, label)
        if not os.path.isdir(ldir):
            continue
        cases = sorted(os.listdir(ldir))
        if args.limit:
            cases = cases[:args.limit]
        for i, case in enumerate(cases, 1):
            rec = survey_case(os.path.join(ldir, case))
            rec["case"] = case
            rec["folder_label"] = label
            rows.append(rec)
            if i % 25 == 0:
                print("      {:<12} {}/{}".format(label, i, len(cases)), flush=True)
    df = pd.DataFrame(rows)

    os.makedirs(OUT_DIR, exist_ok=True)
    csv_p = os.path.join(OUT_DIR, "rizgary_case_flow.csv")
    df.to_csv(csv_p, index=False)

    print("\n[3/3] summary")
    print("-" * 70)
    print("  cases surveyed              : {}".format(len(df)))
    print("  cases with readable DICOM   : {}".format(int((df.n_dicom > 0).sum())))
    print("  total DICOM instances       : {:,}".format(int(df.n_dicom.sum())))
    print("  total series                : {:,}".format(int(df.n_series.sum())))
    print()
    print("  by folder label (hospital's morphology filing):")
    for k, v in df.folder_label.value_counts().sort_index().items():
        print("     {:<12} {:>4}".format(k, int(v)))
    print()
    print("  sequence availability (Chapter 3 needs all three):")
    for c, name in [("has_sag_t1", "sagittal T1"), ("has_sag_t2", "sagittal T2/STIR"),
                    ("has_ax_t2", "axial T2")]:
        print("     {:<18} {:>4} / {} cases".format(name, int(df[c].sum()), len(df)))
    all3 = int(((df.has_sag_t1 + df.has_sag_t2 + df.has_ax_t2) == 3).sum())
    print("     {:<18} {:>4} / {} cases".format("all three", all3, len(df)))
    print()
    print("  geometry: series carrying IOP/IPP/PixelSpacing: {:,} / {:,}".format(
        int(df.n_series_with_geometry.sum()), int(df.n_series.sum())))
    print()
    print("  PatientID as a de-identification key:")
    multi = int((df.distinct_patient_ids > 1).sum())
    print("     cases whose files disagree on PatientID: {}".format(multi))
    # Cohort-wide uniqueness, not the sum of per-case counts. deidentify_dicom.py
    # derives the anonymous ID by hashing PatientID, so if PatientID repeats
    # across cases the de-identification silently MERGES those patients into one
    # pseudonym -- which would break patient-level splitting as well as privacy.
    pid_all = collections.Counter(
        h for s_ in df.pid_hash.dropna() for h in str(s_).split(";") if h)
    name_all = collections.Counter(
        h for s_ in df.name_hash.dropna() for h in str(s_).split(";") if h)
    print("     distinct PatientID values in {} cases : {}".format(
        len(df), len(pid_all)))
    print("     distinct PatientName values           : {}".format(len(name_all)))
    dup = sum(1 for v in pid_all.values() if v > 1)
    print("     PatientID values shared by >1 case    : {}".format(dup))
    if len(pid_all) < len(df):
        print("     [!] PatientID is NOT unique per case. Hashing it would map")
        print("         several patients to one pseudonym. Use a per-case key.")
    if len(name_all) < len(df):
        print("     [!] PatientName is not unique either ({} for {} cases)."
              .format(len(name_all), len(df)))
    print()
    print("  scanners:")
    sc = collections.Counter()
    for s in df.scanners.dropna():
        for x in str(s).split(";"):
            if x:
                sc[x] += 1
    for k, v in sc.most_common(6):
        print("     {:<34} {:>4}".format(k[:34], v))
    print()
    print("  study years: {}".format(sorted({y for s in df.study_years.dropna()
                                             for y in str(s).split(",") if y})))
    print("-" * 70)
    print("  case-flow table -> {}".format(os.path.relpath(csv_p, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
