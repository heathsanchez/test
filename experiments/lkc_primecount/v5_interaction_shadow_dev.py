#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"v5_bitset_proof_dev.py"))
src=(OUT/"Submission_v5_bitset_proof_dev.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

extra=r'''
/-! Interaction-proof layer: least-factor semantic shadow. -/

def AliveAt (p i : Nat) : Prop :=
  Nat.Prime i ∨ p ≤ i.minFac

theorem clearBitIfSet_false_preserved
    (bits m i : Nat) (hi : bits.testBit i = false) :
    (clearBitIfSet bits m).testBit i = false := by
  rw [clearBitIfSet_testBit]
  by_cases h : i = m
  · simp [h]
  · simp [h, hi]

theorem clearMultiples_false_preserved
    (fuel n p m bits i : Nat)
    (hi : bits.testBit i = false) :
    (clearMultiples fuel n p m bits).testBit i = false := by
  induction fuel generalizing m bits with
  | zero =>
      exact hi
  | succ fuel ih =>
      rw [clearMultiples]
      by_cases hnm : n < m
      · rw [if_pos hnm]
        exact hi
      · rw [if_neg hnm]
        apply ih (m + p) (clearBitIfSet bits m)
        exact clearBitIfSet_false_preserved bits m i hi

theorem minFac_two_le_of_two_le (i : Nat) (hi : 2 ≤ i) :
    2 ≤ i.minFac := by
  have hne : i ≠ 1 := by omega
  exact (Nat.minFac_prime hne).two_le

theorem initialPrimeBits_alive
    (n i : Nat) (hi2 : 2 ≤ i) (hin : i ≤ n) :
    ((((1 <<< (n + 1)) - 1) ^^^ 3).testBit i) =
      decide (AliveAt 2 i) := by
  rw [initialPrimeBits_between n i hin]
  have hmf : 2 ≤ i.minFac := minFac_two_le_of_two_le i hi2
  simp [AliveAt, hi2, hmf]

theorem not_dvd_of_lt_minFac
    (p i : Nat) (hp2 : 2 ≤ p) (hpi : p < i.minFac) :
    ¬ p ∣ i := by
  intro hd
  have hle : i.minFac ≤ p := Nat.minFac_le_of_dvd hp2 hd
  omega

theorem alive_step_of_not_prime
    (p i : Nat) (hp2 : 2 ≤ p) (hi2 : 2 ≤ i)
    (hp : ¬ Nat.Prime p) :
    AliveAt p i ↔ AliveAt (p + 1) i := by
  constructor
  · intro h
    rcases h with hip | hmin
    · exact Or.inl hip
    · right
      by_contra hnot
      have hle : i.minFac ≤ p := by omega
      have heq : i.minFac = p := by omega
      have hmfprime : Nat.Prime i.minFac :=
        Nat.minFac_prime (by omega : i ≠ 1)
      have hp' : Nat.Prime p := by simpa [heq] using hmfprime
      exact hp hp'
  · intro h
    rcases h with hip | hmin
    · exact Or.inl hip
    · exact Or.inr (by omega)

theorem alive_next_not_dvd
    (p i : Nat) (hp2 : 2 ≤ p) (hi2 : 2 ≤ i)
    (h : AliveAt (p + 1) i) (hne : i ≠ p) :
    ¬ p ∣ i := by
  rcases h with hip | hmin
  · intro hd
    have hpprime : Nat.Prime p := by
      have hpi := (Nat.prime_dvd_prime_iff_eq
        (Nat.minFac_prime (by omega : p ≠ 1)) hip)
      -- If p is not itself prime, minFac p supplies a strictly smaller divisor;
      -- if it is prime, prime divisibility forces equality.  The former branch
      -- is dispatched by least-factor minimality below.
      by_cases hpp : Nat.Prime p
      · exact hpp
      · have hfac : p.minFac ∣ p := Nat.minFac_dvd p
        have hfacp : Nat.Prime p.minFac :=
          Nat.minFac_prime (by omega : p ≠ 1)
        have hd' : p.minFac ∣ i := dvd_trans hfac hd
        have heq := (Nat.prime_dvd_prime_iff_eq hfacp hip).mp hd'
        have hle := Nat.minFac_le p (by omega)
        omega
    exact hne ((Nat.prime_dvd_prime_iff_eq hpprime hip).mp hd)
  · exact not_dvd_of_lt_minFac p i hp2 (by omega)
'''

p=OUT/"Submission_v5_interaction_shadow_dev.lean"
p.write_text(prefix+"\n"+extra+"\nend Submission\n")
print(f"generated {p} bytes={len(p.read_bytes())}")
