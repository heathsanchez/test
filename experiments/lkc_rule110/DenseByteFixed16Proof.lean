import DenseByteSeqAddProof
import WideDenseByteProof

namespace DenseByteFixed

open GenericPack
open WideGather
open WideDenseByte
open DenseByteSequence
open Submission

theorem packBytesNat_one (x : Nat) :
    packBytesNat x 1 = pack8Nat x := by
  rfl

theorem packW8_bytes1 (x : Nat) :
    packW 8
      (packBytesNat x 1)
      (packBytesNat (x + 8 * stepConst) 1) =
      packBytesNat x 2 := by
  rw [show (2 : Nat) = 1 + 1 by decide]
  rw [packBytesNat_add x 1 1]
  rw [advanceBytes_eq]
  unfold packW
  rw [Nat.shiftLeft_eq]
  change
    packBytesNat x 1 +
        packBytesNat (x + 8 * stepConst) 1 * 2 ^ 8 =
      packBytesNat x 1 +
        256 ^ 1 * packBytesNat (x + 8 * stepConst) 1
  rw [show (2 ^ 8 : Nat) = 256 ^ 1 by decide]
  rw [Nat.mul_comm]

theorem dense16_eq_bytes2 (x : Nat) :
    dense16 x = packBytesNat x 2 := by
  unfold dense16
  rw [dense8_eq_pack8Nat x, dense8_eq_pack8Nat (x + 8 * stepConst)]
  rw [← packBytesNat_one x, ← packBytesNat_one (x + 8 * stepConst)]
  exact packW8_bytes1 x

end DenseByteFixed
