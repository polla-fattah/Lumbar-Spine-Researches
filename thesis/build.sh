#!/bin/sh
# Build the thesis. Run from thesis/.
#
# --output-safechars on biber is REQUIRED, not cosmetic: biber decodes LaTeX
# accent macros from the .bib into DECOMPOSED Unicode, which inputenc cannot
# typeset, and the build fails on any cited author with an accented name.
#
# Four passes: pdflatex to emit .bcf, biber to resolve the bibliography, then
# two more pdflatex so cross-references and the table of contents settle.
set -e
export PATH="$LOCALAPPDATA/Programs/MiKTeX/miktex/bin/x64:$PATH"
pdflatex -interaction=nonstopmode thesis
biber --output-safechars thesis
pdflatex -interaction=nonstopmode thesis
pdflatex -interaction=nonstopmode thesis
echo
grep -c '^! ' thesis.log && echo "ERRORS ABOVE" || echo "0 errors"
grep -c 'Warning: \(Citation\|Reference\)' thesis.log || echo "0 undefined references"
grep 'Output written on' thesis.log
