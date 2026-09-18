#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

/-- Explicit structural fuel version of Mathlib's odd least-factor search. -/
def minFacStructuralAux (n : Nat) : Nat → Nat → Nat
  | 0, _ => n
  | fuel + 1, k =>
      if n < k * k then n
      else if n % k = 0 then k
      else minFacStructuralAux n fuel (k + 2)

theorem minFacStructuralAux_eq (n fuel : Nat) : ∀ k, n < k + fuel →
    minFacStructuralAux n fuel k = Nat.minFacAux n k := by
  induction fuel with
  | zero =>
      intro k hk
      have hnk : n < k := by omega
      have hpos : 0 < k := by omega
      have hsq : n < k * k :=
        Nat.lt_of_lt_of_le hnk (Nat.le_mul_of_pos_right k hpos)
      rw [minFacStructuralAux, Nat.minFacAux, if_pos hsq]
  | succ fuel ih =>
      intro k hk
      rw [minFacStructuralAux, Nat.minFacAux]
      by_cases hsq : n < k * k
      · simp only [if_pos hsq]
      · simp only [if_neg hsq]
        by_cases hm : n % k = 0
        · have hd : k ∣ n := Nat.dvd_of_mod_eq_zero hm
          simp only [if_pos hm, if_pos hd]
        · have hd : ¬ k ∣ n := fun h => hm (Nat.mod_eq_zero_of_dvd h)
          simp only [if_neg hm, if_neg hd]
          exact ih (k + 2) (by omega)

def minFacStructural (n : Nat) : Nat :=
  if n % 2 = 0 then 2 else minFacStructuralAux n (n + 1) 3

theorem minFacStructural_eq (n : Nat) : minFacStructural n = n.minFac := by
  rw [minFacStructural, Nat.minFac_eq]
  simp only [Nat.dvd_iff_mod_eq_zero,
    minFacStructuralAux_eq n (n + 1) 3 (by omega)]

def isPrimeStructural (p : Nat) : Bool :=
  decide (2 ≤ p) && (minFacStructural p == p)

theorem isPrimeStructural_eq (p : Nat) :
    isPrimeStructural p = decide (Nat.Prime p) := by
  rw [isPrimeStructural, minFacStructural_eq]
  apply Bool.eq_iff_iff.mpr
  simp [Nat.prime_def_minFac]

def countDirectStructural : Nat → Nat
  | 0 => 0
  | n + 1 =>
      countDirectStructural n +
        if isPrimeStructural (n + 1) then 1 else 0

theorem primeCounting_succ_step (n : Nat) :
    Nat.primeCounting (n + 1) =
      Nat.primeCounting n + if Nat.Prime (n + 1) then 1 else 0 := by
  rw [← Nat.primesLE_card_eq_primeCounting (n + 1),
      ← Nat.primesLE_card_eq_primeCounting n,
      Nat.primesLE_succ]
  by_cases hp : Nat.Prime (n + 1)
  · simp [hp, Nat.notMem_primesLE]
  · simp [hp]

theorem countDirectStructural_eq (n : Nat) :
    countDirectStructural n = Nat.primeCounting n := by
  induction n with
  | zero =>
      simp [countDirectStructural]
  | succ n ih =>
      rw [countDirectStructural, ih, primeCounting_succ_step]
      simp [isPrimeStructural_eq]

def impl (n : Nat) : Nat := countDirectStructural n

theorem impl_correct : ∀ n, impl n = primeCountSpec n := by
  intro n
  exact countDirectStructural_eq n

end Submission
'''
p=OUT/"Submission_v3.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
