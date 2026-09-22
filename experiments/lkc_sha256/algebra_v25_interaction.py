#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

# Exact V24 runtime stays untouched.  The second component of the interaction
# unit is proof-only: a compositional mod-2^32 shadow.
runpy.run_path(str(ROOT/"algebra_v24_probe.py"))
runpy.run_path(str(ROOT/"algebra_fullproof_v21.py"))
runtime=(OUT/"Submission_algebra_v24_probe.lean").read_text()
v23=(OUT/"Submission_algebra_v21_proof.lean").read_text()
prefix=runtime.rsplit("\nend Submission",1)[0] + "\n\n"

bridge=r'''
/-!
V25 interaction certificate: V24 deferred-normalization runtime + a proof-only
compositional congruence shadow.  Never normalize the whole SHA expression.
-/

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

/-- Tiny proof relation carried only by the certificate side of the interaction. -/
def Mod32Eq (a b : Nat) : Prop := a % 2^32 = b % 2^32

theorem mod32_refl (a : Nat) : Mod32Eq a a := rfl

theorem mod32_of_eq {a b : Nat} (h : a = b) : Mod32Eq a b := by
  cases h
  rfl

theorem mod32_add {a b c d : Nat}
    (h₁ : Mod32Eq a b) (h₂ : Mod32Eq c d) :
    Mod32Eq (a + c) (b + d) := by
  unfold Mod32Eq at *
  calc
    (a + c) % 2^32 = (a % 2^32 + c % 2^32) % 2^32 := Nat.add_mod _ _ _
    _ = (b % 2^32 + d % 2^32) % 2^32 := by rw [h₁, h₂]
    _ = (b + d) % 2^32 := (Nat.add_mod _ _ _).symm

theorem mod32_mask_right (x : Nat) : Mod32Eq x (x &&& w32) := by
  unfold Mod32Eq
  rw [mask32_eq_mod, Nat.mod_mod]

theorem mask_eq_of_mod32 {a b : Nat} (h : Mod32Eq a b) :
    (a &&& w32) = (b &&& w32) := by
  unfold Mod32Eq at h
  rw [mask32_eq_mod, mask32_eq_mod]
  exact h

theorem mask_add_mask (a b : Nat) :
    (a + b) &&& w32 =
      ((a &&& w32) + (b &&& w32)) &&& w32 := by
  apply mask_eq_of_mod32
  exact mod32_add (mod32_mask_right a) (mod32_mask_right b)

theorem mask_add_right_mask (a b : Nat) :
    (a + b) &&& w32 =
      (a + (b &&& w32)) &&& w32 := by
  apply mask_eq_of_mod32
  exact mod32_add (mod32_refl a) (mod32_mask_right b)

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

theorem bigSigma0_lt (x : Nat) : bigSigma0 x < 2^32 := by
  have h := Nat.mod_lt (bigSigma0Fast x) (by decide : 0 < 2^32)
  rw [bigSigma0Fast_mod_eq] at h
  exact h

theorem bigSigma1_lt (x : Nat) : bigSigma1 x < 2^32 := by
  have h := Nat.mod_lt (bigSigma1Fast x) (by decide : 0 < 2^32)
  rw [bigSigma1Fast_mod_eq] at h
  exact h

theorem smallSigma0_lt (x : Nat) (hx : x < 2^32) :
    smallSigma0 x < 2^32 := by
  have h := Nat.mod_lt (smallSigma0Fast x) (by decide : 0 < 2^32)
  rw [smallSigma0Fast_mod_eq x hx] at h
  exact h

theorem smallSigma1_lt (x : Nat) (hx : x < 2^32) :
    smallSigma1 x < 2^32 := by
  have h := Nat.mod_lt (smallSigma1Fast x) (by decide : 0 < 2^32)
  rw [smallSigma1Fast_mod_eq x hx] at h
  exact h

theorem bigSigma0Fast_mod32 (x : Nat) :
    Mod32Eq (bigSigma0Fast x) (bigSigma0 x) := by
  unfold Mod32Eq
  rw [bigSigma0Fast_mod_eq, Nat.mod_eq_of_lt (bigSigma0_lt x)]

theorem bigSigma1Fast_mod32 (x : Nat) :
    Mod32Eq (bigSigma1Fast x) (bigSigma1 x) := by
  unfold Mod32Eq
  rw [bigSigma1Fast_mod_eq, Nat.mod_eq_of_lt (bigSigma1_lt x)]

theorem smallSigma0Fast_mod32 (x : Nat) (hx : x < 2^32) :
    Mod32Eq (smallSigma0Fast x) (smallSigma0 x) := by
  unfold Mod32Eq
  rw [smallSigma0Fast_mod_eq x hx, Nat.mod_eq_of_lt (smallSigma0_lt x hx)]

theorem smallSigma1Fast_mod32 (x : Nat) (hx : x < 2^32) :
    Mod32Eq (smallSigma1Fast x) (smallSigma1 x) := by
  unfold Mod32Eq
  rw [smallSigma1Fast_mod_eq x hx, Nat.mod_eq_of_lt (smallSigma1_lt x hx)]

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

round_bridge=r'''
def t1Raw (s : Digest) (k w : Nat) : Nat :=
  s.h + bigSigma1Fast s.e + chFast s.e s.f s.g + k + w

