import WideDenseBaseProof

namespace WideDense

open GenericPack
open WideHierarchy
open WideGather
open Submission

theorem dense32_eq (x : Nat) :
    dense32 x = packMixBit x 32 := by
  unfold dense32 packW
  rw [dense16_eq, dense16_eq]
  rw [show 32 = 16 + 16 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense64_eq (x : Nat) :
    dense64 x = packMixBit x 64 := by
  unfold dense64 packW
  rw [dense32_eq, dense32_eq]
  rw [show 64 = 32 + 32 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

end WideDense
