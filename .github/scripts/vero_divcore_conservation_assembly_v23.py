from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_conservation_assembly_v23').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreConservationAssemblyV23

-- Algebraic conservation law needed to compose the verified quotient-padding,
-- quotient/subtrahend bridge, and subtraction-cancellation lemmas.
theorem conservation_compose
    (p oldQ newQ mono sub oldCur newCur : Nat)
    (hquot : NatModEq p newQ (oldQ + mono))
    (hbridge : NatModEq p mono sub)
    (hcancel : NatModEq p (newCur + sub) oldCur) :
    NatModEq p (newQ + newCur) (oldQ + oldCur) := by
  unfold NatModEq at hquot hbridge hcancel ⊢
  calc
    (newQ + newCur) % p = (newQ % p + newCur % p) % p := by simp [Nat.add_mod]
    _ = (((oldQ + mono) % p) + newCur % p) % p := by rw [hquot]
    _ = ((oldQ % p + mono % p) + newCur % p) % p := by simp [Nat.add_mod]
    _ = ((oldQ % p + sub % p) + newCur % p) % p := by rw [hbridge]
    _ = (oldQ % p + ((newCur + sub) % p)) % p := by
      simp [Nat.add_mod, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
    _ = (oldQ % p + oldCur % p) % p := by rw [hcancel]
    _ = (oldQ + oldCur) % p := by simp [Nat.add_mod]

end VeroDivCoreConservationAssemblyV23
'''
(P/'DivCoreConservationAssemblyV23.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V23_CONSERVATION_ASSEMBLY_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreConservationAssemblyV23.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V23_CONSERVATION_ASSEMBLY_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
