#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Adversarial integrity check for the AMOG-Net implementation.

WHY THIS EXISTS
---------------
The 13 "Quality Gates" in this repository cannot fail. Each one reads a JSON file
that the script under test wrote moments earlier and asserts that the constant
inside it exceeds a threshold. The value being checked and the value being written
are the same value, so every gate passes by construction.

This checker is different in one respect that matters: it was written by a party
other than the one being checked, and it is designed to FAIL on the code as it
currently stands. A verification that cannot fail verifies nothing.

It answers one question: *does the reported number trace back to a computation on
real data, or was it typed in?*

WHAT IT CHECKS
--------------
  A. Fabricated metrics   -- results assigned as literals rather than measured
  B. Synthetic input      -- models fitted to torch.randn instead of images
  C. Empty training loops -- epochs with no backward()/optimizer.step()
  D. Derived metrics      -- F1/kappa computed by multiplying accuracy
  E. Checkpoint substance -- .pt files that are not real state_dicts, or whose
                             parameter count contradicts the claimed architecture
  F. Methodology drift    -- graph node count and class count vs chapter3.tex
  G. Pixel provenance     -- whether any image is ever actually opened
  H. Output hygiene       -- required directories exist and are kept separate

EXIT CODES
----------
  0  all checks passed
  1  one or more integrity violations found
  2  could not run (missing dependency or unreadable tree)

USAGE
-----
  python implementation/99_audit/verify_integrity.py
  python implementation/99_audit/verify_integrity.py --json report.json
  python implementation/99_audit/verify_integrity.py --create-dirs
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

IMPL_DIR = os.path.dirname(os.path.abspath(__file__))
IMPL_ROOT = os.path.dirname(IMPL_DIR)
PROJECT_ROOT = os.path.dirname(IMPL_ROOT)
DATA_DIR = os.path.join(PROJECT_ROOT, "data")

# Directories every run must be able to write into, kept separate by purpose so
# that a training artefact can never be mistaken for a test artefact.
REQUIRED_OUTPUT_DIRS = [
    os.path.join(DATA_DIR, "manifests"),    # cohort tables built from source data
    os.path.join(DATA_DIR, "splits"),       # frozen patient-level split ID lists
    os.path.join(DATA_DIR, "derived"),      # intermediate computed artefacts
    os.path.join(DATA_DIR, "checkpoints"),  # model weights
    os.path.join(DATA_DIR, "logs"),         # STAGE 1: per-epoch training history
    os.path.join(DATA_DIR, "reports"),      # STAGE 2: held-out test results only
    os.path.join(DATA_DIR, "governance"),   # de-identification and audit records
]

# Names that denote a reported result. Assigning a float literal to one of these
# is the signature of a fabricated metric.
METRIC_NAMES = {
    "test_acc", "test_accuracy", "test_loss", "test_f1", "test_qwk", "test_ece",
    "train_acc", "train_loss", "val_acc", "val_loss", "val_f1",
    "macro_f1", "qwk", "qwk_kappa", "ece", "ece_error", "accuracy", "auroc",
    "auprc", "brier", "kappa", "sensitivity", "specificity", "recall", "precision",
}

SKIP_DIR_PARTS = {"venv", "__pycache__", ".git", "site-packages", "99_audit"}


class Findings:
    def __init__(self):
        self.items = []

    def add(self, check, severity, path, line, message):
        rel = os.path.relpath(path, PROJECT_ROOT) if path else ""
        self.items.append({
            "check": check, "severity": severity,
            "file": rel.replace("\\", "/"), "line": line, "message": message,
        })

    @property
    def critical(self):
        return [i for i in self.items if i["severity"] == "CRITICAL"]

    @property
    def warnings(self):
        return [i for i in self.items if i["severity"] == "WARNING"]


def iter_python_files():
    for root, dirs, files in os.walk(IMPL_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIR_PARTS]
        for fn in sorted(files):
            if fn.endswith(".py"):
                yield os.path.join(root, fn)


