from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('div_identity_lift/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

namespace GaloistoolsDivIdentityLift
'''
footer = '\nend GaloistoolsDivIdentityLift\n'

probes = {
'gfStrip_append_strip': r'''
theorem gfStrip_append_strip (xs ys : List Nat) :
    Galoistools.gfStrip (xs ++ ys) =
      Galoistools.gfStrip (Galoistools.gfStrip xs ++ ys) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      by_cases hx : x = 0
      · simp [Galoistools.gfStrip, hx, ih]
      · simp [Galoistools.gfStrip, hx]
''',
'gfAdd_strip_right_attempt': r'''
theorem gfAdd_strip_right_attempt (p : Nat) (a b : List Nat) :
    Galoistools.gfAdd a (Galoistools.gfStrip b) p =
      Galoistools.gfAdd a b p := by
  induction b with
  | nil => rfl
  | cons x xs ih =>
      by_cases hx : x = 0
      · simp only [Galoistools.gfStrip, hx, if_pos]
        rw [ih]
        simp only [Galoistools.gfAdd, List.reverse_cons]
      · simp [Galoistools.gfStrip, hx]
'''
}

census=[]
for name, text in probes.items():
    probe=source/f'Probe_{name}.lean'
    probe.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',probe.name],cwd=source,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr
    lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for k,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+100]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-440:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('div_identity_lift'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('DIV_IDENTITY_LIFT_CENSUS',json.dumps(census))
