import WideGatherProof
import Submission

namespace DenseBaseProbe

open GenericPack
open WideHierarchy
open WideGather
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem dense1_eq_if_probe (x : Nat) :
    dense1 x = (if mixBit31 x then 1 else 0) := by
  unfold dense1
  exact (bits1_eq_mix x).trans
    ((mixBit31Nat_eq x).trans (boolToNat_eq_if (mixBit31 x)))

theorem dense2_eq_probe (x : Nat) :
    dense2 x = packMixBit x 2 := by
  unfold dense2 packW
  rw [dense1_eq_if_probe, dense1_eq_if_probe]
  simp [packMixBit, Nat.shiftLeft_eq, Nat.mul_comm]

end DenseBaseProbe
