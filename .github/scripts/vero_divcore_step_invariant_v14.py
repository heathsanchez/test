from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_step_invariant_v14').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreStepInvariantV14

-- Algebraic hinge for the recursive divCore invariant: one subtraction step
-- can be exactly reversed by adding the same eliminated term back.
theorem divcore_step_cancel (p : Nat) (cur sub : List Nat)
    (hp : 1 < p) (hn : Galoistools.IsNorm p cur) :
    Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p = cur := by
  rw [prove_sub_eq_add_neg cur sub p hp]
  -- Ring-level normalization/cancellation should now decide the residual.
  simp [hn]

end VeroDivCoreStepInvariantV14
'''
(P/'DivCoreStepInvariantV14.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V14_DIVCORE_STEP_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreStepInvariantV14.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V14_DIVCORE_STEP_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-16000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
