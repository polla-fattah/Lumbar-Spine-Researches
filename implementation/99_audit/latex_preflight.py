#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Catch LaTeX build failures without a LaTeX toolchain.

WHY THIS EXISTS
---------------
Roughly a thousand lines of new LaTeX were written into Chapters 4 and 5, with
seven tables and thirty-five cross-references, and no compiler is installable on
this machine. Balanced braces and resolving references were already verified;
neither catches what actually breaks a build.

CALIBRATION -- THE PART THAT MAKES IT WORTH ANYTHING
----------------------------------------------------
Chapters 2 and 3 have compiled: `chapter2.pdf` and `chapter3.pdf` exist. So any
issue reported in those files is a false positive BY CONSTRUCTION, and they are
the calibration set. A checker is only useful if it is silent on known-good
input.

A first version of this file reported 268 issues, of which every single one was
a false positive. Four separate defects caused them, all now fixed and all
recorded here because each is an easy trap:

  * The column specification was parsed with `[^}]*`, which cannot handle the
    nested braces in `p{1.1cm}p{5.0cm}`. It truncated at the first brace and
    then complained that every row had too many columns.
  * Table rows were assumed to occupy one source line. A `p{}` column wraps, so
    a single logical row spans several lines. Rows are now joined on `\\\\`
    across the whole environment body.
  * `#1` inside `\\newcommand` is a parameter, not an unescaped hash.
  * A trailing `%` comment is ordinary LaTeX. Distinguishing an intentional
    comment from a percent sign someone forgot to escape is not decidable from
    the source, so that check was removed rather than left to cry wolf.

WHAT IT CHECKS NOW
------------------
Column counts per logical row against a brace-aware column specification.
Unescaped `_` and `#` outside mathematics, outside verbatim, and outside the
arguments where they are legitimate. Citation keys against the bibliography.
Environment nesting. Control characters left by the shell-escaping incidents
earlier in this project, which are invisible in an editor and fatal to a build.

