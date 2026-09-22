#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"v5_invariant_dev.py"))
src=(OUT/"Submission_v5_invariant_dev.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

extra=r'''
/-! Prime transition: clear exactly the least-factor-p composite class. -/

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

theorem not_dvd_of_lt_minFac
    (p i : Nat) (hp2 : 2 ≤ p) (hpi : p < i.minFac) :
    ¬ p ∣ i := by
  intro hd
  have hle : i.minFac ≤ p := Nat.minFac_le_of_dvd hp2 hd
  omega

theorem clearMultiples_preserves_prime
    (n p bits i : Nat)
    (hp2 : 2 ≤ p) (hpp : Nat.Prime p) (hip : Nat.Prime i) :
    (clearMultiples (n + 1) n p (p * p) bits).testBit i =
      bits.testBit i := by
  by_cases hpi : p = i
  · subst i
    apply clearMultiples_below
    exact lt_mul_of_one_lt_right (by omega : 0 < p) (by omega : 1 < p)
  · apply clearMultiples_preserves_not_dvd
    · exact dvd_mul_right p p
    · intro hd
      have heq : p = i :=
        (Nat.prime_dvd_prime_iff_eq hpp hip).mp hd
      exact hpi heq

theorem prime_clear_step_inv
    (n p bits : Nat)
    (hp2 : 2 ≤ p) (hpp : Nat.Prime p)
    (hinv : SieveInv n p bits) :
    SieveInv n (p + 1)
      (clearMultiples (n + 1) n p (p * p) bits) := by
  intro i hi2 hin
  by_cases hip : Nat.Prime i
  · have hbefore : bits.testBit i = true :=
      (hinv i hi2 hin).2 (Or.inl hip)
    have hpres :=
      clearMultiples_preserves_prime n p bits i hp2 hpp hip
    have hafter :
        (clearMultiples (n + 1) n p (p * p) bits).testBit i = true := by
      rw [hpres]
      exact hbefore
    constructor
    · intro _
      exact Or.inl hip
    · intro _
      exact hafter
  · by_cases hlt : i.minFac < p
    · have hbefore_false : bits.testBit i = false := by
        cases hbit : bits.testBit i with
        | false => rfl
        | true =>
            exfalso
            have halive := (hinv i hi2 hin).1 hbit
            rcases halive with hpr | hmin
            · exact hip hpr
            · omega
      have hafter_false :=
        clearMultiples_false_preserved
          (n + 1) n p (p * p) bits i hbefore_false
      constructor
      · intro htrue
        rw [hafter_false] at htrue
        contradiction
      · intro halive
        rcases halive with hpr | hmin
        · exact (hip hpr).elim
        · omega
    · have hle : p ≤ i.minFac := Nat.le_of_not_gt hlt
      by_cases heq : i.minFac = p
      · have hnext_false : ¬ AliveAt (p + 1) i := by
          intro halive
          rcases halive with hpr | hmin
          · exact hip hpr
          · omega
        rcases composite_on_minFac_progression i (by omega) hip with ⟨k, hk⟩
        rw [heq] at hk
        have hsumle : p * p + k * p ≤ n := by
          rw [← hk]
          exact hin
        have hk_le_i : k ≤ i := by
          calc
            k ≤ k * p := Nat.le_mul_of_pos_right k (by omega)
            _ ≤ p * p + k * p := Nat.le_add_left _ _
            _ = i := hk.symm
        have hkfuel : k < n + 1 := by omega
        have hhit :=
          clearMultiples_hits
            (n + 1) n p (p * p) bits k
            (by omega) hkfuel hsumle
        constructor
        · intro htrue
          exfalso
          rw [hk] at htrue
          rw [hhit] at htrue
          contradiction
        · intro halive
          exact (hnext_false halive).elim
      · have hp_lt : p < i.minFac := by omega
        have hnotdvd : ¬ p ∣ i :=
          not_dvd_of_lt_minFac p i hp2 hp_lt
        have hpres :=
          clearMultiples_preserves_not_dvd
            (n + 1) n p (p * p) bits i
            (dvd_mul_right p p) hnotdvd
        have hbefore : bits.testBit i = true :=
          (hinv i hi2 hin).2 (Or.inr hle)
        have hafter :
            (clearMultiples (n + 1) n p (p * p) bits).testBit i = true := by
          rw [hpres]
          exact hbefore
        have hnext : AliveAt (p + 1) i :=
          Or.inr (by omega)
        constructor
        · intro _
          exact hnext
        · intro _
          exact hafter
'''

p=OUT/"Submission_v5_prime_step_dev.lean"
p.write_text(prefix+"\n"+extra+"\nend Submission\n")
print(f"generated {p} bytes={len(p.read_bytes())}")