def read(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


# ---------------------------------------------------------------- checks A-D
def check_source(find):
    """Static analysis of every implementation script."""
    for path in iter_python_files():
        src = read(path)
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            find.add("PARSE", "WARNING", path, exc.lineno or 0,
                     "file could not be parsed: {}".format(exc.msg))
            continue

        lines = src.splitlines()

        for node in ast.walk(tree):
            # A. metric = <literal>   or   a, b = <literal>, <literal>
            if isinstance(node, ast.Assign):
                targets = []
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        targets.append(t.id)
                    elif isinstance(t, ast.Tuple):
                        targets += [e.id for e in t.elts if isinstance(e, ast.Name)]

                hits = [t for t in targets if t.lower() in METRIC_NAMES]
                if hits:
                    values = node.value.elts if isinstance(node.value, ast.Tuple) else [node.value]
                    for val in values:
                        if isinstance(val, ast.Constant) and isinstance(val.value, (int, float)) \
                                and not isinstance(val.value, bool):
                            find.add(
                                "A_FABRICATED_METRIC", "CRITICAL", path, node.lineno,
                                "result '{}' assigned the literal {} - not measured from data"
                                .format(", ".join(hits), val.value))
                            break

                    # D. metric = other_metric * constant
                    for val in values:
                        if isinstance(val, ast.BinOp) and isinstance(val.op, ast.Mult):
                            names = [n.id for n in ast.walk(val) if isinstance(n, ast.Name)]
                            consts = [c.value for c in ast.walk(val)
                                      if isinstance(c, ast.Constant)
                                      and isinstance(c.value, (int, float))]
                            if any(n.lower() in METRIC_NAMES for n in names) and consts:
                                find.add(
                                    "D_DERIVED_METRIC", "CRITICAL", path, node.lineno,
                                    "'{}' derived by multiplying another metric by a constant "
                                    "- F1/kappa must come from a confusion matrix"
                                    .format(", ".join(hits)))
                                break

            # B. synthetic training input
            if isinstance(node, ast.Call):
                fn = node.func
                dotted = ""
                if isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name):
                    dotted = "{}.{}".format(fn.value.id, fn.attr)
                if dotted in ("torch.randn", "torch.randint", "torch.rand"):
                    ctx = lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                    # Check if synthetic call is a legitimate test fixture, parameter init, or augmentation
                    legit = False
                    if ("Parameter" in ctx or "nn.init" in ctx
                            or "determinism" in path.lower() or "install" in path.lower()
                            or "auto_setup" in path.lower() or "perf" in path.lower()
                            or "torch.rand(1)" in ctx):
                        legit = True
                    else:
                        # Check if inside Synthetic class, smoke helper, or __main__ self-test block
                        for idx in range(node.lineno - 1, -1, -1):
                            l_str = lines[idx].strip()
                            if (l_str.startswith("class Synthetic") or "if __name__ ==" in l_str
                                    or "def _make_smoke" in l_str or "smoke" in l_str.lower()):
                                legit = True
                                break
                            if l_str.startswith("class ") or (l_str.startswith("def ") and not l_str.startswith("def __")):
                                if "synthetic" not in l_str.lower() and "smoke" not in l_str.lower():
                                    break
                    if not legit:
                        find.add(
                            "B_SYNTHETIC_INPUT", "CRITICAL", path, node.lineno,
                            "model input generated by {} - fitting noise, not images"
                            .format(dotted))

        # C. a training loop that never backpropagates
        if re.search(r"for\s+epoch\s+in\s+range", src):
            if "loss.backward()" not in src and ".backward()" not in src:
                find.add("C_EMPTY_TRAIN_LOOP", "CRITICAL", path, 0,
                         "epoch loop present but no .backward() anywhere - "
                         "no training occurs")
            elif "optimizer.step()" not in src:
                find.add("C_EMPTY_TRAIN_LOOP", "WARNING", path, 0,
                         "backward() found but no optimizer.step() - weights never update")


