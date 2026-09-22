#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def clearMask (bits mask : Nat) : Nat :=
  bits ^^^ (bits &&& mask)

def progressionMask (n p start : Nat) : Nat :=
  if p = 0 || n < start then 0
  else
    let count := (n - start) / p + 1
    let geom := ((1 <<< (p * count)) - 1) / ((1 <<< p) - 1)
    geom <<< start

theorem clearMask_testBit (bits mask i : Nat) :
    (clearMask bits mask).testBit i =
      (bits.testBit i && !(mask.testBit i)) := by
  unfold clearMask
  simp only [Nat.testBit_xor, Nat.testBit_and]
  cases bits.testBit i <;> cases mask.testBit i <;> decide

theorem two_le_two_pow_of_pos (p : Nat) (hp : 0 < p) :
    2 <= 2^p := by
  have h : 1 <= p := hp
  calc
    2 = 2^1 := by rfl
    _ <= 2^p := Nat.pow_le_pow_right (by decide) h

theorem progressionMask_eq_sum
    (n p start : Nat) (hp : 0 < p) (hs : start <= n) :
    progressionMask n p start =
      ∑ q ∈ Finset.range ((n-start)/p+1), (1 <<< (start + q*p)) := by
  unfold progressionMask
  simp only [hp.ne', false_or, show !(n < start) by omega, Bool.false_eq_true, if_false]
  let count := (n-start)/p+1
  have hgeom := Nat.geomSum_eq (two_le_two_pow_of_pos p hp) count
  simp only [Nat.one_shiftLeft, Nat.shiftLeft_eq]
  change
    (((2^(p*count)-1)/(2^p-1)) * 2^start) =
      ∑ q ∈ Finset.range count, 2^(start+q*p)
  rw [← hgeom]
  rw [Finset.sum_mul]
  apply Finset.sum_congr rfl
  intro q hq
  rw [pow_mul]
  rw [← pow_add]
  congr 1
  omega

end Submission
'''
p=OUT/"PrimeBulkMaskCensus_v7.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
