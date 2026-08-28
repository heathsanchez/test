from pathlib import Path
import re, shutil, subprocess

BASE=Path('baseline28/galoistools_allin28').resolve()
OUT=Path('vero_msi_sealed_residual_probe_v2').resolve()
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(BASE,OUT)
for c in OUT.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

TARGET='prove_gcd_divides_both'
BLOCK_RE=re.compile(
    r'(?P<head>theorem\s+(?P<name>[A-Za-z0-9_]+)\s*:[^\n]+:=\s*by\n'
    r'-- !benchmark @start proof def=(?P=name) kind=prove target=[^\n]+\n)'
    r'(?P<body>.*?)'
    r'(?P<tail>\n-- !benchmark @end proof def=(?P=name))', re.S)

def isolate(src):
    def repl(m):
        if m.group('name')==TARGET: return m.group(0)
        return m.group('head')+'  sorry'+m.group('tail')
    return BLOCK_RE.sub(repl,src)

def patch(src,body):
    def repl(m):
        if m.group('name')!=TARGET:return m.group(0)
        return m.group('head')+body+m.group('tail')
    return BLOCK_RE.sub(repl,src)

pf=OUT/'Galoistools/Proof/Division.lean'
src=isolate(pf.read_text())
body='''  simp only [spec_gcd_divides_both, canonical]\n  intros f g p hp hf hg\n  simp [Galoistools.gfGcd, Galoistools.gfRem]'''
pf.write_text(patch(src,body))
cp=subprocess.run(['lake','lean','Galoistools/Proof/Division.lean'],cwd=OUT,text=True,capture_output=True,timeout=180)
raw=cp.stdout+'\n'+cp.stderr
Path('sealed_residual_v2.txt').write_text(raw)
print('SEALED_RESIDUAL_V2_EXIT',cp.returncode)
print(raw[-30000:])
# This probe is evidence collection, so preserve workflow green while retaining
# the actual compiler exit in the artifact/log.
