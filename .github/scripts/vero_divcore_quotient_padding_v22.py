from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_quotient_padding_v22').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreQuotientPaddingV22

@[simp] theorem eval_reduced (p x : Nat) (hp : 0 < p) : ∀ xs : List Nat,
    Galoistools.refPolyEval p xs x % p = Galoistools.refPolyEval p xs x := by
  intro xs; unfold Galoistools.refPolyEval
  induction xs.reverse with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux]

@[simp] theorem eval_append_coeff (p x a : Nat) (f : List Nat) :
    Galoistools.refPolyEval p (f ++ [a]) x =
      (Galoistools.refPolyEval p f x * x + a) % p := by
  simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux,
    Nat.mul_comm, Nat.add_comm, Nat.add_left_comm, Nat.add_assoc]

@[simp] theorem eval_append_zeros (p x n : Nat) (f : List Nat) (hp : 0 < p) :
    Galoistools.refPolyEval p (f ++ List.replicate n 0) x =
      (Galoistools.refPolyEval p f x * x^n) % p := by
  induction n generalizing f with
  | zero =>
      simp only [List.replicate_zero, List.append_nil, Nat.pow_zero, Nat.mul_one]
      exact (eval_reduced p x hp f).symm
  | succ n ih =>
      simp only [List.replicate_succ]
      rw [show f ++ 0 :: List.replicate n 0 = (f ++ [0]) ++ List.replicate n 0 by simp]
      rw [ih (f := f ++ [0]), eval_append_coeff, Nat.pow_succ]
      have hmod : NatModEq p (((Galoistools.refPolyEval p f x * x + 0) % p) * x^n)
          ((Galoistools.refPolyEval p f x * x) * x^n) := by
        apply natModEq_mul
        · unfold NatModEq
          simp
        · rfl
      unfold NatModEq at hmod
      simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hmod

-- The exact semantic effect of filling one zero in a completed quotient.
theorem quotient_padding_delta (p x c gap s : Nat) (q : List Nat) (hp : 0 < p) :
    NatModEq p
      (Galoistools.refPolyEval p
        (q ++ List.replicate gap 0 ++ [c] ++ List.replicate s 0) x)
      (Galoistools.refPolyEval p
        (q ++ List.replicate gap 0 ++ [0] ++ List.replicate s 0) x
       + c * x^s) := by
  let pre := q ++ List.replicate gap 0
  have hnew := eval_append_zeros p x s (pre ++ [c]) hp
  have hold := eval_append_zeros p x s (pre ++ [0]) hp
  rw [show q ++ List.replicate gap 0 ++ [c] ++ List.replicate s 0 =
      (pre ++ [c]) ++ List.replicate s 0 by simp [pre]]
  rw [show q ++ List.replicate gap 0 ++ [0] ++ List.replicate s 0 =
      (pre ++ [0]) ++ List.replicate s 0 by simp [pre]]
  rw [hnew, hold, eval_append_coeff, eval_append_coeff]
  have hdist :
      x^s * (Galoistools.refPolyEval p pre x * x + c) =
        x^s * (Galoistools.refPolyEval p pre x * x) + c * x^s := by
    rw [Nat.mul_add]
    simp [Nat.mul_comm]
  unfold NatModEq
  calc
    ((((Galoistools.refPolyEval p pre x * x + c) % p) * x^s) % p) % p =
      ((x^s * (Galoistools.refPolyEval p pre x * x + c)) % p) := by
        simp [Nat.mul_mod, Nat.mul_comm]
    _ = ((x^s * (Galoistools.refPolyEval p pre x * x) + c * x^s) % p) := by rw [hdist]
    _ = (((((Galoistools.refPolyEval p pre x * x + 0) % p) * x^s) % p) + c * x^s) % p := by
      simp [Nat.mul_mod, Nat.add_mod, Nat.mul_comm, Nat.mul_assoc]

end VeroDivCoreQuotientPaddingV22
'''
(P/'DivCoreQuotientPaddingV22.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V22_QUOTIENT_PADDING_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreQuotientPaddingV22.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V22_QUOTIENT_PADDING_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
