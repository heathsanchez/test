#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"structural_v3.py"))
src=(OUT/"Submission_v3.lean").read_text()

old='''def countDirectStructural : Nat → Nat
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
'''

new='''theorem primeCounting_succ_step (n : Nat) :
    Nat.primeCounting (n + 1) =
      Nat.primeCounting n + if Nat.Prime (n + 1) then 1 else 0 := by
  rw [← Nat.primesLE_card_eq_primeCounting (n + 1),
      ← Nat.primesLE_card_eq_primeCounting n,
      Nat.primesLE_succ]
  by_cases hp : Nat.Prime (n + 1)
  · simp [hp, Nat.notMem_primesLE]
  · simp [hp]

/-- Count 2 once, then test only odd candidates 3,5,7,... . -/
def countOddStructural : Nat → Nat
  | 0 => 1
  | k + 1 =>
      countOddStructural k +
        if isPrimeStructural (2 * k + 3) then 1 else 0

theorem even_ge_four_not_prime (k : Nat) :
    ¬ Nat.Prime (2 * k + 4) := by
  intro hp
  have he : Even (2 * k + 4) := ⟨k + 2, by omega⟩
  have htwo := hp.even_iff.mp he
  omega

theorem countOddStructural_eq (k : Nat) :
    countOddStructural k = Nat.primeCounting (2 * k + 2) := by
  induction k with
  | zero =>
      have h1 := primeCounting_succ_step 1
      simp [countOddStructural, Nat.primeCounting_one] at h1 ⊢
  | succ k ih =>
      simp only [countOddStructural, ih, Nat.mul_succ]
      rw [show 2 * k + 2 + 1 = 2 * k + 3 by omega]
      rw [show 2 * k + 2 + 2 = 2 * k + 4 by omega]
      rw [primeCounting_succ_step (2 * k + 3)]
      rw [primeCounting_succ_step (2 * k + 2)]
      simp [isPrimeStructural_eq, even_ge_four_not_prime]

def impl (n : Nat) : Nat :=
  if n < 2 then 0
  else countOddStructural ((n - 1) / 2)

theorem impl_correct : ∀ n, impl n = primeCountSpec n := by
  intro n
  unfold primeCountSpec
  rw [impl]
  by_cases hsmall : n < 2
  · rw [if_pos hsmall]
    exact Nat.primeCounting_eq_zero_iff.mpr (by omega)
  · rw [if_neg hsmall]
    rw [countOddStructural_eq]
    rcases n.mod_two_eq_zero_or_one with heven | hodd
    · have harg : 2 * ((n - 1) / 2) + 2 = n := by omega
      rw [harg]
    · have harg : 2 * ((n - 1) / 2) + 2 = n + 1 := by omega
      rw [harg, primeCounting_succ_step n]
      have hnp : ¬ Nat.Prime (n + 1) := by
        intro hp
        rcases hp.eq_two_or_odd with htwo | hpodd
        · omega
        · omega
      simp [hnp]
'''

if old not in src:
    raise SystemExit("V3 counting block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v6_odd.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