def t1SpecFlat (s : Digest) (k w : Nat) : Nat :=
  s.h + bigSigma1 s.e + ch s.e s.f s.g + k + w

def t2Raw (s : Digest) : Nat :=
  bigSigma0Fast s.a + majFast s.a s.b s.c

def t2SpecFlat (s : Digest) : Nat :=
  bigSigma0 s.a + maj s.a s.b s.c

theorem t1_mod32 (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    Mod32Eq (t1Raw s k w) (t1SpecFlat s k w) := by
  unfold t1Raw t1SpecFlat
  exact
    mod32_add
      (mod32_add
        (mod32_add
          (mod32_add
            (mod32_refl s.h)
            (bigSigma1Fast_mod32 s.e))
          (mod32_of_eq (chFast_eq s.e s.f s.g hs.e hs.g)))
        (mod32_refl k))
      (mod32_refl w)

theorem t2_mod32 (s : Digest) :
    Mod32Eq (t2Raw s) (t2SpecFlat s) := by
  unfold t2Raw t2SpecFlat
  exact mod32_add
    (bigSigma0Fast_mod32 s.a)
    (mod32_of_eq (majFast_eq s.a s.b s.c))

def roundShadow (s : Digest) (k w : Nat) : Digest :=
  let t1 := t1SpecFlat s k w
  let t2 := t2SpecFlat s
  ⟨(t1 + t2) &&& w32, s.a, s.b, s.c,
   (s.d + t1) &&& w32, s.e, s.f, s.g⟩

theorem roundFast_eq_shadow
    (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    roundFast s k w = roundShadow s k w := by
  have ha :
      (t1Raw s k w + t2Raw s) &&& w32 =
        (t1SpecFlat s k w + t2SpecFlat s) &&& w32 :=
    mask_eq_of_mod32 (mod32_add (t1_mod32 s k w hs) (t2_mod32 s))
  have he :
      (s.d + t1Raw s k w) &&& w32 =
        (s.d + t1SpecFlat s k w) &&& w32 :=
    mask_eq_of_mod32
      (mod32_add (mod32_refl s.d) (t1_mod32 s k w hs))
  change
    Digest.mk
      ((t1Raw s k w + t2Raw s) &&& w32) s.a s.b s.c
      ((s.d + t1Raw s k w) &&& w32) s.e s.f s.g =
    Digest.mk
      ((t1SpecFlat s k w + t2SpecFlat s) &&& w32) s.a s.b s.c
      ((s.d + t1SpecFlat s k w) &&& w32) s.e s.f s.g
  rw [ha, he]

def t1Nested (s : Digest) (k w : Nat) : Nat :=
  add32 s.h (add32 (bigSigma1 s.e)
    (add32 (ch s.e s.f s.g) (add32 k w)))

def t2Nested (s : Digest) : Nat :=
  add32 (bigSigma0 s.a) (maj s.a s.b s.c)

theorem t1Spec_mask_eq_nested (s : Digest) (k w : Nat) :
    (t1SpecFlat s k w &&& w32) = t1Nested s k w := by
  unfold t1SpecFlat t1Nested
  exact mask5_eq_nested s.h (bigSigma1 s.e) (ch s.e s.f s.g) k w

theorem t2Spec_mask_eq_nested (s : Digest) :
    (t2SpecFlat s &&& w32) = t2Nested s := by
  rfl

theorem roundShadow_eq_round (s : Digest) (k w : Nat) :
    roundShadow s k w = round s k w := by
  have ha :
      (t1SpecFlat s k w + t2SpecFlat s) &&& w32 =
        add32 (t1Nested s k w) (t2Nested s) := by
    rw [mask_add_mask, t1Spec_mask_eq_nested, t2Spec_mask_eq_nested]
    rfl
  have he :
      (s.d + t1SpecFlat s k w) &&& w32 =
        add32 s.d (t1Nested s k w) := by
    rw [mask_add_right_mask, t1Spec_mask_eq_nested]
    rfl
  change
    Digest.mk
      ((t1SpecFlat s k w + t2SpecFlat s) &&& w32) s.a s.b s.c
      ((s.d + t1SpecFlat s k w) &&& w32) s.e s.f s.g =
    Digest.mk
      (add32 (t1Nested s k w) (t2Nested s)) s.a s.b s.c
      (add32 s.d (t1Nested s k w)) s.e s.f s.g
  rw [ha, he]

theorem roundFast_eq_round (s : Digest) (k w : Nat) (hs : ValidDigest s) :
    roundFast s k w = round s k w :=
  (roundFast_eq_shadow s k w hs).trans (roundShadow_eq_round s k w)
'''

c=v23.index("def Window.toList")
d=v23.index("theorem Window.nextFast_eq_nextWord")
pre_next=v23[c:d]
e=v23.index("def Window.advance", d)
post_next=v23[e:v23.rindex("\nend Submission")]

next_bridge=r'''
def Window.nextRaw (w : Window) : Nat :=
  smallSigma1Fast w.x14 + w.x9 + smallSigma0Fast w.x1 + w.x0

def Window.nextShadow (w : Window) : Nat :=
  (smallSigma1 w.x14 + w.x9 + smallSigma0 w.x1 + w.x0) &&& w32

theorem Window.nextRaw_mod32 (w : Window) (hw : ValidWindow w) :
    Mod32Eq w.nextRaw
      (smallSigma1 w.x14 + w.x9 + smallSigma0 w.x1 + w.x0) := by
  unfold Window.nextRaw
  exact
    mod32_add
      (mod32_add
        (mod32_add
          (smallSigma1Fast_mod32 w.x14 hw.x14)
          (mod32_refl w.x9))
        (smallSigma0Fast_mod32 w.x1 hw.x1))
      (mod32_refl w.x0)

theorem Window.nextFast_eq_shadow (w : Window) (hw : ValidWindow w) :
    w.nextFast = w.nextShadow := by
  change (w.nextRaw &&& w32) =
    ((smallSigma1 w.x14 + w.x9 + smallSigma0 w.x1 + w.x0) &&& w32)
  exact mask_eq_of_mod32 (w.nextRaw_mod32 hw)

theorem Window.nextShadow_eq_nextWord (w : Window) :
    w.nextShadow = w.nextWord := by
  unfold Window.nextShadow Window.nextWord
  exact mask4_eq_nested
    (smallSigma1 w.x14) w.x9 (smallSigma0 w.x1) w.x0

theorem Window.nextFast_eq_nextWord (w : Window) (hw : ValidWindow w) :
    w.nextFast = w.nextWord :=
  (w.nextFast_eq_shadow hw).trans w.nextShadow_eq_nextWord
'''

text=prefix+bridge+pre_round+round_bridge+pre_next+next_bridge+post_next+"\nend Submission\n"
p=OUT/"Submission_algebra_v25_interaction.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
