from pathlib import Path
import json, subprocess, shutil

SRC = Path('coldcert/project').resolve()
WORK = Path('division_blocker_quarantine_v1/work').resolve()
OUT = Path('division_blocker_quarantine_v1').resolve()
OUT.mkdir(exist_ok=True)
if WORK.exists(): shutil.rmtree(WORK)
shutil.copytree(SRC, WORK)

p = WORK/'Galoistools/Proof/Division.lean'
text = p.read_text()

NAMES = ['prove_gcd_monic','prove_gcd_self','prove_gcd_zero_right','prove_gcd_empty_iff']

def replace_body(text, name):
    start = f'-- !benchmark @start proof def={name}'
    end = f'-- !benchmark @end proof def={name}'
    a = text.index(start) + len(start)
    b = text.index(end, a)
    return text[:a] + '\n  sorry\n' + text[b:]

for n in NAMES:
    text = replace_body(text, n)
p.write_text(text)

cp = subprocess.run(['lake','build','Galoistools.Proof.Division'],cwd=WORK,text=True,capture_output=True)
raw = cp.stdout+'\n'+cp.stderr
print('DIVISION_BLOCKER_QUARANTINE_V1', json.dumps({'division_exit':cp.returncode,'quarantined':NAMES}))
print(raw[-30000:])
(OUT/'result.json').write_text(json.dumps({'division_exit':cp.returncode,'quarantined':NAMES,'tail':raw[-30000:]},indent=2))
raise SystemExit(cp.returncode)
