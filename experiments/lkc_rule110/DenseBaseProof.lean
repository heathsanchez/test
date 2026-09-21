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
  calc
    dense1 x = bits1 x := rfl
    _ = mixBit31Nat x := bits1_eq_mix x
    _ = (mixBit31 x).toNat := mixBit31Nat_eq x
    _ = (if mixBit31 x then 1 else 0) := boolToNat_eq_if (mixBit31 x)

theorem dense2_eq_probe (x : Nat) :
    dense2 x = packMixBit x 2 := by
  unfold dense2 packW
  rw [dense1_eq_if_probe, dense1_eq_if_probe]
  unfold packMixBit
  rw [Nat.shiftLeft_eq]
  rw [show 2 ^ 1 = 2 by decide]
  rw [Nat.mul_comm (if mixBit31 (x + 1 * stepConst) then 1 else 0) 2]
  rfl

end DenseBaseProbe
