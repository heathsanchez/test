#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

structure PairState where
  f : Nat
  g : Nat

theorem add_eq (a b : Nat) : Nat.add a b = a+b := rfl
theorem sub_eq (a b : Nat) : Nat.sub a b = a-b := rfl
theorem mul_eq (a b : Nat) : Nat.mul a b = a*b := rfl
theorem div_eq (a b : Nat) : Nat.div a b = a/b := rfl
theorem mod_eq (a b : Nat) : Nat.mod a b = a%b := rfl

def pairStep (recur : Nat → PairState) (n : Nat) : PairState :=
  bif n.beq 0 then ⟨0,1⟩ else
    match recur (Nat.div n 2) with
    | ⟨a,b⟩ =>
      let c := Nat.mul a (Nat.sub (Nat.mul 2 b) a)
      let d := Nat.add (Nat.mul b b) (Nat.mul a a)
      bif (Nat.mod n 2).beq 0 then ⟨c,d⟩ else ⟨d,Nat.add c d⟩

def pairRec (fuel : Nat) : Nat → PairState :=
  Nat.rec (fun _ => ⟨0,1⟩) (fun _ recur => pairStep recur) fuel

theorem pairRec_correct (fuel n : Nat) (h : n < 2^fuel) :
    pairRec fuel n = ⟨Nat.fib n, Nat.fib (n+1)⟩ := by
  induction fuel generalizing n with
  | zero =>
      have hn : n=0 := by simpa using h
      subst n
      rfl
  | succ fuel ih =>
      change pairStep (pairRec fuel) n = _
      unfold pairStep
      simp only [Bool.cond_eq_ite, Nat.beq_eq, add_eq, sub_eq, mul_eq, div_eq, mod_eq]
      by_cases hn : n=0
      · subst n
        rfl
      · rw [if_neg hn]
        have hk : n/2 < 2^fuel := by
          rw [pow_succ] at h
          omega
        rw [ih (n/2) hk]
        dsimp only
        rw [← Nat.fib_two_mul]
        have hodd (k : Nat) :
            Nat.fib (k+1)*Nat.fib (k+1)+Nat.fib k*Nat.fib k =
              Nat.fib (2*k+1) := by
          simpa only [pow_two] using (Nat.fib_two_mul_add_one k).symm
        rw [hodd]
        split_ifs with hp
        · congr 1 <;> congr 1 <;> omega
        · rw [← Nat.fib_add_two]
          congr 1 <;> congr 1 <;> omega

def impl (n : Nat) : Nat :=
  match pairRec n (Nat.div n 2) with
  | ⟨a,b⟩ =>
      bif (Nat.mod n 2).beq 0 then Nat.mul a (Nat.sub (Nat.mul 2 b) a)
      else Nat.add (Nat.mul b b) (Nat.mul a a)

theorem impl_correct : ∀ n, impl n = Nat.fib n := by
  intro n
  unfold impl
  simp only [Bool.cond_eq_ite, Nat.beq_eq, add_eq, sub_eq, mul_eq, div_eq, mod_eq]
  have hk : n/2 < 2^n := by
    have hn : n < 2^n := Nat.lt_pow_self (by decide)
    omega
  rw [pairRec_correct n (n/2) hk]
  dsimp only
  split_ifs with hp
  · change Nat.fib (n/2)*(2*Nat.fib (n/2+1)-Nat.fib (n/2)) = _
    rw [← Nat.fib_two_mul]
    congr 1
    omega
  · change Nat.fib (n/2+1)*Nat.fib (n/2+1)+Nat.fib (n/2)*Nat.fib (n/2)=_
    rw [← pow_two, ← pow_two, ← Nat.fib_two_mul_add_one]
    congr 1
    omega

end Submission
'''
p=OUT/"Submission_v7_boolpair.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
