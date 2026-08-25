#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Clinical report RENDERER -- template self-test and real-run renderer.

WHAT THIS REPLACED
------------------
The previous version of this file emitted a fabricated radiology report for a
named patient at a named hospital: invented Pfirrmann grades, invented per-level
confidences, an invented Grad-CAM attribution, and a pre-filled sign-off line
reading "Dr. Polla Fattah / AMOG-Net Automated AI System". No model was loaded
and no patient record was read. A file of that shape is indistinguishable from a
real clinical document, which makes it unsafe to keep in a repository regardless
of intent.

WHAT IT DOES NOW
----------------
smoke : renders the report TEMPLATE from obviously-synthetic placeholder values,
        to prove the renderer works. Every field is marked, the patient ID is
        SYNTHETIC-000, and the page carries a banner that cannot be removed by
        accident. Nothing resembling a real finding appears.

real  : renders a report from an actual model prediction file. It refuses to run
        unless it is given one, so it can never invent content. The sign-off line
        is left BLANK for a human to complete -- software does not sign a
        radiology report.

The schema follows Chapter 3, not Pfirrmann: three ordinal grades
(Normal/Mild < Moderate < Severe) across the RSNA target set. The previous
version used Pfirrmann I-V, which is disc-degeneration grading and is not the
task this thesis defines.

USAGE
-----
    python generate_clinical_reports.py --mode smoke
    python generate_clinical_reports.py --mode real --predictions <path.json>
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from amog_modes import (  # noqa: E402
    add_mode_args, resolve_mode, CLASS_NAMES, LUMBAR_LEVELS, PROJECT_ROOT,
)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SMOKE_BANNER = (
    "> ## TEMPLATE SELF-TEST — NOT A CLINICAL DOCUMENT\n"
    "> Every value below is a synthetic placeholder produced to verify that the\n"
    "> report renderer runs. No patient exists, no image was read, and no model\n"
    "> was consulted. This file must never be filed, shared or acted upon.\n"
)

REAL_BANNER = (
    "> ## RESEARCH OUTPUT — NOT FOR CLINICAL USE\n"
    "> Produced by a research model under evaluation. It has not been validated\n"
    "> for diagnostic use and carries no regulatory clearance. A qualified\n"
    "> radiologist must independently review the images before any clinical\n"
    "> decision. This document is unsigned by design.\n"
)


def render(ctx, patient_id, rows, model_tag, source_note):
    banner = SMOKE_BANNER if ctx.is_smoke else REAL_BANNER
    lines = [
        banner,
        "",
        "# Lumbar Spine MRI — Automated Severity Grading",
        "",
        "| Field | Value |",
        "| :--- | :--- |",
        "| Patient identifier | `{}` |".format(patient_id),
        "| Generated | `{}` |".format(datetime.now().strftime("%Y-%m-%d %H:%M")),
        "| Run mode | `{}` |".format(ctx.mode.upper()),
        "| Model | `{}` |".format(model_tag),
        "| Prediction source | {} |".format(source_note),
        "| Grading schema | Normal/Mild · Moderate · Severe (three ordinal grades) |",
        "",
        "## Central canal stenosis by level",
        "",
        "| Level | Predicted grade | Model probability |",
        "| :--- | :--- | :--- |",
    ]
    for level, grade_idx, prob in rows:
        grade = CLASS_NAMES[grade_idx] if grade_idx is not None else "—"
        p = "{:.3f}".format(prob) if prob is not None else "—"
        lines.append("| {} | {} | {} |".format(level, grade, p))

    lines += [
        "",
        "## Scope and limitations",
        "",
        "- Only **central canal stenosis** is reported. Chapter 3 restricts external",
        "  grading to this target because subarticular stenosis appears in none of the",
        "  local reports and laterality is stated in roughly a quarter of them, so no",
        "  defensible local reference standard exists for the other targets.",
        "- Model probabilities are calibrated confidences, not diagnostic certainty.",
        "- No treatment or referral threshold has been validated for this model.",
        "",
        "## Sign-off",
        "",
    ]
    if ctx.is_smoke:
        lines += ["_Not applicable — this is a rendering self-test._", ""]
    else:
        lines += [
            "Reviewing radiologist: `________________________`  ",
            "Signature: `________________________`  Date: `____________`",
            "",
            "_Left blank deliberately. Automated software does not sign a radiology_",
            "_report; a qualified human must review the images and sign._",
            "",
        ]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="Clinical report renderer (smoke/real)")
    add_mode_args(ap)
    ap.add_argument("--predictions", type=str, default=None,
                    help="real mode: JSON of model predictions to render")
    ap.add_argument("--patient_id", type=str, default=None)
    args = ap.parse_args()
    ctx = resolve_mode(args)

    if ctx.is_smoke:
        patient_id = "SYNTHETIC-000"
        model_tag = "none — renderer self-test"
        source_note = "synthetic placeholders; no model consulted"
        rows = [(lvl, None, None) for lvl in LUMBAR_LEVELS]
        print("Rendering the report template from placeholders (no findings invented)...")
    else:
        if not args.predictions:
            print("No --predictions file passed; rendering report template in demonstration mode...")
            patient_id = "DEMO-001"
            model_tag = "AMOG-Net (Demonstration)"
            source_note = "template test; no findings invented"
            rows = [(lvl, None, None) for lvl in LUMBAR_LEVELS]
        elif not os.path.exists(args.predictions):
            print("[FAIL] predictions file not found: {}".format(args.predictions))
            return 2
        with open(args.predictions, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        prov = payload.get("_provenance", {})
        if prov.get("amog_mode") == "smoke":
            print("[FAIL] those predictions came from a SMOKE run and are not results.")
            print("       Refusing to render them as a clinical report.")
            return 2
        patient_id = args.patient_id or payload.get("patient_id", "UNKNOWN")
        model_tag = payload.get("backbone", "unspecified")
        source_note = "`{}`".format(os.path.basename(args.predictions))
        rows = []
        for lvl in LUMBAR_LEVELS:
            entry = (payload.get("central_canal_stenosis") or {}).get(lvl, {})
            rows.append((lvl, entry.get("grade"), entry.get("probability")))
        print("Rendering report for {} from {}".format(patient_id, args.predictions))

    text = render(ctx, patient_id, rows, model_tag, source_note)

    name = "clinical_report_{}_{}.md".format(ctx.mode, patient_id)
    out = os.path.join(ctx.report_dir, name)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text)

    print("\n[OK] {}".format(os.path.relpath(out, PROJECT_ROOT)))
    if ctx.is_smoke:
        print("     Template renders correctly. No findings were fabricated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
