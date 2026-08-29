from pathlib import Path
import json, shutil, subprocess

ROOT=Path.cwd(); SOURCE=(ROOT/'coldcert'/'project').resolve(); OUT=(ROOT/'vero_divcore_recursive_bridge_v21').resolve()
if OUT.exists(): shutil.rmtree(OUT)
OUT.mkdir(); P=OUT/'source'; shutil.copytree(SOURCE,P)
for c in P.rglob('.lake'):
    if c.is_dir(): shutil.rmtree(c)

probe=r'''
import Galoistools.Proof.Ring
import Galoistools.Impl.Division
import Galoistools.Spec.Division

open Galoistools
namespace VeroDivCoreRecursiveBridgeV21

@[simp] theorem eval_reduced (p x : Nat) (hp : 0 < p) : ∀ xs : List Nat,
    Galoistools.refPolyEval p xs x % p = Galoistools.refPolyEval p xs x := by
  intro xs; unfold Galoistools.refPolyEval
  induction xs.reverse with
  | nil => simp [Galoistools.refPolyEvalRevAux]
  | cons a as ih => simp [Galoistools.refPolyEvalRevAux]

@[simp] theorem eval_append_zero (p x : Nat) (f : List Nat) :
    Galoistools.refPolyEval p (f ++ [0]) x = (Galoistools.refPolyEval p f x * x) % p := by
  simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux, Nat.mul_comm]

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
      rw [ih (f := f ++ [0]), eval_append_zero, Nat.pow_succ]
      have hmod : NatModEq p (((Galoistools.refPolyEval p f x * x) % p) * x^n)
          ((Galoistools.refPolyEval p f x * x) * x^n) := by
        apply natModEq_mul
        · exact natModEq_mod_left (by rfl)
        · rfl
      unfold NatModEq at hmod
      simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hmod

@[simp] theorem mul_eval_hom (p x : Nat) (u v : List Nat) :
    Galoistools.refPolyEval p (Galoistools.gfMul u v p) x =
      (Galoistools.refPolyEval p u x * Galoistools.refPolyEval p v x) % p := by
  simp only [Galoistools.gfMul]
  by_cases hzero : u = [] ∨ v = []
  · rw [if_pos hzero]
    rcases hzero with rfl | rfl <;>
      simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux]
  · rw [if_neg hzero, refPolyEval_gfStrip]
    simp only [Galoistools.refPolyEval, List.reverse_reverse]
    have hconv := natModEq_refPolyEvalRevAux_convolve p x u.reverse v.reverse
    unfold NatModEq at hconv
    have hevalmod :
        Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) % p =
        Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) := by
      cases Galoistools.convolve p u.reverse v.reverse <;>
        simp [Galoistools.refPolyEvalRevAux]
    calc
      Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) =
        Galoistools.refPolyEvalRevAux p x
          (Galoistools.convolve p u.reverse v.reverse) % p := hevalmod.symm
      _ = (Galoistools.refPolyEvalRevAux p x u.reverse *
            Galoistools.refPolyEvalRevAux p x v.reverse) % p := hconv

theorem scaleP_eval_mod (p x c : Nat) (g : List Nat) :
    NatModEq p
      (Galoistools.refPolyEval p (Galoistools.scaleP p c g) x)
      (c * Galoistools.refPolyEval p g x) := by
  unfold Galoistools.scaleP
  rw [refPolyEval_gfStrip]
  unfold Galoistools.refPolyEval
  rw [← List.map_reverse]
  have h := natModEq_refPolyEvalRevAux_map_mul p x c g.reverse
  simpa [Nat.mul_comm] using h

theorem shiftUp_eval_mod (p x s : Nat) (f : List Nat) (hp : 0 < p) :
    NatModEq p
      (Galoistools.refPolyEval p (Galoistools.shiftUp s f) x)
      (Galoistools.refPolyEval p f x * x^s) := by
  unfold Galoistools.shiftUp
  by_cases hf : f = []
  · subst f
    unfold NatModEq
    simp [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux]
  · rw [if_neg hf, eval_append_zeros p x s f hp]
    exact natModEq_mod_left (by rfl)

theorem quotient_sub_bridge (p x c s : Nat) (g : List Nat) (hp : 0 < p) :
    NatModEq p
      (Galoistools.refPolyEval p
        (Galoistools.gfMul (Galoistools.shiftUp s [c]) g p) x)
      (Galoistools.refPolyEval p
        (Galoistools.shiftUp s (Galoistools.scaleP p c g)) x) := by
  have hmono := shiftUp_eval_mod p x s [c] hp
  have hscale := scaleP_eval_mod p x c g
  have hscaledShift := shiftUp_eval_mod p x s (Galoistools.scaleP p c g) hp
  have hscaleMul : NatModEq p
      (Galoistools.refPolyEval p (Galoistools.scaleP p c g) x * x^s)
      ((c * Galoistools.refPolyEval p g x) * x^s) := by
    apply natModEq_mul
    · exact hscale
    · rfl
  unfold NatModEq at hmono hscale hscaledShift hscaleMul ⊢
  rw [mul_eval_hom]
  calc
    ((Galoistools.refPolyEval p (Galoistools.shiftUp s [c]) x *
        Galoistools.refPolyEval p g x) % p) % p =
      ((Galoistools.refPolyEval p (Galoistools.shiftUp s [c]) x % p) *
        Galoistools.refPolyEval p g x) % p := by simp [Nat.mul_mod]
    _ = (((Galoistools.refPolyEval p [c] x * x^s) % p) *
        Galoistools.refPolyEval p g x) % p := by rw [hmono]
    _ = (((c * Galoistools.refPolyEval p g x) * x^s) % p) := by
      have hreassoc :
          (c * x^s) * Galoistools.refPolyEval p g x =
            (c * Galoistools.refPolyEval p g x) * x^s := by
        simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      have hmod := congrArg (fun z : Nat => z % p) hreassoc
      simpa [Galoistools.refPolyEval, Galoistools.refPolyEvalRevAux,
        Nat.mul_mod] using hmod
    _ = (Galoistools.refPolyEval p (Galoistools.scaleP p c g) x * x^s) % p := hscaleMul.symm
    _ = Galoistools.refPolyEval p (Galoistools.shiftUp s (Galoistools.scaleP p c g)) x % p := hscaledShift.symm

end VeroDivCoreRecursiveBridgeV21
'''
(P/'DivCoreRecursiveBridgeV21.lean').write_text(probe)
build=subprocess.run(['lake','build','Galoistools.Proof.Ring','Galoistools.Impl.Division','Galoistools.Spec.Division'],cwd=P,text=True,capture_output=True,timeout=300)
if build.returncode:
    raw=build.stdout+'\n'+build.stderr
    print('V21_RECURSIVE_BRIDGE_GATE',json.dumps({'stage':'build','exit':build.returncode,'tail':raw[-12000:]})); raise SystemExit(1)
cp=subprocess.run(['lake','env','lean','DivCoreRecursiveBridgeV21.lean'],cwd=P,text=True,capture_output=True,timeout=300)
raw=cp.stdout+'\n'+cp.stderr
print('V21_RECURSIVE_BRIDGE_GATE',json.dumps({'stage':'lemma','exit':cp.returncode,'tail':raw[-20000:]}))
(OUT/'result.json').write_text(json.dumps({'exit':cp.returncode,'raw':raw},indent=2))
raise SystemExit(cp.returncode)
