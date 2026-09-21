import DenseByteFixed16Proof

namespace DenseByteFixed

open GenericPack
open WideGather
open DenseByteSequence
open Submission

theorem packW16_bytes2 (x : Nat) :
    packW 16
      (packBytesNat x 2)
      (packBytesNat (x + 16 * stepConst) 2) =
      packBytesNat x 4 := by
  rw [show (4 : Nat) = 2 + 2 by decide]
  rw [packBytesNat_add x 2 2]
  rw [advanceBytes_eq]
  unfold packW
  rw [Nat.shiftLeft_eq]
  change
    packBytesNat x 2 +
        packBytesNat (x + 16 * stepConst) 2 * 2 ^ 16 =
      packBytesNat x 2 +
        256 ^ 2 * packBytesNat (x + 16 * stepConst) 2
  rw [show (2 ^ 16 : Nat) = 256 ^ 2 by decide]
  rw [Nat.mul_comm]

theorem dense32_eq_bytes4 (x : Nat) :
    dense32 x = packBytesNat x 4 := by
  unfold dense32
  rw [dense16_eq_bytes2 x, dense16_eq_bytes2 (x + 16 * stepConst)]
  exact packW16_bytes2 x

end DenseByteFixed
