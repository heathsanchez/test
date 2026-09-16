import WideDenseSmallProof

namespace WideDense

open GenericPack
open WideHierarchy
open WideGather
open Submission

theorem dense128_eq (x : Nat) :
    dense128 x = packMixBit x 128 := by
  unfold dense128 packW
  rw [dense64_eq, dense64_eq]
  rw [show 128 = 64 + 64 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense256_eq (x : Nat) :
    dense256 x = packMixBit x 256 := by
  unfold dense256 packW
  rw [dense128_eq, dense128_eq]
  rw [show 256 = 128 + 128 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense256_low254 (x : Nat) :
    dense256 x &&& (2 ^ 254 - 1) = packMixBit x 254 := by
  rw [dense256_eq]
  rw [Nat.and_two_pow_sub_one_eq_mod]
  have h : 256 = 254 + 2 := by decide
  rw [h, DenseAlgebraProbe.packMixBit_mod_pow_probe]

end WideDense
