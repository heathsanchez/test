from pathlib import Path
import subprocess, json
from vero.generation.extractor import read_artifact
from vero.generation.sandbox import create_sandbox

bench=Path('benchmarks/galoistools').resolve()
seed=read_artifact(Path('../baseline27/allin_artifact.json').resolve())
out=Path('div_step_cancel_v1/source').resolve()
create_sandbox(bench,out,mode='codeproof',overwrite=True,seed_artifact=seed)

header='''import Galoistools.Proof.Ring\nimport Galoistools.Impl.Division\nimport Galoistools.Spec.Division\n\nnamespace DivStepCancelV1\n'''
footer='\nend DivStepCancelV1\n'

probes={
'sub_add_cancel_unfold': r'''
theorem sub_add_cancel_unfold (p : Nat) (cur sub : List Nat)
    (hn : Galoistools.IsNorm p cur) :
    Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p = cur := by
  simp only [Galoistools.gfAdd, Galoistools.gfSub]
''',
'sub_add_cancel_via_neg': r'''
theorem sub_add_cancel_via_neg (p : Nat) (cur sub : List Nat)
    (hp : 1 < p) (hn : Galoistools.IsNorm p cur) :
    Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p = cur := by
  rw [prove_sub_eq_add_neg cur sub p hp]
'''
}

res=[]
for name,body in probes.items():
 p=out/f'Probe_{name}.lean'; p.write_text(header+body+footer)
 cp=subprocess.run(['lake','lean',p.name],cwd=out,text=True,capture_output=True)
 raw=cp.stdout+'\n'+cp.stderr
 print(f'=== {name} EXIT {cp.returncode} ===')
 if cp.returncode: print(raw[-18000:])
 res.append({'probe':name,'exit':cp.returncode,'tail':raw[-24000:] if cp.returncode else ''})
Path('div_step_cancel_v1').mkdir(exist_ok=True)
Path('div_step_cancel_v1/result.json').write_text(json.dumps(res,indent=2))
