#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"v5_prime_step_dev.py"))
src=(OUT/"Submission_v5_prime_step_dev.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]

extra=r'''
/-! Structural closure of the exact V5 sieve. -/

theorem sieveLoop_correct :
    ∀ fuel n p bits,
      2 ≤ p →
      n < p + fuel →
      SieveInv n p bits →
      ∀ i, 2 ≤ i → i ≤ n →
        ((sieveLoop fuel n p bits).testBit i = true ↔ Nat.Prime i) := by
  intro fuel
  induction fuel with
  | zero =>
      intro n p bits hp2 hf hinv i hi2 hin
      have hpp : p ≤ p * p :=
        Nat.le_mul_of_pos_right p (by omega : 0 < p)
      have hstop : n < p * p := by omega
      simp only [sieveLoop]
      exact (hinv i hi2 hin).trans
        (alive_stop_iff_prime n p i hp2 hi2 hin hstop)
  | succ fuel ih =>
      intro n p bits hp2 hf hinv i hi2 hin
      rw [sieveLoop]
      by_cases hstop : n < p * p
      · rw [if_pos hstop]
        exact (hinv i hi2 hin).trans
          (alive_stop_iff_prime n p i hp2 hi2 hin hstop)
      · rw [if_neg hstop]
        have hsq : p * p ≤ n := Nat.le_of_not_gt hstop
        have hpp : p ≤ p * p :=
          Nat.le_mul_of_pos_right p (by omega : 0 < p)
        have hpn : p ≤ n := le_trans hpp hsq
        have hself :
            bits.testBit p = true ↔ Nat.Prime p :=
          (hinv p hp2 hpn).trans (alive_self_iff_prime p hp2)
        by_cases hp : Nat.Prime p
        · have hbit : bits.testBit p = true := hself.mpr hp
          simp only [hbit, if_true]
          exact ih n (p + 1)
            (clearMultiples (n + 1) n p (p * p) bits)
            (by omega) (by omega)
            (prime_clear_step_inv n p bits hp2 hp hinv)
            i hi2 hin
        · have hbit : bits.testBit p = false := by
            cases hb : bits.testBit p with
            | false => rfl
            | true =>
                exfalso
                exact hp (hself.mp hb)
          simp only [hbit, if_false]
          exact ih n (p + 1) bits
            (by omega) (by omega)
            (sieve_inv_step_of_not_prime n p bits hp2 hp hinv)
            i hi2 hin

theorem primeBits_correct
    (n i : Nat) (hi2 : 2 ≤ i) (hin : i ≤ n) :
    ((primeBits n).testBit i = true ↔ Nat.Prime i) := by
  unfold primeBits
  have hn2 : ¬ n < 2 := by omega
  rw [if_neg hn2]
  exact sieveLoop_correct
    (n + 1) n 2 (((1 <<< (n + 1)) - 1) ^^^ 3)
    (by omega) (by omega) (initial_sieve_inv n)
    i hi2 hin
'''

p=OUT/"Submission_v5_loop_dev.lean"
p.write_text(prefix+"\n"+extra+"\nend Submission\n")
print(f"generated {p} bytes={len(p.read_bytes())}")
