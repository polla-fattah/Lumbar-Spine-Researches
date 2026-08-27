"""Replace Chapter 4's comparisons table by locating its own delimiters."""
import io

P = (r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
     r'\thesis\chapter4.tex')
lines = io.open(P, encoding='utf-8').read().split('\n')

# find the table environment that contains \label{tab:comparisons}
lab = next(i for i, l in enumerate(lines) if 'label{tab:comparisons}' in l)
start = max(i for i in range(lab) if lines[i].startswith(r'\begin{table}'))
end = next(i for i in range(lab, len(lines)) if lines[i].startswith(r'\end{table}'))

BS = chr(92)
new = [
    r'\begin{table}[htbp]',
    r'\centering',
    r'\small',
    r'\caption{Pre-specified comparisons, QWK, seven seeds. Difference averaged',
    r'over seeds with the patient resample shared across them; FDR controlled',
    r'across these rows.}',
    r'\label{tab:comparisons}',
    r'\begin{tabular}{llccccc}',
    r'\toprule',
    r'Comparison & Tests & $\Delta$ & 95\% CI & Seeds $+$ & $p_{\mathrm{FDR}}$ & Sig \\',
    r'\midrule',
    r'E7 vs E0 & full system & $+0.0177$ & $[+0.0097, +0.0260]$ & 7/7 & $\mathbf{<0.001}$ & \textbf{yes} \\',
    r'E6 vs E5 & typed edges (RQ1) & $+0.0093$ & $[+0.0027, +0.0156]$ & 7/7 & $\mathbf{0.009}$ & \textbf{yes} \\',
    r'E7 vs E6 & ordinal head (RQ5) & $+0.0082$ & $[+0.0025, +0.0143]$ & 7/7 & $\mathbf{0.009}$ & \textbf{yes} \\',
    r'\midrule',
    r'E2 vs E1 & routing (RQ3) & $+0.0053$ & $[-0.0002, +0.0112]$ & 5/7 & $0.131$ & no \\',
    r'E4 vs E3 & ACSSL (RQ2) & $+0.0020$ & $[-0.0043, +0.0089]$ & 4/7 & $0.688$ & no \\',
    r'E6 vs E6\_shuf & anatomy (RQ1) & $+0.0020$ & $[-0.0038, +0.0076]$ & 4/7 & $0.688$ & no \\',
    r'E6 vs E6\_ung & gating & $+0.0014$ & $[-0.0041, +0.0064]$ & 3/7 & $0.713$ & no \\',
    r'E5 vs E0 & message passing & $+0.0002$ & $[-0.0073, +0.0074]$ & 5/7 & $0.967$ & no \\',
    r'E3 vs E2 & modality dropout & $-0.0026$ & $[-0.0091, +0.0034]$ & 4/7 & $0.627$ & no \\',
    r'\bottomrule',
    r'\end{tabular}',
    r'\end{table}',
]

out = lines[:start] + new + lines[end + 1:]
txt = '\n'.join(out)
txt = txt.replace(
    'corrected procedure. [3-SEED]',
    'corrected procedure. Three survive correction, where the three-seed\n'
    'analysis produced one.')
io.open(P, 'w', encoding='utf-8').write(txt)
print('table 4.3 replaced (lines %d-%d), [3-SEED] marker cleared' % (start + 1, end + 1))
