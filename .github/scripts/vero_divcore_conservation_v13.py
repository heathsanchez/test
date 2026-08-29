from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_conservation_v13').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools

namespace VeroDivCoreConservationV13

abbrev Poly := List Nat

def samples : List Poly :=
  [[], [0], [1], [2], [1,0], [0,1], [1,1], [2,1], [1,2], [1,0,1], [2,0,1], [1,2,1]]

def ps : List Nat := [2,3,5,7]
def xs : List Nat := [0,1,2,3,4,5,6]
def es : List Int := [0,1,2,3,4,5]

def completedQ (q : Poly) (e : Int) : Poly :=
  q ++ List.replicate (e + 1).toNat 0

def sem (p x : Nat) (q cur g : Poly) : Nat :=
  (refPolyEval p (gfMul q g p) x + refPolyEval p cur x) % p

def bad : List (Nat × Nat × Poly × Poly × Poly × Int × Int × Nat × Nat) :=
  ps.flatMap fun p => xs.flatMap fun x => samples.flatMap fun g => samples.flatMap fun cur =>
    samples.flatMap fun q => es.filterMap fun e =>
      let cur0 := gfStrip cur
      let dg := gfDegree g
      let dc := gfDegree cur0
      if g = [] || dc < dg then none else
      let s := dc - dg
      if s < 0 || e < s then none else
      let c := (leadCoeff cur0 * invMod (leadCoeff g) p) % p
      let gap := List.replicate (e - s).toNat 0
      let q' := q ++ gap ++ [c]
      let sub := shiftUp s.toNat (scaleP p c g)
      let cur' := gfSub cur0 sub p
      let before := sem p x (completedQ q e) cur0 g
      let after := sem p x (q' ++ List.replicate s.toNat 0) cur' g
      if before = after then none else some (p,x,g,cur0,q,e,s,before,after)

#eval (bad.length, bad.take 20)

end VeroDivCoreConservationV13
'''
(P/'DivCoreConservationV13.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V13_DIVCORE_CONSERVATION',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-10000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreConservationV13.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V13_DIVCORE_CONSERVATION',json.dumps({'stage':'census','exit':cp.returncode,'tail':raw[-12000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
