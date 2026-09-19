#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_v20.py"))
src=(OUT/"Submission_algebra_v20.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0] + "\n\n"

proof=r'''
theorem w32_eq : w32 = 2^32 - 1 := by decide

theorem mask32_eq_mod (x : Nat) :
    x &&& w32 = x % 2^32 := by
  rw [w32_eq, Nat.and_two_pow_sub_one_eq_mod]

theorem mask32_lt (x : Nat) : x &&& w32 < 2^32 := by
  rw [mask32_eq_mod]
  exact Nat.mod_lt _ (by decide)

theorem majFast_eq (x y z : Nat) :
    majFast x y z = maj x y z := by
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [majFast, maj, Nat.testBit_xor, Nat.testBit_and]
  generalize x.testBit i = bx
  generalize y.testBit i = byy
  generalize z.testBit i = bz
  cases bx <;> cases byy <;> cases bz <;> decide

theorem chFast_eq (x y z : Nat)
    (hx : x < 2^32) (hz : z < 2^32) :
    chFast x y z = ch x y z := by
  unfold chFast ch
  rw [show w32 = 2^32 - 1 by exact w32_eq]
  apply Nat.eq_of_testBit_eq
  intro i
  simp only [Nat.testBit_xor, Nat.testBit_and,
    Nat.testBit_two_pow_sub_one]
  by_cases hi : i < 32
  · simp only [hi, decide_true]
    generalize x.testBit i = bx
    generalize y.testBit i = byy
    generalize z.testBit i = bz
    cases bx <;> cases byy <;> cases bz <;> decide
  · have h32i : 32 ≤ i := Nat.le_of_not_gt hi
    have hp : 2^32 ≤ 2^i :=
      Nat.pow_le_pow_right (by decide) h32i
    have hxlt : x < 2^i := Nat.lt_of_lt_of_le hx hp
    have hzlt : z < 2^i := Nat.lt_of_lt_of_le hz hp
    have hxb : x.testBit i = false := Nat.testBit_lt_two_pow hxlt
    have hzb : z.testBit i = false := Nat.testBit_lt_two_pow hzlt
    simp [hi, hxb, hzb]

theorem mask4_eq_nested (a b c d : Nat) :
    (a + b + c + d) &&& w32 =
      add32 (add32 a b) (add32 c d) := by
  simp only [add32, mask32_eq_mod]
  simp only [Nat.mod_add_mod, Nat.add_mod_mod]
  simp [Nat.add_assoc]

theorem mask5_eq_nested (a b c d e : Nat) :
    (a + b + c + d + e) &&& w32 =
      add32 a (add32 b (add32 c (add32 d e))) := by
  simp only [add32, mask32_eq_mod]
  simp only [Nat.add_mod_mod]
  simp [Nat.add_assoc]

theorem mask2_eq_add32 (a b : Nat) :
    (a + b) &&& w32 = add32 a b := rfl

end Submission
'''
p=OUT/"Algebra_census_v20.lean"
p.write_text(prefix+proof)
print(f"generated {p} bytes={len((prefix+proof).encode())}")
