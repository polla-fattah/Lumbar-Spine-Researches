#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Render the implementation log for Chapter 4 from git history.

Chapter 4 has to say what was built, what was found broken, and what changed as
a result. That record has to come from somewhere that cannot drift: git. This
reads the history, groups it, and pairs each defect with the evidence document
that measures it.

The DEFECTS table below is curated -- a commit subject cannot say how much a bug
cost -- but every figure in it appears in a generated evidence document or a
commit message, and the commit hash is given so it can be checked.

    python implementation/99_audit/make_implementation_log.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
IMPL = os.path.dirname(HERE)
ROOT = os.path.dirname(IMPL)
OUT = os.path.join(ROOT, "thesis", "chapter4", "implementation_log.md")

# Defects found and what each cost. Every number here is reproducible from the
# named evidence document or the named commit.
DEFECTS = [
    ("Fabricated results",
     "Phases 07-13 wrote literal accuracy/F1/QWK values to JSON and rendered "
     "'audit' reports declaring their own gates passed. No model was trained. "
     "The 13 quality gates each read back the constant the preceding script had "
     "just written.",
     "All E1-E7 and Track B numbers were invented",
     "AUDIT_FINDINGS.md"),
    ("E0 trained on noise",
     "train_e0_baselines.py trained one 5-layer CNN on torch.randn images with "
     "torch.randint labels, then reported macro_f1 = acc x 0.97 and "
     "qwk = acc x 1.06.",
     "The baseline was a random-number generator",
     "AUDIT_FINDINGS.md"),
    ("Shuffled-graph control was not a permutation",
     "build_edges(shuffled=True) drew fresh random endpoints instead of "
     "permuting, giving an asymmetric graph with colliding edges and degrees "
     "1-16 against a near-regular 5-7.",
     "E6 would have beaten a structurally weaker control and the gain credited "
     "to anatomy. Biased the central claim toward its own hypothesis",
     "protocol_decisions.md sec.6"),
    ("Evidence mask lost through LayerNorm",
     "The mask was applied once to the GNN input. LayerNorm(0) = beta, so a node "
     "with no image re-acquired a state at layer 1 and broadcast it.",
     "Masked node output norm 2.68 instead of 0; all six graph neighbours "
     "contaminated. Manufactured the information contagion the isolated-lesion "
     "test exists to detect",
     "protocol_decisions.md sec.7"),
    ("Model selection was discarded",
     "The best-validation checkpoint was saved, re-read, asserted non-empty, and "
     "never loaded. load_state_dict appeared nowhere in the trainer.",
     "Every held-out score came from the final epoch, which with no schedule and "
     "no early stopping was the most overfit one",
     "protocol_decisions.md sec.3"),
    ("Test set redrawn per training seed",
     "patient_split was called with the training seed, so a three-seed campaign "
     "drew three different cohorts.",
     "Seeds 0 and 1 shared 12.8% of test patients; 39.5% of the cohort was "
     "tested in one run and trained on in another",
     "protocol_decisions.md sec.1"),
    ("E4 implemented no ACSSL",
     "E4 built the same modules as E3 plus a projection head no forward path "
     "referenced; info_nce was imported and never called.",
     "Core Contribution I would have reported seed noise -- most likely a tight "
     "null, i.e. a false negative against the thesis's own contribution",
     "protocol_decisions.md sec.8"),
    ("E0 read the wrong MRI sequence",
     "forward_target took modality slot 0 unconditionally. RSNA annotates canal "
     "stenosis on sagittal T2 and subarticular on axial T2.",
     "28,963 of 48,657 targets (59.5%) graded from a projected crop of a "
     "sequence no radiologist marked. With random backbone init, cost 0.4650 QWK",
     "e0_baseline.md"),
    ("Backbones randomly initialised",
     "SequenceEncoder defaults to pretrained=False and AMOGNet never overrode it.",
     "A 24M-parameter ResNet-50 trained from scratch on 34k crops",
     "e0_baseline.md"),
    ("Freeze script published random weights",
     "freeze_amog_model.py constructed a fresh AMOGNet, loaded nothing, and "
     "serialised it as AMOG_PUBLIC_FROZEN_v1.0.pt.",
     "Every downstream Track B step would have measured an untrained network "
     "under the project's release name",
     "protocol_decisions.md"),
    ("Calibration never applied",
     "TemperatureScaler was imported and never called; ECE was reported but "
     "never corrected.",
     "E7's 'calibrated heads' claim had no implementation",
     "protocol_decisions.md sec.5"),
    ("ROI crops were pixel-framed",
     "decode_roi cut a fixed 128-pixel box. Chapter 3 sec:method-roi warns "
     "against precisely this.",
     "Physical-mm framing won on every seed: +0.0292 QWK and Severe recall "
     "46.2% -> 57.5%",
     "roi_geometry_ablation.md"),
    ("Series-edge annotations silently dropped",
     "The 2.5D neighbour fallback looked up the centre slice before it had been "
     "cached.",
     "Extraction 99.86% -> 100.00%. Losses concentrated in axial subarticular "
     "targets, so one compartment was removed preferentially",
     "roi_geometry_ablation.md"),
    ("De-identification keyed on a non-unique field",
     "deidentify_dicom.py hashes PatientID to build each pseudonym.",
     "45 distinct PatientID values across 346 Rizgary cases. Would merge ~8 "
     "cases per pseudonym, corrupting patient-level splitting",
     "rizgary_cohort_reconciliation.md"),
]

