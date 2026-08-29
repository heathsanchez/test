from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_add_semantics_v19').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreAddSemanticsV19

-- V18 verified primitive: stripping leading zero coefficients is evaluation-neutral mod p.
theorem revaux_append_zero_mod (p x : Nat) : ∀ xs : List Nat,
    Galoistools.refPolyEvalRevAux p x (xs ++ [0]) % p =
    Galoistools.refPolyEvalRevAux p x xs % p := by
  intro xs
  induction xs with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih =>
      simp [Galoistools.refPolyEvalRevAux, ih, Nat.add_mod, Nat.mul_mod]

theorem gfStrip_cons_zero (as : List Nat) :
    Galoistools.gfStrip (0 :: as) = Galoistools.gfStrip as := by
  simp [Galoistools.gfStrip]

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
        rw [gfStrip_cons_zero]
        simp only [List.reverse_cons]
        rw [ih]
        exact (revaux_append_zero_mod p x as.reverse).symm
      · simp [Galoistools.gfStrip, h]

-- Next exact primitive: coefficientwise padded addition is Horner-evaluation addition modulo p.
theorem revaux_zipAddPad_mod (p x : Nat) : ∀ as bs : List Nat,
    Galoistools.refPolyEvalRevAux p x (Galoistools.zipAddPad p as bs) % p =
      (Galoistools.refPolyEvalRevAux p x as +
       Galoistools.refPolyEvalRevAux p x bs) % p := by
  intro as
  induction as with
  | nil =>
      intro bs
      induction bs with
      | nil => simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux]
      | cons b bs ih =>
          simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux, ih,
            Nat.add_mod, Nat.mul_mod]
  | cons a as ih =>
      intro bs
      cases bs with
      | nil =>
          induction as generalizing a with
          | nil => simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux,
              Nat.add_mod, Nat.mul_mod]
          | cons a' as' ih' =>
              simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux, ih',
                Nat.add_mod, Nat.mul_mod]
      | cons b bs =>
          simp [Galoistools.zipAddPad, Galoistools.refPolyEvalRevAux, ih bs,
            Nat.add_mod, Nat.mul_mod]

end VeroDivCoreAddSemanticsV19
'''
(P/'DivCoreAddSemanticsV19.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V19_ADD_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreAddSemanticsV19.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V19_ADD_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
