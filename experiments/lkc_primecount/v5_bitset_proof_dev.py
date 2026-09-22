#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"flash_v5_bitset_probe.py"))
src=(OUT/"Submission_v5_bitset_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

proof=r'''
/-! Foundational bit semantics for the V5 sieve proof. -/

theorem clearBitIfSet_testBit (bits i j : Nat) :
    (clearBitIfSet bits i).testBit j =
      (if j = i then false else bits.testBit j) := by
  unfold clearBitIfSet
  by_cases hb : bits.testBit i = true
  · simp only [hb, if_pos, Nat.testBit_xor, Nat.testBit_shiftLeft]
    have hv := (@Nat.testBit_one_eq_true_iff_self_eq_zero (j - i))
    grind
  · have hb' : bits.testBit i = false := by
      cases h : bits.testBit i <;> simp_all
    simp only [hb']
    by_cases hji : j = i
    · subst j
      simp [hb']
    · simp [hji]


theorem clearMultiples_below
    (fuel n p m bits j : Nat) (hj : j < m) :
    (clearMultiples fuel n p m bits).testBit j = bits.testBit j := by
  induction fuel generalizing m bits with
  | zero =>
      rfl
  | succ fuel ih =>
      rw [clearMultiples]
      by_cases hnm : n < m
      · rw [if_pos hnm]
      · rw [if_neg hnm]
        rw [ih (m + p) (clearBitIfSet bits m) (by omega)]
        rw [clearBitIfSet_testBit]
        simp [Nat.ne_of_lt hj]

theorem clearMultiples_hits
    (fuel n p m bits k : Nat)
    (hp : 0 < p) (hf : k < fuel) (hi : m + k * p ≤ n) :
    (clearMultiples fuel n p m bits).testBit (m + k * p) = false := by
  induction k generalizing fuel m bits with
  | zero =>
      cases fuel with
      | zero => omega
      | succ fuel =>
          rw [clearMultiples]
          rw [if_neg (by omega : ¬ n < m)]
          have hlt : m < m + p := by omega
          simp only [Nat.zero_mul, Nat.add_zero]
          rw [clearMultiples_below fuel n p (m + p)
            (clearBitIfSet bits m) m hlt]
          rw [clearBitIfSet_testBit]
          simp
  | succ k ih =>
      cases fuel with
      | zero => omega
      | succ fuel =>
          rw [clearMultiples]
          have hmle : m ≤ n := by
            have := hi
            omega
          rw [if_neg (by omega : ¬ n < m)]
          have ht : m + (k + 1) * p = (m + p) + k * p := by
            simp [Nat.succ_mul, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
          rw [ht]
          apply ih fuel (m + p) (clearBitIfSet bits m)
          · omega
          · rw [← ht]
            exact hi

theorem initialPrimeBits_testBit (n i : Nat) :
    ((((1 <<< (n + 1)) - 1) ^^^ 3).testBit i) =
      ((decide (i < n + 1)) ^^ ((3 : Nat).testBit i)) := by
  simp only [Nat.testBit_xor, Nat.testBit_two_pow_sub_one,
    Nat.shiftLeft_eq, Nat.one_mul]

theorem initialPrimeBits_between (n i : Nat)
    (hi : i ≤ n) :
    ((((1 <<< (n + 1)) - 1) ^^^ 3).testBit i) =
      decide (2 ≤ i) := by
  rw [initialPrimeBits_testBit]
  have hlt : i < n + 1 := by omega
  simp only [hlt, decide_true, Bool.true_xor]
  have h0 := (@Nat.testBit_one_eq_true_iff_self_eq_zero i)
  have h1 := (@Nat.testBit_one_eq_true_iff_self_eq_zero (i - 1))
  by_cases hi0 : i = 0
  · subst i
    decide
  · by_cases hi1 : i = 1
    · subst i
      decide
    · have h2 : 2 ≤ i := by omega
      have h3 : (3 : Nat).testBit i = false := by
        have hlt4 : 3 < 2 ^ i := by
          have : 4 ≤ 2 ^ i := by
            exact Nat.pow_le_pow_right (by trivial : 0 < 2) h2
          omega
        exact Nat.testBit_lt_two_pow hlt4
      simp [h2, h3]
'''

text=prefix+"\n"+proof+"\nend Submission\n"
p=OUT/"Submission_v5_bitset_proof_dev.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
