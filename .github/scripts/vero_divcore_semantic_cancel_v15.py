from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_semantic_cancel_v15').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreSemanticCancelV15

-- Representation-stable version of the V14 hinge: canonicalization is allowed,
-- but evaluation must be unchanged by subtracting and re-adding the same term.
theorem divcore_semantic_cancel (p x : Nat) (cur sub : List Nat)
    (hp : 1 < p) (hn : Galoistools.IsNorm p cur) :
    Galoistools.refPolyEval p
      (Galoistools.gfAdd (Galoistools.gfSub cur sub p) sub p) x =
    Galoistools.refPolyEval p cur x := by
  simp [Galoistools.gfAdd, Galoistools.gfSub, Galoistools.refPolyEval]

end VeroDivCoreSemanticCancelV15
'''
(P/'DivCoreSemanticCancelV15.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V15_DIVCORE_SEMANTIC_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreSemanticCancelV15.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V15_DIVCORE_SEMANTIC_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
