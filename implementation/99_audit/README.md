# 99_audit — independent integrity verification

This directory contains the only check in the repository that is capable of failing.

## Why it exists

The 13 "Quality Gates" in `00_`–`13_` do not verify anything. Each gate reads a JSON
file that the script under test wrote moments earlier, and asserts that the constant
inside it clears a threshold. The value being checked and the value being written are
the same value, so the gate passes by construction. `verify_gate7_gate8_graph.py` is
the clearest example:

```python
assert m['total_graph_nodes'] == 1000          # a number the fabricator wrote
assert f1_gain > 5.0                           # another one
```

Self-certification is not verification. This checker was written by a different party
from the one being checked, and it is designed to fail on the code as it stands.

## Running it

```bash
python implementation/99_audit/verify_integrity.py
```

Options:

| Flag | Effect |
|---|---|
| `--create-dirs` | create any missing output directory, then continue |
| `--json PATH` | write machine-readable findings for CI |

Exit codes: `0` clean, `1` integrity violations found, `2` could not run.

## What it checks

| ID | Check | Question it answers |
|---|---|---|
| **A** | Fabricated metrics | Is a reported result assigned a float literal instead of measured? |
| **B** | Synthetic input | Is the model fitted to `torch.randn` rather than to images? |
| **C** | Empty training loops | Does an epoch loop exist with no `.backward()`? |
| **D** | Derived metrics | Are F1 / kappa produced by multiplying accuracy by a constant? |
| **E** | Checkpoint substance | Does a `.pt` hold a real `state_dict`, and does its parameter count match the architecture in its filename? |
| **F** | Methodology drift | Do graph node count and class count match `thesis/chapter3.tex`? Does `forward()` actually use `edge_index`? |
| **G** | Pixel provenance | Does any script in the tree ever open image data? |
| **H** | Output hygiene | Do the required output directories exist, and is Stage 1 (training) kept out of the Stage 2 (test) directory? |

Check **F** reads `thesis/chapter3.tex` directly and parses `|V| = 25` from the node-set
equation, so the methodology stays the single source of truth. If Chapter 3 changes, the
check follows it — there is no second copy of the specification to drift out of sync.

Check **G** currently passes: `00_deidentify/deidentify_dicom.py` and
`02_data_manifest/build_lumbarDISC_manifest.py` do genuinely read DICOM. The check is
calibrated to distinguish real data handling from fabrication, not to fail everything.

## Current status

```
RESULT: FAILED — 38 critical, 4 warning
```

See `../AUDIT_FINDINGS.md` for the full analysis and for which components are genuine
and worth keeping.

## Using it as a gate

Any future implementation — whoever or whatever writes it — should have to pass this
before its numbers are believed:

```bash
python implementation/99_audit/verify_integrity.py || echo "results are not citable"
```

A clean run is a necessary condition, not a sufficient one. It shows that numbers trace
back to a computation on real data. It cannot show that the computation was the right
one; that is what the ablations and controls in Chapter 3 are for.
