from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox
bench=Path('benchmarks/galoistools').resolve(); seed=read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out=Path('add_strip_invariance_v1/source').resolve(); create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)
h='''import Galoistools.Proof.Ring\n\nnamespace GaloistoolsAddStripInvariantV1\n'''; ft='\nend GaloistoolsAddStripInvariantV1\n'
probes={
'leading_zero_add':r'''
theorem leading_zero_add (p : Nat) (f g : List Nat) :
    Galoistools.gfAdd (0 :: f) g p = Galoistools.gfAdd f g p := by
  simp only [Galoistools.gfAdd, List.reverse_cons]
''',
'leading_zero_add_cases':r'''
theorem leading_zero_add_cases (p : Nat) (f g : List Nat) :
    Galoistools.gfAdd (0 :: f) g p = Galoistools.gfAdd f g p := by
  simp only [Galoistools.gfAdd, List.reverse_cons]
  induction f generalizing g with
  | nil => cases g <;> simp [Galoistools.zipAddPad, Galoistools.gfStrip]
  | cons a f ih =>
      cases g with
      | nil => simp [Galoistools.zipAddPad, Galoistools.gfStrip]
      | cons b g =>
          simp only [List.reverse_cons]
          sorry
''',
'add_strip_left_from_leading':r'''
theorem leading_zero_add_local (p : Nat) (f g : List Nat) :
    Galoistools.gfAdd (0 :: f) g p = Galoistools.gfAdd f g p := by
  simp only [Galoistools.gfAdd, List.reverse_cons]
  -- expose the exact low-end padding residual
  simp [Galoistools.zipAddPad, Galoistools.gfStrip]

theorem add_strip_left_from_leading (p : Nat) (f g : List Nat) :
    Galoistools.gfAdd (Galoistools.gfStrip f) g p = Galoistools.gfAdd f g p := by
  induction f with
  | nil => rfl
  | cons a f ih =>
      by_cases ha : a = 0
      · simp only [Galoistools.gfStrip, ha, if_true]
        rw [ih]
        symm
        exact leading_zero_add_local p f g
      · simp [Galoistools.gfStrip, ha]
'''
}
c=[]
for n,t in probes.items():
 p=out/f'Probe_{n}.lean'; p.write_text(h+t+ft); cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True); raw=cp.stdout+'\n'+cp.stderr; ls=raw.splitlines(); goals=[]
 for k,l in enumerate(ls):
  if '⊢ ' in l or l.startswith('case '): goals.append('\n'.join(ls[k:k+100]))
 c.append({'probe':n,'exit':cp.returncode,'errors':[l for l in ls if 'error:' in l or 'unknown identifier' in l][-10:],'residual':goals[-3:],'tail':'\n'.join(ls[-350:]) if cp.returncode else ''}); print('===',n,cp.returncode,'==='); print(c[-1]['tail'] if cp.returncode else '')
Path('add_strip_invariance_v1').mkdir(exist_ok=True); Path('add_strip_invariance_v1/census.json').write_text(json.dumps(c,indent=2))
