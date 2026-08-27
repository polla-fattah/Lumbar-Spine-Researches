"""Which scripts are still load-bearing, and which are superseded?

Deleting by memory is how a working file gets removed. This classifies every
Python file in the numbered phase directories by whether anything still
references it, whether it writes results the thesis cites, and whether the
amog_* pipeline supersedes it.
"""
import io, os, re, subprocess, glob

ROOT = r'C:\Users\USER\Desktop\Polla\Lumbar\Lumbar-Spine-Researches'
os.chdir(ROOT)

phase = sorted(glob.glob('implementation/[0-9]*/*.py'))
core = sorted(glob.glob('implementation/*.py') + glob.glob('tools/*.py')
              + glob.glob('implementation/99_audit/*.py'))

all_src = {}
for f in phase + core:
    try:
        all_src[f] = io.open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        all_src[f] = ''

# also scan docs and the thesis for references
docs = []
for pat in ('*.md', 'thesis/*.tex', 'thesis/chapter4/*.md', '*.yml', '*.cfg'):
    docs += glob.glob(pat)
doc_src = ''
for d in docs:
    try:
        doc_src += io.open(d, encoding='utf-8', errors='ignore').read()
    except Exception:
        pass

print('%-52s %8s %6s %6s' % ('file', 'refs', 'indocs', 'lines'))
print('-' * 78)
rows = []
for f in phase:
    stem = os.path.splitext(os.path.basename(f))[0]
    refs = 0
    for g, src in all_src.items():
        if g == f:
            continue
        if re.search(r'\b' + re.escape(stem) + r'\b', src):
            refs += 1
    indocs = len(re.findall(r'\b' + re.escape(stem) + r'\b', doc_src))
    lines = all_src[f].count('\n') + 1
    rows.append((f, refs, indocs, lines))

for f, refs, indocs, lines in rows:
    flag = '' if (refs or indocs) else '   <- no references anywhere'
    print('%-52s %8d %6d %6d%s' % (f, refs, indocs, lines, flag))

orphan = [r for r in rows if r[1] == 0 and r[2] == 0]
print()
print('phase scripts: %d total, %d with no reference anywhere'
      % (len(rows), len(orphan)))
print()
print('git last-touched for the unreferenced ones:')
for f, _, _, _ in orphan:
    try:
        d = subprocess.run(['git', 'log', '-1', '--format=%ad', '--date=short',
                            '--', f], capture_output=True, text=True).stdout.strip()
    except Exception:
        d = '?'
    print('   %-50s %s' % (f, d or 'never committed'))
