#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runtime=r'''import Spec

namespace Submission

def clearBitIfSet (bits i : Nat) : Nat :=
  if bits.testBit i then bits ^^^ (1 <<< i) else bits

def clearMultiples : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, bits => bits
  | fuel + 1, n, p, m, bits =>
      if n < m then bits
      else clearMultiples fuel n p (m + p) (clearBitIfSet bits m)

def sieveLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, bits => bits
  | fuel + 1, n, p, bits =>
      if n < p * p then bits
      else
        let bits' :=
          if bits.testBit p then clearMultiples (n + 1) n p (p * p) bits
          else bits
        sieveLoop fuel n (p + 1) bits'

def primeBits (n : Nat) : Nat :=
  if n < 2 then 0
  else
    let bits := ((1 <<< (n + 1)) - 1) ^^^ 3
    sieveLoop (n + 1) n 2 bits

def countBits : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | fuel + 1, i, bits =>
      (if bits.testBit i then 1 else 0) + countBits fuel (i + 1) bits

def impl (n : Nat) : Nat :=
  if n < 2 then 0 else countBits (n - 1) 2 (primeBits n)

/-! First proof census: bit-level semantics only. -/

theorem singletonMask_testBit (i j : Nat) :
    (1 <<< i).testBit j = decide (j = i) := by
  rw [Nat.one_shiftLeft, Nat.testBit_two_pow]
  simp [eq_comm]

theorem clearBitIfSet_testBit (bits i j : Nat) :
    (clearBitIfSet bits i).testBit j =
      if j = i then false else bits.testBit j := by
  unfold clearBitIfSet
  by_cases hb : bits.testBit i = true
  · have hb' : bits.testBit i = true := hb
    simp only [hb, if_true, Nat.testBit_xor, singletonMask_testBit]
    by_cases hji : j = i
    · subst j
      simp [hb']
    · simp [hji]
  · have hb0 : bits.testBit i = false := Bool.eq_false_of_not_eq_true hb
    simp [hb0]
    by_cases hji : j = i
    · subst j
      exact hb0
    · rfl

theorem initialBits_testBit (n i : Nat) (hn : 2 ≤ n) :
    ((((1 <<< (n + 1)) - 1) ^^^ 3).testBit i) =
      decide (2 ≤ i ∧ i ≤ n) := by
  rw [Nat.one_shiftLeft, Nat.testBit_xor, Nat.testBit_two_pow_sub_one]
  have h3 : (3 : Nat) = 2 ^ 2 - 1 := by decide
  rw [h3, Nat.testBit_two_pow_sub_one]
  by_cases htop : i < n + 1
  · by_cases hlow : i < 2
    · have hin : i ≤ n := by omega
      have hnot : ¬ 2 ≤ i := by omega
      simp [htop, hlow, hin, hnot]
    · have hin : i ≤ n := by omega
      have hlo : 2 ≤ i := by omega
      simp [htop, hlow, hin, hlo]
  · have hnin : ¬ i ≤ n := by omega
    have hlowfalse : ¬ (2 ≤ i ∧ i ≤ n) := by omega
    by_cases hlow : i < 2
    · omega
    · simp [htop, hlow, hnin, hlowfalse]

end Submission
'''
p=OUT/"PrimeBitCensus_v6.lean"
p.write_text(runtime)
print(f"generated {p} bytes={len(runtime.encode())}")
