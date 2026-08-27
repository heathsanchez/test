from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench_dir = Path('benchmarks/galoistools').resolve()
seed = read_artifact(Path('../baseline/ratchet/artifact.json').resolve())
source = Path('mul_shape_v2/source').resolve()
create_sandbox(bench_dir, source, mode='codeproof', overwrite=True, seed_artifact=seed)

header = '''import Galoistools.Proof.Ring
import Galoistools.Impl.Ring
import Galoistools.Spec.Ring

namespace GaloistoolsMulShapeV2
'''
footer = '\nend GaloistoolsMulShapeV2\n'

helpers = r'''
theorem zipAddPad_length_v2 (p : Nat) : ∀ xs ys : List Nat,
    (Galoistools.zipAddPad p xs ys).length = Nat.max xs.length ys.length := by
  intro xs
  induction xs with
  | nil =>
      intro ys
      simp [Galoistools.zipAddPad]
  | cons x xs ih =>
      intro ys
      cases ys with
      | nil => simp [Galoistools.zipAddPad]
      | cons y ys =>
          simp only [Galoistools.zipAddPad, List.length_cons]
          rw [ih ys]
          omega

theorem convolve_length_nonempty_v2 (p : Nat) (xs ys : List Nat)
    (hxs : xs ≠ []) (hys : ys ≠ []) :
    (Galoistools.convolve p xs ys).length = xs.length + ys.length - 1 := by
  induction xs with
  | nil => contradiction
  | cons x xs ih =>
      rw [Galoistools.convolve]
      rw [zipAddPad_length_v2]
      simp only [List.length_map, List.length_cons]
      by_cases htail : xs = []
      · subst xs
        simp [Galoistools.convolve]
        have hyl : 1 ≤ ys.length := by
          cases ys with
          | nil => contradiction
          | cons y ys => simp
        omega
      · have iht := ih htail
        rw [iht]
        have hxl : 0 < xs.length := by
          cases xs with
          | nil => contradiction
          | cons y ys => simp
        have hyl : 0 < ys.length := by
          cases ys with
          | nil => contradiction
          | cons y ys => simp
        omega
'''

probes = {
'zipAddPad_length_v2': helpers + r'''
theorem zipAddPad_length_probe (p : Nat) (xs ys : List Nat) :
    (Galoistools.zipAddPad p xs ys).length = Nat.max xs.length ys.length :=
  zipAddPad_length_v2 p xs ys
''',
'convolve_length_nonempty_v2': helpers + r'''
theorem convolve_length_nonempty_probe (p : Nat) (xs ys : List Nat)
    (hxs : xs ≠ []) (hys : ys ≠ []) :
    (Galoistools.convolve p xs ys).length = xs.length + ys.length - 1 :=
  convolve_length_nonempty_v2 p xs ys hxs hys
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
    item={'probe':name,'exit':cp.returncode,'errors':errors[-12:],'residual':goals[-3:],'raw_tail':'\n'.join(lines[-400:]) if cp.returncode else ''}
    census.append(item)
    print(f'=== {name} EXIT {cp.returncode} ===')
    if cp.returncode: print(item['raw_tail'])

outdir=Path('mul_shape_v2'); outdir.mkdir(exist_ok=True)
(outdir/'census.json').write_text(json.dumps(census,indent=2))
print('MUL_SHAPE_V2_CENSUS',json.dumps(census))
