#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

# Generate the exact fast V24 runtime and the already-qualified V23 proof bank.
runpy.run_path(str(ROOT/"algebra_v24_probe.py"))
runpy.run_path(str(ROOT/"algebra_fullproof_v21.py"))
runtime=(OUT/"Submission_algebra_v24_probe.lean").read_text()
v23=(OUT/"Submission_algebra_v21_proof.lean").read_text()
prefix=runtime.rsplit("\nend Submission",1)[0] + "\n\n"

bridge=r'''
/-! Proof bridge for V24 deferred normalization. -/

theorem w32_eq : w32 = 2^32 - 1 := by decide

theorem mask32_eq_mod (x : Nat) :
    x &&& w32 = x % 2^32 := by
  rw [w32_eq, Nat.and_two_pow_sub_one_eq_mod]

theorem mask32_lt (x : Nat) : x &&& w32 < 2^32 := by
  rw [mask32_eq_mod]
  exact Nat.mod_lt _ (by decide)

theorem and_mask32_eq_self (x : Nat) (hx : x < 2^32) :
    x &&& w32 = x := by
  rw [w32_eq]
  exact Nat.and_two_pow_sub_one_of_lt_two_pow hx

theorem bigSigma0Fast_mod_eq (x : Nat) :
    bigSigma0Fast x % 2^32 = bigSigma0 x := by
  rw [← mask32_eq_mod]
  unfold bigSigma0Fast bigSigma0 rotrRaw rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]

theorem bigSigma1Fast_mod_eq (x : Nat) :
    bigSigma1Fast x % 2^32 = bigSigma1 x := by
  rw [← mask32_eq_mod]
  unfold bigSigma1Fast bigSigma1 rotrRaw rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]

theorem smallSigma0Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    smallSigma0Fast x % 2^32 = smallSigma0 x := by
  rw [← mask32_eq_mod]
  unfold smallSigma0Fast smallSigma0 rotrRaw rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  have hs : x >>> 3 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 3) hx
  rw [and_mask32_eq_self (x >>> 3) hs]

theorem smallSigma1Fast_mod_eq (x : Nat) (hx : x < 2^32) :
    smallSigma1Fast x % 2^32 = smallSigma1 x := by
  rw [← mask32_eq_mod]
  unfold smallSigma1Fast smallSigma1 rotrRaw rotr32
  rw [Nat.and_xor_distrib_right, Nat.and_xor_distrib_right]
  have hs : x >>> 10 < 2^32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 10) hx
  rw [and_mask32_eq_self (x >>> 10) hs]

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
'''

a=v23.index("structure ValidDigest")
b=v23.index("theorem roundFast_eq_round")
pre_round=v23[a:b]

c=v23.index("def Window.toList")
d=v23.index("theorem Window.nextFast_eq_nextWord")
pre_next=v23[c:d]
e=v23.index("def Window.advance", d)
post_next=v23[e:v23.rindex("\nend Submission")]

round_proof=r'''
theorem roundFast_eq_round (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    roundFast s k w = round s k w := by
  unfold roundFast round
  rw [chFast_eq s.e s.f s.g hs.e hs.g]
  rw [majFast_eq s.a s.b s.c]
  simp only [add32, mask32_eq_mod]
  simp only [Nat.add_mod]
  rw [bigSigma1Fast_mod_eq s.e]
  rw [bigSigma0Fast_mod_eq s.a]
  simp [Nat.add_assoc]
'''

next_proof=r'''
theorem Window.nextFast_eq_nextWord (w : Window) (hw : ValidWindow w) :
    w.nextFast = w.nextWord := by
  unfold Window.nextFast Window.nextWord
  simp only [add32, mask32_eq_mod]
  simp only [Nat.add_mod]
  rw [smallSigma1Fast_mod_eq w.x14 hw.x14]
  rw [smallSigma0Fast_mod_eq w.x1 hw.x1]
  simp [Nat.add_assoc]
'''

text=prefix+bridge+pre_round+round_proof+pre_next+next_proof+post_next+"\nend Submission\n"
p=OUT/"Submission_algebra_v24_proof.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
