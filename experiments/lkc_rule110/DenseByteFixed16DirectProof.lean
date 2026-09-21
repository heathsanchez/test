import DenseByteSeqAddProof
import WideDenseByteProof

namespace DenseByteFixedDirect

open GenericPack
open WideGather
open WideDenseByte
open DenseByteSequence
open Submission

theorem bytes1 (x : Nat) :
    packBytesNat x 1 = pack8Nat x := by
  rfl

theorem bytes2 (x : Nat) :
    packBytesNat x 2 =
      pack8Nat x + 256 * pack8Nat (x + 8 * stepConst) := by
  simp only [packBytesNat, Nat.mul_zero, Nat.add_zero]
  rw [advance8_eq_swar]

theorem packW8_direct (x : Nat) :
    packW 8 (pack8Nat x) (pack8Nat (x + 8 * stepConst)) =
      packBytesNat x 2 := by
  rw [bytes2]
  unfold packW
  rw [Nat.shiftLeft_eq]
  rw [show (2 ^ 8 : Nat) = 256 by decide]
  rw [Nat.mul_comm]

theorem dense16_eq_bytes2 (x : Nat) :
    dense16 x = packBytesNat x 2 := by
  unfold dense16
  rw [dense8_eq_pack8Nat x]
  rw [dense8_eq_pack8Nat (x + 8 * stepConst)]
  exact packW8_direct x

end DenseByteFixedDirect
