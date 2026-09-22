#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"v5_loop_dev.py"))
src=(OUT/"Submission_v5_loop_dev.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

extra=r'''
/-! Count bridge: independent of the packed sieve representation. -/

def countPrimeFuel : Nat → Nat → Nat
  | 0, _ => 0
  | fuel + 1, i =>
      (if Nat.Prime i then 1 else 0) + countPrimeFuel fuel (i + 1)

theorem countBits_eq_countPrimeFuel :
    ∀ fuel i bits,
      (∀ j, i ≤ j → j < i + fuel →
        (bits.testBit j = true ↔ Nat.Prime j)) →
      countBits fuel i bits = countPrimeFuel fuel i := by
  intro fuel
  induction fuel with
  | zero =>
      intro i bits h
      rfl
  | succ fuel ih =>
      intro i bits h
      have htail :
          countBits fuel (i + 1) bits =
            countPrimeFuel fuel (i + 1) := by
        apply ih
        intro j hjlo hjhi
        apply h j
        · omega
        · omega
      have hhere := h i (Nat.le_refl _) (by omega)
      by_cases hp : Nat.Prime i
      · have hb : bits.testBit i = true := hhere.mpr hp
        simp [countBits, countPrimeFuel, hb, hp, htail]
      · have hb : bits.testBit i = false := by
          cases hbit : bits.testBit i with
          | false => rfl
          | true =>
              exfalso
              exact hp (hhere.mp hbit)
        simp [countBits, countPrimeFuel, hb, hp, htail]

theorem countPrimeFuel_snoc :
    ∀ fuel i,
      countPrimeFuel (fuel + 1) i =
        countPrimeFuel fuel i +
          (if Nat.Prime (i + fuel) then 1 else 0) := by
  intro fuel
  induction fuel with
  | zero =>
      intro i
      simp [countPrimeFuel]
  | succ fuel ih =>
      intro i
      simp only [countPrimeFuel]
      rw [ih (i + 1)]
      have hidx : i + 1 + fuel = i + (fuel + 1) := by omega
      rw [hidx]
      omega

theorem primeCounting_succ_step (n : Nat) :
    Nat.primeCounting (n + 1) =
      Nat.primeCounting n + if Nat.Prime (n + 1) then 1 else 0 := by
  rw [← Nat.primesLE_card_eq_primeCounting (n + 1),
      ← Nat.primesLE_card_eq_primeCounting n,
      Nat.primesLE_succ]
  by_cases hp : Nat.Prime (n + 1)
  · simp [hp, Nat.notMem_primesLE]
  · simp [hp]

theorem countPrimeFuel_two_eq :
    ∀ fuel, countPrimeFuel fuel 2 = Nat.primeCounting (fuel + 1)
  | 0 => by
      simp [countPrimeFuel, Nat.primeCounting_one]
  | fuel + 1 => by
      rw [countPrimeFuel_snoc fuel 2]
      rw [countPrimeFuel_two_eq fuel]
      rw [primeCounting_succ_step (fuel + 1)]
      congr 2 <;> omega

theorem countBits_primeBits_eq
    (n : Nat) (hn : 2 ≤ n) :
    countBits (n - 1) 2 (primeBits n) = Nat.primeCounting n := by
  calc
    countBits (n - 1) 2 (primeBits n) =
        countPrimeFuel (n - 1) 2 := by
          apply countBits_eq_countPrimeFuel
          intro j hj2 hjlt
          apply primeBits_correct n j hj2
          omega
    _ = Nat.primeCounting ((n - 1) + 1) :=
          countPrimeFuel_two_eq (n - 1)
    _ = Nat.primeCounting n := by
          congr 1
          omega

theorem impl_correct : ∀ n, impl n = primeCountSpec n := by
  intro n
  unfold impl primeCountSpec
  by_cases hn : n < 2
  · rw [if_pos hn]
    exact Nat.primeCounting_eq_zero_iff.mpr (by omega)
  · rw [if_neg hn]
    exact countBits_primeBits_eq n (by omega)
'''

p=OUT/"Submission_v5_full_interaction_proof.lean"
p.write_text(prefix+"\n"+extra+"\nend Submission\n")
print(f"generated {p} bytes={len(p.read_bytes())}")
