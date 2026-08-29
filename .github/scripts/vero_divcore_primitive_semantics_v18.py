from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_primitive_semantics_v18').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCorePrimitiveSemanticsV18

-- Exact residual from V17: a trailing zero in the reversed/Horner list
-- does not change evaluation modulo p.
theorem revaux_append_zero_mod (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x (xs ++ [0]) % p =
    Galoistools.refPolyEvalRevAux p x xs % p := by
  intro xs
  induction xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      simp [Galoistools.refPolyEvalRevAux, ih, Nat.add_mod, Nat.mul_mod]

-- First primitive semantic interface: canonical stripping is evaluation-neutral mod p.
theorem strip_eval_mod (p x : Nat) (f : List Nat) :
    NatModEq p
      (Galoistools.refPolyEval p (Galoistools.gfStrip f) x)
      (Galoistools.refPolyEval p f x) := by
  unfold NatModEq Galoistools.refPolyEval
  induction f with
  | nil => simp [Galoistools.gfStrip, Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      by_cases h : a = 0
      · subst a
        change Galoistools.refPolyEvalRevAux p x (Galoistools.gfStrip as).reverse % p =
          Galoistools.refPolyEvalRevAux p x (as.reverse ++ [0]) % p
        rw [ih]
        exact (revaux_append_zero_mod p x as).symm
      · simp [Galoistools.gfStrip, h]

end VeroDivCorePrimitiveSemanticsV18
'''
(P/'DivCorePrimitiveSemanticsV18.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V18_PRIMITIVE_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCorePrimitiveSemanticsV18.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V18_PRIMITIVE_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