GROUPS = [
    ("Audit and verification", ("audit(", "test(", "chore(impl)")),
    ("Data layer", ("feat(dataset", "feat(impl): real Track A", "feat(impl): rebuild")),
    ("Model and training", ("fix(impl)", "feat(impl)", "refactor")),
    ("Track B", ("feat(track_b", "refactor(track_b")),
    ("Chapter 4 evidence", ("docs(chapter4", "docs(thesis")),
]


def git(*a):
    try:
        return subprocess.check_output(["git"] + list(a), cwd=ROOT,
                                       stderr=subprocess.DEVNULL).decode(
                                           "utf-8", "replace")
    except Exception:
        return ""


def main() -> int:
    log = git("log", "--pretty=format:%h\x1f%ad\x1f%s", "--date=short",
              "--", "implementation", "thesis")
    commits = []
    for line in log.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            commits.append(tuple(parts))

    L = []
    L.append("# Implementation Log")
    L.append("")
    L.append("*Generated by `make_implementation_log.py` from git history on {}. "
             "The commit list is read from the repository; the defect table is "
             "curated, and every figure in it appears in the linked evidence "
             "document or the named commit.*"
             .format(datetime.now().strftime("%Y-%m-%d")))
    L.append("")
    L.append("Chapter 4 has to state what was built and what changed. This is "
             "that record. It exists because the implementation it describes was "
             "found, at the outset, to be reporting numbers no experiment had "
             "produced — so the provenance of every later claim has to be "
             "checkable rather than asserted.")
    L.append("")

    L.append("## Defects found, and what each one cost")
    L.append("")
    L.append("| # | Defect | Consequence if unfixed | Evidence |")
    L.append("| ---: | :--- | :--- | :--- |")
    for i, (name, _mech, cost, ev) in enumerate(DEFECTS, 1):
        L.append("| {} | **{}** | {} | `{}` |".format(i, name, cost, ev))
    L.append("")
    L.append("### Mechanism of each")
    L.append("")
    for i, (name, mech, _c, _e) in enumerate(DEFECTS, 1):
        L.append("{}. **{}** — {}".format(i, name, mech))
    L.append("")

    L.append("## How they were found")
    L.append("")
    L.append("Worth stating in Chapter 4, because the detection method is itself "
             "a methodological choice:")
    L.append("")
    L.append("- **Reading the code against the specification.** The fabrication, "
             "the disconnected ACSSL head and the discarded checkpoint were all "
             "visible in source once each rung was checked against the Chapter 3 "
             "section it claimed to implement.")
    L.append("- **Behavioural tests that try to falsify a property.** A test "
             "asserting only that code runs would have passed on the fabricated "
             "implementation. The dead projector was found by a gradient probe, "
             "the LayerNorm leak by measuring a masked node's output norm.")
    L.append("- **Two independent implementations of E0.** The standalone "
             "harness and the pipeline disagreed — QWK 0.7500 against 0.2553 on "
             "the same data — which is the only reason the wrong-sequence defect "
             "surfaced. A single implementation would have looked entirely "
             "self-consistent and simply produced a weak ladder.")
    L.append("- **Negative controls.** Permuted labels and permuted graph edges "
             "test whether a result could have arisen without the mechanism "
             "claimed to produce it.")
    L.append("")
    L.append("Two of the defects — the shuffled-graph control and the evidence "
             "leak — biased results *toward* the thesis's own hypotheses. Those "
             "are the ones a results-first review would have been least likely "
             "to catch, because they make the expected outcome more likely, not "
             "less.")
    L.append("")

    L.append("## Change history")
    L.append("")
    L.append("{} commits touching `implementation/` or `thesis/`.".format(
        len(commits)))
    L.append("")
    seen = set()
    for gname, prefixes in GROUPS:
        rows = [c for c in commits
                if any(c[2].startswith(p) for p in prefixes) and c[0] not in seen]
        if not rows:
            continue
        for c in rows:
            seen.add(c[0])
        L.append("### {}".format(gname))
        L.append("")
        L.append("| Commit | Date | Change |")
        L.append("| :--- | :--- | :--- |")
        for h, d, s in rows:
            L.append("| `{}` | {} | {} |".format(h, d, s.replace("|", "\\|")))
        L.append("")
    rest = [c for c in commits if c[0] not in seen]
    if rest:
        L.append("### Other")
        L.append("")
        L.append("| Commit | Date | Change |")
        L.append("| :--- | :--- | :--- |")
        for h, d, s in rest:
            L.append("| `{}` | {} | {} |".format(h, d, s.replace("|", "\\|")))
        L.append("")

    L.append("## Regenerating")
    L.append("")
    L.append("```bash")
    L.append("python implementation/99_audit/make_implementation_log.py")
    L.append("```")
    L.append("")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    print("wrote {}".format(OUT))
    print("{} commits, {} defects recorded".format(len(commits), len(DEFECTS)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
