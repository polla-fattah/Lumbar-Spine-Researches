#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Every \\ref must resolve, and every \\input file must exist.

pdflatex reports an unresolved reference as "??" in the output and a warning
buried in a log thousands of lines long. In a thesis assembled from standalone
chapters that is easy to ship: the chapter compiles alone, the reference points
at a label in another chapter, and only the full build would have caught it.

This runs without a TeX toolchain, which is the point -- it is the check that
can be made while the toolchain is still being installed.

Run:  python implementation/99_audit/check_refs.py
"""
from __future__ import annotations

import glob
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
THESIS = os.path.join(ROOT, "thesis")

LABEL = re.compile(r"\\label\{([^}]+)\}")
REF = re.compile(r"\\(?:auto|c|C|page)?ref\{([^}]+)\}")
INPUT = re.compile(r"\\(?:input|include)\{([^}]+)\}")
GRAPHIC = re.compile(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}")
GPATH = re.compile(r"\\graphicspath\{((?:\{[^{}]*\})+)\}")


def strip_comments(s):
    return re.sub(r"(?<!\\)%.*", "", s)


def main():
    files = sorted(glob.glob(os.path.join(THESIS, "chapter*.tex")))
    files.append(os.path.join(THESIS, "thesis.tex"))
    files = [f for f in files if os.path.exists(f)]

    text = {}
    labels = {}
    for f in files:
        s = strip_comments(io.open(f, encoding="utf-8").read())
        text[f] = s
        for m in LABEL.finditer(s):
            labels.setdefault(m.group(1), []).append(os.path.basename(f))

    bad_refs, dup, missing_input, missing_gfx = [], [], [], []

    for lab, where in labels.items():
        if len(where) > 1:
            dup.append((lab, where))

    for f, s in text.items():
        base = os.path.basename(f)
        for r in sorted(set(REF.findall(s))):
            if r not in labels:
                bad_refs.append((base, r))

        # \input targets, resolved relative to thesis/
        for t in sorted(set(INPUT.findall(s))):
            cands = [os.path.join(THESIS, t),
                     os.path.join(THESIS, t + ".tex")]
            if not any(os.path.exists(c) for c in cands):
                missing_input.append((base, t))

        # \includegraphics against the declared \graphicspath
        roots = [THESIS]
        gp = GPATH.search(s)
        if gp:
            roots += [os.path.join(THESIS, p)
                      for p in re.findall(r"\{([^{}]*)\}", gp.group(1))]
        for g in sorted(set(GRAPHIC.findall(s))):
            found = False
            for root in roots:
                for ext in ("", ".pdf", ".png", ".jpg", ".eps"):
                    if os.path.exists(os.path.join(root, g + ext)):
                        found = True
                        break
                if found:
                    break
            if not found:
                missing_gfx.append((base, g))

    print("thesis reference check")
    print("-" * 60)
    print("  files    {}".format(len(files)))
    print("  labels   {}".format(len(labels)))

    n = 0
    for title, rows, fmt in (
            ("undefined references", bad_refs, "{}: \\ref{{{}}}"),
            ("duplicate labels", dup, "{}: {}"),
            ("missing \\input targets", missing_input, "{}: {}"),
            ("missing graphics", missing_gfx, "{}: {}")):
        if rows:
            n += len(rows)
            print("\n  {} ({})".format(title, len(rows)))
            for a, b in rows:
                print("    " + fmt.format(a, b))

    print()
    if n:
        print("  {} problem(s). Each becomes a '??' or a hard error at build.".format(n))
    else:
        print("  0 problems: every reference resolves, every input and graphic exists.")
        print("  This does not mean the document compiles; it means these do not")
        print("  break it.")
    return 1 if n else 0


if __name__ == "__main__":
    sys.exit(main())
