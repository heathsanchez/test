#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

structure PairState where
  f : Nat
  g : Nat

def pairStep (recur : Nat → PairState) (n : Nat) : PairState :=
  if n = 0 then ⟨0, 1⟩
  else
    match recur (n / 2) with
    | ⟨a,b⟩ =>
      let c := a * (2 * b - a)
      let d := b * b + a * a
      if n % 2 = 0 then ⟨c,d⟩ else ⟨d,c+d⟩

def pairRec (fuel : Nat) : Nat → PairState :=
  Nat.rec (fun _ => ⟨0,1⟩) (fun _ recur => pairStep recur) fuel

theorem pairRec_correct (fuel n : Nat) (h : n < 2^fuel) :
    pairRec fuel n = ⟨Nat.fib n, Nat.fib (n+1)⟩ := by
  induction fuel generalizing n with
  | zero =>
      have hn : n = 0 := by simpa using h
      subst n
      rfl
  | succ fuel ih =>
      change pairStep (pairRec fuel) n = _
      unfold pairStep
      by_cases hn : n = 0
      · simp [hn]
      · rw [if_neg hn]
        have hk : n / 2 < 2^fuel := by
          rw [pow_succ] at h
          omega
        rw [ih (n/2) hk]
        dsimp
        rw [← Nat.fib_two_mul]
        have hodd (k : Nat) :
            Nat.fib (k+1) * Nat.fib (k+1) + Nat.fib k * Nat.fib k =
              Nat.fib (2*k+1) := by
          simpa only [pow_two] using (Nat.fib_two_mul_add_one k).symm
        rw [hodd]
        split_ifs with hp
        · congr 1 <;> congr 1 <;> omega
        · rw [← Nat.fib_add_two]
          congr 1 <;> congr 1 <;> omega

def impl (n : Nat) : Nat :=
  match pairRec n (n/2) with
  | ⟨a,b⟩ =>
      let c := a * (2*b-a)
      let d := b*b+a*a
      if n%2=0 then c else d

theorem impl_correct : ∀ n, impl n = Nat.fib n := by
  intro n
  unfold impl
  have hk : n / 2 < 2^n := by
    have hn : n < 2^n := Nat.lt_pow_self (by decide)
    omega
  rw [pairRec_correct n (n/2) hk]
  dsimp
  split_ifs with hp
  · rw [← Nat.fib_two_mul]
    congr 1
    omega
  · rw [← pow_two, ← pow_two, ← Nat.fib_two_mul_add_one]
    congr 1
    omega

end Submission
'''
p=OUT/"Submission_v6_pairrec.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
