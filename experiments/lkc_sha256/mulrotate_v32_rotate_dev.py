#!/usr/bin/env python3
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]
proof=r'''
theorem dup32_eq_or_dev (x : Nat) (hx : x < 2^32) :
    dup32 x = (x <<< 32) ||| x := by
  unfold dup32
  rw [show 4294967297 = 2^32 + 1 by decide]
  rw [Nat.mul_add, Nat.mul_one]
  rw [Nat.shiftLeft_eq]
  rw [Nat.mul_comm x (2^32)]
  exact Nat.two_pow_add_eq_or_of_lt hx x

theorem shiftLeft32_shiftRight_dev (x n : Nat) (hn : n ≤ 32) :
    (x <<< 32) >>> n = x <<< (32 - n) := by
  rw [Nat.shiftLeft_eq, Nat.shiftRight_eq_div_pow, Nat.shiftLeft_eq]
  rw [← Nat.pow_sub_mul_pow 2 hn]
  rw [← Nat.mul_assoc]
  exact Nat.mul_div_cancel _ (Nat.two_pow_pos n)

theorem dup32_shift_eq_rotrRaw_dev (x n : Nat)
    (hx : x < 2^32) (hn : n ≤ 32) :
    dup32 x >>> n = rotrRaw x n := by
  rw [dup32_eq_or_dev x hx, Nat.shiftRight_or_distrib]
  rw [shiftLeft32_shiftRight_dev x n hn]
  unfold rotrRaw
  simpa [Nat.or_comm]

example (x : Nat) (hx : x < 2^32) :
    dup32 x >>> 2 = rotrRaw x 2 :=
  dup32_shift_eq_rotrRaw_dev x 2 hx (by decide)

example (x : Nat) (hx : x < 2^32) :
    dup32 x >>> 25 = rotrRaw x 25 :=
  dup32_shift_eq_rotrRaw_dev x 25 hx (by decide)

end Submission
'''
p=OUT/"RotateDev.lean"; p.write_text(prefix+"\n"+proof)
print(f"generated {p} bytes={len(p.read_bytes())}")