# ------------------------------------------------------------------ check E
def check_checkpoints(find):
    ckpt_dir = os.path.join(DATA_DIR, "checkpoints")
    if not os.path.isdir(ckpt_dir):
        find.add("E_CHECKPOINT", "WARNING", ckpt_dir, 0, "no checkpoint directory yet")
        return

    # Claimed architecture -> approximate true parameter count (millions)
    EXPECTED_M = {
        "ResNet_50": 25.6, "ConvNeXt_T": 28.6, "Swin_T": 28.3, "3D_UNet": 19.0,
    }

    try:
        import torch
    except ImportError:
        find.add("E_CHECKPOINT", "WARNING", ckpt_dir, 0,
                 "torch unavailable - checkpoint contents not inspected")
        return

    for fn in sorted(os.listdir(ckpt_dir)):
        if not fn.endswith(".pt"):
            continue
        path = os.path.join(ckpt_dir, fn)
        size = os.path.getsize(path)

        try:
            obj = torch.load(path, map_location="cpu", weights_only=False)
        except Exception:
            find.add("E_CHECKPOINT", "CRITICAL", path, 0,
                     "not a loadable torch checkpoint ({} bytes) - "
                     "file does not contain model weights".format(size))
            continue

        state = None
        if isinstance(obj, dict):
            for key in ("model_state_dict", "state_dict"):
                if key in obj and isinstance(obj[key], dict):
                    state = obj[key]
                    break
            if state is None and all(hasattr(v, "shape") for v in obj.values() if v is not None):
                state = obj

        if not state:
            find.add("E_CHECKPOINT", "CRITICAL", path, 0,
                     "no state_dict inside checkpoint - nothing was trained")
            continue

        n_params = sum(int(v.numel()) for v in state.values() if hasattr(v, "numel"))
        for tag, expected_m in EXPECTED_M.items():
            if tag in fn:
                actual_m = n_params / 1e6
                if actual_m < expected_m * 0.5:
                    find.add(
                        "E_CHECKPOINT", "CRITICAL", path, 0,
                        "named '{}' but holds {:.3f}M parameters, expected about {:.1f}M "
                        "- the claimed architecture was never built"
                        .format(tag, actual_m, expected_m))
                break


# ------------------------------------------------------------------ check F
def check_methodology(find):
    """Cross-check the implementation against thesis/chapter3.tex."""
    ch3 = os.path.join(PROJECT_ROOT, "thesis", "chapter3.tex")
    n_nodes_required = 25
    if os.path.exists(ch3):
        m = re.search(r"\|V\|\s*=\s*(\d+)", read(ch3))
        if m:
            n_nodes_required = int(m.group(1))

    for path in iter_python_files():
        src = read(path)

        for m in re.finditer(r"total_graph_nodes'?\]?\s*==\s*(\d+)", src):
            found = int(m.group(1))
            if found != n_nodes_required:
                find.add(
                    "F_METHODOLOGY_DRIFT", "CRITICAL", path,
                    src[:m.start()].count("\n") + 1,
                    "asserts a graph of {} nodes; chapter3.tex specifies {} "
                    "(5 levels x 5 conditions)".format(found, n_nodes_required))

        # Chapter 3 grades on three ordinal levels: Normal/Mild, Moderate, Severe
        for m in re.finditer(r"num_classes\s*=\s*(\d+)|nn\.Linear\([^)]*,\s*(\d+)\)\s*$",
                             src, re.M):
            val = m.group(1) or m.group(2)
            if val and int(val) == 5 and "graph" not in path.lower():
                find.add(
                    "F_METHODOLOGY_DRIFT", "WARNING", path,
                    src[:m.start()].count("\n") + 1,
                    "output width {} - chapter3.tex defines 3 ordinal grades "
                    "(Normal/Mild < Moderate < Severe)".format(val))
                break

        if "edge_index=None" in src or re.search(r"def forward\([^)]*edge_index[^)]*\):", src):
            body = src[src.find("def forward"):]
            head = body[:600]
            if "edge_index" in head.split("\n")[0] and body.count("edge_index") < 2:
                find.add(
                    "F_METHODOLOGY_DRIFT", "CRITICAL", path,
                    src[:src.find("def forward")].count("\n") + 1,
                    "forward() accepts edge_index but never uses it - "
                    "no message passing occurs, so this is not a graph model")


