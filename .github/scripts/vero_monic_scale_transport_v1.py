from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('monic_scale_transport_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division
\nnamespace GaloistoolsMonicScaleTransportV1\n'''
footer='\nend GaloistoolsMonicScaleTransportV1\n'

probes = {
'scale_modeq': r'''
theorem scale_modeq (p c d : Nat) (f : List Nat)
    (h : NatModEq p c d) :
    Galoistools.scaleP p c f = Galoistools.scaleP p d f := by
  unfold Galoistools.scaleP
  apply List.map_congr_left
  intro x hx
  unfold NatModEq at h
  simp only
  rw [Nat.mul_mod, Nat.mul_mod]
  rw [h]
''',
'mul_scale_both': r'''
theorem mul_scale_both (p a b : Nat) (f g : List Nat) :
    Galoistools.gfMul (Galoistools.scaleP p a f) (Galoistools.scaleP p b g) p =
      Galoistools.scaleP p (a*b) (Galoistools.gfMul f g p) := by
  simp [Galoistools.gfMul, Galoistools.scaleP]
'''
}

census=[]
for name,text in probes.items():
    q=out/f'Probe_{name}.lean'; q.write_text(header+text+footer)
    cp=subprocess.run(['lake','lean',q.name],cwd=out,text=True,capture_output=True)
    raw=cp.stdout+'\n'+cp.stderr; lines=raw.splitlines()
    errors=[x for x in lines if 'error:' in x or 'error(' in x or 'unknown identifier' in x]
    goals=[]
    for k,line in enumerate(lines):
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+100]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'tail':'\n'.join(lines[-350:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['tail'])
Path('monic_scale_transport_v1').mkdir(exist_ok=True)
Path('monic_scale_transport_v1/census.json').write_text(json.dumps(census,indent=2))
