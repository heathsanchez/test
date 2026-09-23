#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def dup32 (x : Nat) : Nat := x * 4294967297

theorem dup32_eq_or (x : Nat) (hx : x < 2^32) :
    dup32 x = (x <<< 32) ||| x := by
  unfold dup32
  calc
    x * 4294967297 = 2^32 * x + x := by norm_num [Nat.mul_add, Nat.mul_comm, Nat.mul_left_comm]
    _ = (2^32 * x) ||| x := Nat.two_pow_add_eq_or_of_lt hx x
    _ = (x <<< 32) ||| x := by rw [Nat.shiftLeft_eq, Nat.mul_comm]

theorem shift32_7 (x : Nat) :
    (x <<< 32) >>> 7 = x <<< 25 := by
  simp [Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow]
  norm_num [Nat.mul_div_assoc]

theorem dup32_shift7 (x : Nat) (hx : x < 2^32) :
    dup32 x >>> 7 = (x >>> 7) ||| (x <<< 25) := by
  rw [dup32_eq_or x hx, Nat.shiftRight_or_distrib, shift32_7]
  rw [Nat.or_comm]

theorem dup32_rotr7 (x : Nat) (hx : x < 2^32) :
    (dup32 x >>> 7) &&& w32 = rotr32 x 7 := by
  rw [dup32_shift7 x hx]
  rfl

end Submission
'''
p=OUT/"V31RotateProofDev.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