# ------------------------------------------------------------------ check G
def check_pixel_provenance(find):
    """At least one script must actually open image data."""
    readers = ("pydicom", "nibabel", "SimpleITK", "cv2", "PIL", "imageio", "skimage")
    reads_pixels = []
    for path in iter_python_files():
        src = read(path)
        if any(r in src for r in readers) and "stop_before_pixels=True" not in src:
            reads_pixels.append(path)

    if not reads_pixels:
        find.add("G_NO_PIXELS", "CRITICAL", "", 0,
                 "no script anywhere reads image pixel data - "
                 "the pipeline cannot be learning from MRI")


# ------------------------------------------------------------------ check H
def check_outputs(find, create=False):
    for d in REQUIRED_OUTPUT_DIRS:
        if os.path.isdir(d):
            continue
        if create:
            os.makedirs(d, exist_ok=True)
            print("  created {}".format(os.path.relpath(d, PROJECT_ROOT)))
        else:
            find.add("H_OUTPUT_DIR", "WARNING", d, 0,
                     "required output directory missing (run with --create-dirs)")

    # Stage separation: training history must not be written into the test-results dir
    reports = os.path.join(DATA_DIR, "reports")
    if os.path.isdir(reports):
        for fn in os.listdir(reports):
            if "epoch" in fn.lower() or "train_history" in fn.lower():
                find.add("H_STAGE_MIXING", "WARNING", os.path.join(reports, fn), 0,
                         "per-epoch training artefact inside data/reports/, which is "
                         "reserved for held-out test results - keep Stage 1 in data/logs/")


# -------------------------------------------------------------------- report
def main():
    ap = argparse.ArgumentParser(description="Adversarial integrity check for AMOG-Net")
    ap.add_argument("--json", type=str, default=None, help="write findings to this JSON file")
    ap.add_argument("--create-dirs", action="store_true",
                    help="create any missing output directories, then continue")
    args = ap.parse_args()

    print("=" * 74)
    print("  AMOG-Net Implementation Integrity Check")
    print("  Designed to fail on fabricated results. See AUDIT_FINDINGS.md.")
    print("=" * 74)
    print("  project : {}".format(PROJECT_ROOT))
    print("  run at  : {}".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    print()

    find = Findings()
    if args.create_dirs:
        print("Ensuring output directories exist:")
    check_outputs(find, create=args.create_dirs)
    if args.create_dirs:
        print()

    check_source(find)
    check_checkpoints(find)
    check_methodology(find)
    check_pixel_provenance(find)

    by_check = {}
    for item in find.items:
        by_check.setdefault(item["check"], []).append(item)

    for check in sorted(by_check):
        items = by_check[check]
        sev = "CRITICAL" if any(i["severity"] == "CRITICAL" for i in items) else "WARNING"
        mark = "[FAIL]" if sev == "CRITICAL" else "[WARN]"
        print("{} {}  ({} finding{})".format(mark, check, len(items),
                                             "" if len(items) == 1 else "s"))
        for i in items[:12]:
            loc = "{}:{}".format(i["file"], i["line"]) if i["line"] else i["file"] or "-"
            print("        {}".format(loc))
            print("            {}".format(i["message"]))
        if len(items) > 12:
            print("        ... and {} more".format(len(items) - 12))
        print()

    n_crit, n_warn = len(find.critical), len(find.warnings)
    print("-" * 74)
    if n_crit:
        print("RESULT: FAILED - {} critical, {} warning".format(n_crit, n_warn))
        print()
        print("Critical findings mean reported results do not trace back to a")
        print("computation on real data. They must not be cited in the thesis.")
    elif n_warn:
        print("RESULT: PASSED WITH WARNINGS - {} warning".format(n_warn))
    else:
        print("RESULT: PASSED - results trace to computation on real data")
    print("-" * 74)

    if args.json:
        payload = {
            "generated_at": datetime.now().isoformat(),
            "project_root": PROJECT_ROOT,
            "critical": n_crit, "warnings": n_warn,
            "passed": n_crit == 0,
            "findings": find.items,
        }
        os.makedirs(os.path.dirname(os.path.abspath(args.json)) or ".", exist_ok=True)
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        print("findings written to {}".format(args.json))

    return 1 if n_crit else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print("[ERROR] integrity check could not run: {}".format(exc))
        sys.exit(2)
