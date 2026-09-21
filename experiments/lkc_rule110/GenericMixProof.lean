import GenericPackProof
import Submission

namespace GenericMix

open GenericPack

def mixCore (m p : Nat) : Nat :=
  let u := stage m 16 p
  let y := (u * Submission.Vec8.c1) &&& m
  let v := stage m 15 y
  v * Submission.Vec8.c2

theorem lt_pow_mono_exp {x a b : Nat}
    (hx : x < 2 ^ a) (hab : a ≤ b) :
    x < 2 ^ b := by
  exact Nat.lt_of_lt_of_le hx (Nat.pow_le_pow_right (by omega) hab)

theorem stage_mul_lt
    (w m s p k : Nat)
    (hmk : m * k < 2 ^ w) :
    stage m s p * k < 2 ^ w := by
  have hle : stage m s p * k ≤ m * k :=
    Nat.mul_le_mul_right k (stage_le m s p)
  exact Nat.lt_of_le_of_lt hle hmk

theorem and_mask_lt
    (w m x : Nat)
    (hm : m < 2 ^ w) :
    (x &&& m) < 2 ^ w :=
  Nat.lt_of_le_of_lt Nat.and_le_right hm

theorem mixCore_lt
    (w m p : Nat)
    (hc2 : m * Submission.Vec8.c2 < 2 ^ w) :
    mixCore m p < 2 ^ w := by
  unfold mixCore
  exact stage_mul_lt w m 15
    (((stage m 16 p * Submission.Vec8.c1) &&& m))
    Submission.Vec8.c2 hc2

theorem mixCore_double
    (w m p q : Nat)
    (hw : 32 ≤ w)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - 32))
    (hc1 : m * Submission.Vec8.c1 < 2 ^ w)
    (hc2 : m * Submission.Vec8.c2 < 2 ^ w) :
    mixCore (maskW w m) (packW w p q) =
      packW w (mixCore m p) (mixCore m q) := by
  have hmw : m < 2 ^ w :=
    lt_pow_mono_exp hm (by omega)
  have hm16 : m < 2 ^ (w - 16) :=
    lt_pow_mono_exp hm (by omega)
  have hm15 : m < 2 ^ (w - 15) :=
    lt_pow_mono_exp hm (by omega)
  have hp1 :
      stage m 16 p * Submission.Vec8.c1 < 2 ^ w :=
    stage_mul_lt w m 16 p Submission.Vec8.c1 hc1
  have hy :
      ((stage m 16 p * Submission.Vec8.c1) &&& m) < 2 ^ w :=
    and_mask_lt w m _ hmw
  simp only [mixCore]
  rw [lift_stage w m 16 p q hp hm16 (by decide) (by omega)]
  rw [packW_mul]
  rw [and_maskW w m
        (stage m 16 p * Submission.Vec8.c1)
        (stage m 16 q * Submission.Vec8.c1)
        hp1 hmw]
  rw [lift_stage w m 15
        ((stage m 16 p * Submission.Vec8.c1) &&& m)
        ((stage m 16 q * Submission.Vec8.c1) &&& m)
        hy hm15 (by decide) (by omega)]
  rw [packW_mul]

end GenericMix
