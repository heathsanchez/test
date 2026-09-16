import WideGatherProof
import DenseAlgebraProof
import Submission

namespace WideDense

open GenericPack
open WideHierarchy
open WideGather
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem dense1_eq_if (x : Nat) :
    dense1 x = (if mixBit31 x then 1 else 0) := by
  unfold dense1
  exact (bits1_eq_mix x).trans
    ((mixBit31Nat_eq x).trans (boolToNat_eq_if (mixBit31 x)))

theorem dense2_eq (x : Nat) :
    dense2 x = packMixBit x 2 := by
  unfold dense2 packW
  rw [dense1_eq_if, dense1_eq_if]
  simp [packMixBit, Nat.shiftLeft_eq, Nat.mul_comm]

end WideDense
