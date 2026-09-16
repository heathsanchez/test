import WideDenseBaseProof

namespace WideDense

open GenericPack
open WideHierarchy
open WideGather
open Submission

theorem dense4_eq (x : Nat) :
    dense4 x = packMixBit x 4 := by
  unfold dense4 packW
  rw [dense2_eq, dense2_eq]
  rw [show 4 = 2 + 2 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense8_eq (x : Nat) :
    dense8 x = packMixBit x 8 := by
  unfold dense8 packW
  rw [dense4_eq, dense4_eq]
  rw [show 8 = 4 + 4 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

theorem dense16_eq (x : Nat) :
    dense16 x = packMixBit x 16 := by
  unfold dense16 packW
  rw [dense8_eq, dense8_eq]
  rw [show 16 = 8 + 8 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

end WideDense
