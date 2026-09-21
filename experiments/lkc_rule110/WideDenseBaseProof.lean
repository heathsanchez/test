import WideDenseByteProof
import DenseAlgebraProof
import Submission

namespace WideDense

open GenericPack
open WideHierarchy
open WideGather
open WideDenseByte
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem pack8Nat_eq_packMixBit8 (x : Nat) :
    pack8Nat x = packMixBit x 8 := by
  rw [pack8Nat_eq]
  symm
  have h := packMixBit_eight x 0
  have hz : packMixBit (advance8 x) 0 = 0 := rfl
  rw [hz] at h
  simpa only [Nat.zero_add, Nat.mul_zero, Nat.add_zero] using h

theorem dense8_eq (x : Nat) :
    dense8 x = packMixBit x 8 := by
  exact (dense8_eq_pack8Nat x).trans (pack8Nat_eq_packMixBit8 x)

theorem dense16_eq (x : Nat) :
    dense16 x = packMixBit x 16 := by
  unfold dense16 packW
  rw [dense8_eq, dense8_eq]
  rw [show 16 = 8 + 8 by decide, DenseAlgebraProbe.packMixBit_add_probe]
  simp [Nat.shiftLeft_eq, Nat.mul_comm]

end WideDense