THIS IS A SUBSTITUTE, NOT A REPLACEMENT
---------------------------------------
A clean run means the common failures are absent. It does not mean the document
compiles: package conflicts, float placement, and anything depending on the
class file are outside what static analysis can see.
"""
from __future__ import annotations

import os
import re
import sys
from collections import Counter

BS = chr(92)
E = re.escape

# arguments whose contents are filenames, labels or literal text, where an
# underscore is legitimate and must not be flagged
#
# graphicspath is here with a nested-brace body because its argument is a LIST
# of brace groups -- \graphicspath{{a/}{b/}} -- so the flat \{[^}]*\} used for
# the others stops at the first closing brace and leaves the rest of the line
# exposed. Its contents are directory names that graphicx only ever uses for
# file lookup and never typesets, so underscores in them are legitimate.
LITERAL_ARGS = re.compile(
    E(BS) + r'(?:addbibresource|input|include|includegraphics|label|ref|autoref'
    r'|cite[a-zA-Z]*|texttt|verb|path|url|href|bibliography)'
    r'(?:\[[^\]]*\])?\{[^}]*\}'
    r'|' + E(BS) + r'graphicspath\s*\{(?:[^{}]|\{[^{}]*\})*\}')
MATH = re.compile(r'\$[^$]*\$')
# Display maths too. Chapter 3 is largely equations, and their
# subscripts are legitimate underscores; masking only inline $...$
# flagged 193 of them in a file that demonstrably compiles.
MATH_ENVS = ('equation', 'equation*', 'align', 'align*', 'gather',
             'gather*', 'multline', 'multline*', 'displaymath',
             'eqnarray', 'eqnarray*', 'split', 'array')
NEWCMD = re.compile(E(BS) + r'(?:re)?newcommand|' + E(BS) + r'def')


def math_env_lines(text):
    """Line numbers (1-based) that sit inside a display-maths environment."""
    inside, out, depth = False, set(), 0
    for n, line in enumerate(text.split('\n'), 1):
        opens = [e for e in MATH_ENVS
                 if (BS + 'begin{' + e + '}') in line]
        closes = [e for e in MATH_ENVS
                  if (BS + 'end{' + e + '}') in line]
        if opens:
            depth += len(opens)
        if depth > 0:
            out.add(n)
        if closes:
            depth = max(0, depth - len(closes))
        # \[ ... \] display maths
        if (BS + '[') in line:
            depth += line.count(BS + '[')
            out.add(n)
        if (BS + ']') in line:
            depth = max(0, depth - line.count(BS + ']'))
            out.add(n)
    return out


def strip_comment(line):
    out, i = [], 0
    while i < len(line):
        if line[i] == BS and i + 1 < len(line):
            out.append(line[i:i + 2]); i += 2; continue
        if line[i] == '%':
            break
        out.append(line[i]); i += 1
    return ''.join(out)


def mask(s, pat):
    return pat.sub(lambda m: ' ' * len(m.group(0)), s)


def count_columns(spec):
    """Column count of a tabular specification, brace-aware."""
    out, depth = [], 0
    for ch in spec:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
        elif depth == 0:
            out.append(ch)
    return len(re.findall(r'[lcrpmb]', ''.join(out)))


def read_spec(text, i):
    """Read a balanced {...} beginning at text[i] == '{'. Returns (spec, end)."""
    depth, j = 0, i
    while j < len(text):
        if text[j] == '{':
            depth += 1
        elif text[j] == '}':
            depth -= 1
            if depth == 0:
                return text[i + 1:j], j + 1
        j += 1
    return None, i


def check_tables(text, path, errs):
    """Every logical row against its own column specification."""
    # Match ONLY the egin{env} and any [pos] option. Do not try to match the
    # column specification with a regex -- it contains nested braces, and an
    # optional group that matches it will swallow it and leave the balanced
    # reader pointing at the first brace of the table BODY, which reports every
    # spec as "0 declared".
    pat = re.compile(E(BS) + r'begin\{(tabular|longtable|tabularx)\}'
                     r'(?:\[[^\]]*\])?')
    WS = ' ' + chr(9) + chr(10) + chr(13)
    for m in pat.finditer(text):
        env = m.group(1)
        i = m.end()
        while i < len(text) and text[i] in WS:
            i += 1
        if i >= len(text) or text[i] != '{':
            continue
        spec, body_start = read_spec(text, i)
        if spec is None:
            continue
        cols = count_columns(spec)
        end = text.find(BS + 'end{' + env + '}', body_start)
        if end < 0:
            continue
        body = text[body_start:end]
        line0 = text[:m.start()].count('\n') + 1

        for raw_row in re.split(E(BS) + E(BS), body):
            row = mask(strip_comment(raw_row), MATH)
            if BS + 'multicolumn' in row or BS + 'multirow' in row:
                continue
            core = re.sub(E(BS) + r'(toprule|midrule|bottomrule|hline'
                          r'|cmidrule\{[^}]*\}|endfirsthead|endhead|endfoot'
                          r'|endlastfoot|caption\{|label\{|addlinespace)', '', row)
            if not core.strip():
                continue
            amps = len(re.findall(r'(?<!' + E(BS) + r')&', core))
            if amps and amps + 1 != cols:
                errs.append('{}: {} near line {}: row has {} columns, {} declared'
                            .format(path, env, line0, amps + 1, cols))


def check_escapes(text, path, errs):
    in_verb = False
    mathlines = math_env_lines(text)
    for n, raw in enumerate(text.split('\n'), 1):
        if n in mathlines:
            continue
        if re.search(E(BS) + r'begin\{(verbatim|lstlisting)\}', raw):
            in_verb = True
        if re.search(E(BS) + r'end\{(verbatim|lstlisting)\}', raw):
            in_verb = False
            continue
        if in_verb or raw.lstrip().startswith('%'):
            continue
        line = mask(mask(strip_comment(raw), MATH), LITERAL_ARGS)
        for m in re.finditer(r'(?<!' + E(BS) + r')_', line):
            errs.append('{}:{}: unescaped underscore at col {}'.format(
                path, n, m.start() + 1))
        if not NEWCMD.search(raw):
            for m in re.finditer(r'(?<!' + E(BS) + r')#', line):
                errs.append('{}:{}: unescaped hash at col {}'.format(
                    path, n, m.start() + 1))


def check_envs(text, path, errs):
    c = Counter()
    for line in text.split('\n'):
        s = strip_comment(line)
        for e in re.findall(E(BS) + r'begin\{([a-zA-Z*]+)\}', s):
            c[e] += 1
        for e in re.findall(E(BS) + r'end\{([a-zA-Z*]+)\}', s):
            c[e] -= 1
    for e, v in c.items():
        if v:
            errs.append('{}: environment {} unbalanced by {:+d}'.format(path, e, v))


def check_controls(text, path, errs):
    for code, name in ((9, 'TAB'), (13, 'CR'), (8, 'BACKSPACE'),
                       (12, 'FORMFEED'), (11, 'VTAB')):
        if chr(code) in text:
            errs.append('{}: contains {} x{} (lost-backslash signature)'.format(
                path, name, text.count(chr(code))))


def check_citations(text, path, keys, errs):
    if not keys:
        return
    seen = set()
    for m in re.finditer(E(BS) + r'cite[a-zA-Z]*(?:\[[^\]]*\])*\{([^}]*)\}', text):
        for k in m.group(1).split(','):
            k = k.strip()
            if k and k not in keys and k not in seen:
                seen.add(k)
                errs.append('{}: citation key not in bibliography: {}'.format(path, k))


def bib_keys(*roots):
    keys = set()
    for root in roots:
        for dirpath, _d, names in os.walk(root):
            for nm in names:
                if nm.endswith('.bib'):
                    try:
                        s = open(os.path.join(dirpath, nm), encoding='utf-8',
                                 errors='ignore').read()
                    except Exception:
                        continue
                    keys.update(k.strip() for k in
                                re.findall(r'@[a-zA-Z]+\s*\{\s*([^,]+),', s))
    return keys


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))
    tdir = os.path.join(root, 'thesis')
    files = sorted(f for f in os.listdir(tdir)
                   if f.startswith('chapter') and f.endswith('.tex'))
    if os.path.exists(os.path.join(tdir, 'thesis.tex')):
        files.append('thesis.tex')

    keys = bib_keys(tdir, root)
    known_good = {f for f in files
                  if os.path.exists(os.path.join(tdir, f.replace('.tex', '.pdf')))}

    print('=' * 74)
    print('  LaTeX pre-flight')
    print('=' * 74)
    print('  bibliography keys: {}'.format(len(keys)))
    print('  calibration set (already compiled): {}'.format(
        ', '.join(sorted(known_good)) or 'none'))
    print('')

    total, fp = 0, 0
    for f in files:
        p = os.path.join(tdir, f)
        text = open(p, encoding='utf-8').read()
        errs = []
        check_controls(text, f, errs)
        check_envs(text, f, errs)
        check_tables(text, f, errs)
        check_escapes(text, f, errs)
        check_citations(text, f, keys, errs)
        total += len(errs)
        if f in known_good:
            fp += len(errs)
        flag = '' if f not in known_good else '  [calibration]'
        print('  {:<16} {}{}'.format(
            f, 'OK' if not errs else '{} ISSUE(S)'.format(len(errs)), flag))
        for e in errs[:20]:
            print('      {}'.format(e))
        if len(errs) > 20:
            print('      ... {} more'.format(len(errs) - 20))

    print('')
    print('  total issues: {}'.format(total))
    if fp:
        print('  [!] {} of them are in files that ALREADY COMPILE, so the'.format(fp))
        print('      checker is producing false positives and must be fixed')
        print('      before its output on the new chapters means anything.')
    else:
        print('  0 issues on the calibration set, so the checker is silent on')
        print('  known-good input.')
    print('')
    print('  A clean run means the common failures are absent. It does not mean')
    print('  the document compiles. Build on a machine with a toolchain.')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
