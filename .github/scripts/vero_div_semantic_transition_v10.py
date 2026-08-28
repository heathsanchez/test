from pathlib import Path
import shutil, subprocess, json

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_div_semantic_transition_v10').resolve()
if OUT.exists(): shutil.rmtree(OUT)
shutil.copytree(SOURCE,OUT)
for c in OUT.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=OUT/'SemanticTransitionV10.lean'
probe.write_text(r'''import Galoistools.Proof.Ring
import Galoistools.Impl.Division

open Galoistools

namespace SemanticTransitionV10

def samples : List (List Nat) :=
  [[], [0], [1], [2], [1,0], [0,1], [1,1], [2,1], [1,0,1], [2,2,1]]

def ps : List Nat := [2,3,5,7]
def xs : List Nat := [0,1,2,3]
def cs : List Nat := [0,1,2,3]
def ss : List Nat := [0,1,2,3]

def listEqWitnesses : List (Nat × Nat × List Nat) :=
  (cs.flatMap fun c => ss.flatMap fun s => samples.filterMap fun g =>
    let lhs := gfMul (shiftUp s [c]) g 5
    let rhs := shiftUp s (scaleP 5 c g)
    if lhs = rhs then none else some (c,s,g))

def semanticBad : List (Nat × Nat × Nat × Nat × List Nat) :=
  ps.flatMap fun p => xs.flatMap fun x => cs.flatMap fun c => ss.flatMap fun s =>
    samples.filterMap fun g =>
      let lhs := refPolyEval p (gfMul (shiftUp s [c]) g p) x
      let rhs := refPolyEval p (shiftUp s (scaleP p c g)) x
      if lhs = rhs then none else some (p,x,c,s,g)

#eval (listEqWitnesses.length, listEqWitnesses.take 12)
#eval (semanticBad.length, semanticBad.take 12)

end SemanticTransitionV10
''')
cp=subprocess.run(['lake','env','lean','SemanticTransitionV10.lean'],cwd=OUT,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
result={'exit':cp.returncode,'raw':raw[-24000:]}
(ROOT/'vero_div_semantic_transition_v10_result.json').write_text(json.dumps(result,indent=2))
print('VERO_DIV_SEMANTIC_TRANSITION_V10',json.dumps({'exit':cp.returncode,'tail':raw[-4000:]}))
raise SystemExit(cp.returncode)
