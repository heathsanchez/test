from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out = Path('msi_monic_separator_v1/source').resolve()
create_sandbox(bench, out, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Division

namespace GaloistoolsMSIMonicSeparatorV1
'''
footer = '\nend GaloistoolsMSIMonicSeparatorV1\n'

probes = {
'scale_modeq_exact': r'''
theorem scale_modeq_exact (p c d : Nat) (f : List Nat)
    (h : NatModEq p c d) :
    Galoistools.scaleP p c f = Galoistools.scaleP p d f := by
  unfold Galoistools.scaleP
  congr 1
  apply List.map_congr_left
  intro x hx
  unfold NatModEq at h
  rw [Nat.mul_mod, Nat.mul_mod, h]
''',
'zip_scale': r'''
theorem zip_scale (p k : Nat) (xs ys : List Nat) :
    Galoistools.zipAddPad p
      (xs.map (fun x => (x*k)%p))
      (ys.map (fun y => (y*k)%p)) =
    (Galoistools.zipAddPad p xs ys).map (fun z => (z*k)%p) := by
  induction xs generalizing ys with
  | nil =>
      cases ys <;> simp [Galoistools.zipAddPad, Nat.mul_mod]
  | cons x xs ih =>
      cases ys with
      | nil => simp [Galoistools.zipAddPad, Nat.mul_mod]
      | cons y ys =>
          simp [Galoistools.zipAddPad, ih, Nat.add_mul, Nat.add_mod, Nat.mul_mod]
''',
'convolve_scale_left': r'''
theorem convolve_scale_left (p k : Nat) (xs ys : List Nat) :
    Galoistools.convolve p (xs.map (fun x => (x*k)%p)) ys =
      (Galoistools.convolve p xs ys).map (fun z => (z*k)%p) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      simp [Galoistools.convolve, ih]
''',
'convolve_scale_both': r'''
theorem convolve_scale_both (p a b : Nat) (xs ys : List Nat) :
    Galoistools.convolve p
      (xs.map (fun x => (x*a)%p))
      (ys.map (fun y => (y*b)%p)) =
    (Galoistools.convolve p xs ys).map (fun z => (z*(a*b))%p) := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      simp [Galoistools.convolve, ih]
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
        if '⊢ ' in line or line.startswith('case '): goals.append('\n'.join(lines[k:k+120]))
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'tail':'\n'.join(lines[-420:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['tail'])
Path('msi_monic_separator_v1').mkdir(exist_ok=True)
Path('msi_monic_separator_v1/census.json').write_text(json.dumps(census,indent=2))
print('MSI_MONIC_SEPARATOR_V1', json.dumps([{'probe':x['probe'],'exit':x['exit']} for x in census]))
