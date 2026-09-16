import WideGatherProof
import Submission

namespace WideDenseByte

open GenericPack
open WideHierarchy
open WideGather
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem dense1_eq_nat (x : Nat) :
    dense1 x = mixBit31Nat x := by
  unfold dense1
  exact bits1_eq_mix x

theorem dense8_eq_pack8Nat (x : Nat) :
    dense8 x = pack8Nat x := by
  unfold dense8 dense4 dense2 packW pack8Nat
  rw [dense1_eq_nat, dense1_eq_nat, dense1_eq_nat, dense1_eq_nat,
      dense1_eq_nat, dense1_eq_nat, dense1_eq_nat, dense1_eq_nat]
  simp only [Nat.shiftLeft_eq]
  have h2 : x + 2 * stepConst = x + stepConst + stepConst := by omega
  have h3 : x + 2 * stepConst + 1 * stepConst =
      x + stepConst + stepConst + stepConst := by omega
  have h4 : x + 4 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst := by omega
  have h5 : x + 4 * stepConst + 1 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst + stepConst := by omega
  have h6 : x + 4 * stepConst + 2 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst := by omega
  have h7 : x + 4 * stepConst + 2 * stepConst + 1 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst := by omega
  rw [h7, h6, h5, h4, h3, h2]
  simp only [Nat.one_mul, Nat.pow_succ, Nat.pow_zero, Nat.mul_one]
  omega

end WideDenseByte
