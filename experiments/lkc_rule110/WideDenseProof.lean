import WideGatherProof
import Submission

namespace WideDense

set_option maxRecDepth 4194304
set_option exponentiation.threshold 20000
set_option maxHeartbeats 2000000

open GenericPack
open WideHierarchy
open WideGather
open Submission

theorem packMixBit_lt (x k : Nat) :
    packMixBit x k < 2 ^ k := by
  induction k generalizing x with
  | zero => simp [packMixBit]
  | succ k ih =>
      simp only [packMixBit, Nat.pow_succ]
      have hb : (if mixBit31 x then 1 else 0) < 2 := by
        split <;> omega
      have ht := ih (x + stepConst)
      omega

theorem packMixBit_add (x a b : Nat) :
    packMixBit x (a + b) =
      packMixBit x a + 2 ^ a * packMixBit (x + a * stepConst) b := by
  induction a generalizing x with
  | zero =>
      simp [packMixBit]
  | succ a ih =>
      simp only [Nat.succ_add, packMixBit, Nat.pow_succ]
      rw [ih (x + stepConst)]
      have hx :
          x + stepConst + a * stepConst =
            x + (a + 1) * stepConst := by
        unfold stepConst
        omega
      rw [hx, Nat.mul_add]
      simp only [Nat.add_assoc]

theorem packMixBit_mod_pow (x a b : Nat) :
    packMixBit x (a + b) % 2 ^ a = packMixBit x a := by
  rw [packMixBit_add]
  have hp := packMixBit_lt x a
  simp [Nat.add_mod, Nat.mod_eq_of_lt hp]

theorem dense1_eq (x : Nat) :
    dense1 x = packMixBit x 1 := by
  unfold dense1
  change bits1 x = (if mixBit31 x then 1 else 0)
  exact (bits1_eq_mix x).trans
    ((mixBit31Nat_eq x).trans (boolToNat_eq_if (mixBit31 x)))

theorem dense2_eq (x : Nat) :
    dense2 x = packMixBit x 2 := by
  unfold dense2 packW
  rw [dense1_eq, dense1_eq]
  rw [show 2 = 1 + 1 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense4_eq (x : Nat) :
    dense4 x = packMixBit x 4 := by
  unfold dense4 packW
  rw [dense2_eq, dense2_eq]
  rw [show 4 = 2 + 2 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense8_eq (x : Nat) :
    dense8 x = packMixBit x 8 := by
  unfold dense8 packW
  rw [dense4_eq, dense4_eq]
  rw [show 8 = 4 + 4 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense16_eq (x : Nat) :
    dense16 x = packMixBit x 16 := by
  unfold dense16 packW
  rw [dense8_eq, dense8_eq]
  rw [show 16 = 8 + 8 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense32_eq (x : Nat) :
    dense32 x = packMixBit x 32 := by
  unfold dense32 packW
  rw [dense16_eq, dense16_eq]
  rw [show 32 = 16 + 16 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense64_eq (x : Nat) :
    dense64 x = packMixBit x 64 := by
  unfold dense64 packW
  rw [dense32_eq, dense32_eq]
  rw [show 64 = 32 + 32 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense128_eq (x : Nat) :
    dense128 x = packMixBit x 128 := by
  unfold dense128 packW
  rw [dense64_eq, dense64_eq]
  rw [show 128 = 64 + 64 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense256_eq (x : Nat) :
    dense256 x = packMixBit x 256 := by
  unfold dense256 packW
  rw [dense128_eq, dense128_eq]
  rw [show 256 = 128 + 128 by decide, packMixBit_add]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense256_low254 (x : Nat) :
    dense256 x &&& (2 ^ 254 - 1) = packMixBit x 254 := by
  rw [dense256_eq]
  rw [Nat.and_two_pow_sub_one_eq_mod]
  have h : 256 = 254 + 2 := by decide
  rw [h, packMixBit_mod_pow]

end WideDense
