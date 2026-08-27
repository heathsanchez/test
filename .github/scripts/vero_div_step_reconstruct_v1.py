from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench=Path('benchmarks/galoistools').resolve()
seed=read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out=Path('div_step_reconstruct_v1/source').resolve()
create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)
header='''import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\nimport Galoistools.Spec.Division\n\nnamespace GaloistoolsDivStepReconstructV1\n'''
footer='\nend GaloistoolsDivStepReconstructV1\n'
common=r'''
theorem sub_eq_add_neg_local (f g : List Nat) (p : Nat) (hp : 1 < p) :
    Galoistools.gfSub f g p = Galoistools.gfAdd f (Galoistools.gfNeg g p) p := by
  have h := prove_sub_eq_add_neg
  simp only [spec_sub_eq_add_neg, canonical] at h
  exact h f g p hp
'''
probes={
'add_sub_cancel_norm':common+r'''
theorem add_sub_cancel_norm (cur sub : List Nat) (p : Nat)
    (hp : 1 < p) (hcur : Galoistools.IsNorm p cur) :
    Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p = cur := by
  rw [sub_eq_add_neg_local cur sub p hp]
  simp only [Galoistools.gfAdd, Galoistools.gfNeg]
''',
'add_sub_cancel_norm_both':common+r'''
theorem add_sub_cancel_norm_both (cur sub : List Nat) (p : Nat)
    (hp : 1 < p) (hcur : Galoistools.IsNorm p cur) (hsub : Galoistools.IsNorm p sub) :
    Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p = cur := by
  rw [sub_eq_add_neg_local cur sub p hp]
  simp only [Galoistools.gfAdd, Galoistools.gfNeg]
'''
}
c=[]
for name,text in probes.items():
 p=out/f'Probe_{name}.lean'; p.write_text(header+text+footer)
 cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
 raw=cp.stdout+'\n'+cp.stderr; ls=raw.splitlines(); goals=[]
 for k,l in enumerate(ls):
  if '⊢ ' in l or l.startswith('case '): goals.append('\n'.join(ls[k:k+120]))
 item={'probe':name,'exit':cp.returncode,'errors':[l for l in ls if 'error:' in l or 'unknown identifier' in l][-12:],'residual':goals[-3:],'raw_tail':'\n'.join(ls[-450:]) if cp.returncode else ''}
 c.append(item); print('===',name,'EXIT',cp.returncode,'==='); print(item['raw_tail'] if cp.returncode else '')
Path('div_step_reconstruct_v1').mkdir(exist_ok=True); Path('div_step_reconstruct_v1/census.json').write_text(json.dumps(c,indent=2))
