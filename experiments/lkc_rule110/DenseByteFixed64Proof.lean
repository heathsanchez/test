import DenseByteFixed32Proof

namespace DenseByteFixed

open GenericPack
open WideGather
open DenseByteSequence
open Submission

theorem packW32_bytes4 (x : Nat) :
    packW 32
      (packBytesNat x 4)
      (packBytesNat (x + 32 * stepConst) 4) =
      packBytesNat x 8 := by
  rw [show (8 : Nat) = 4 + 4 by decide]
  rw [packBytesNat_add x 4 4]
  rw [advanceBytes_eq]
  unfold packW
  rw [Nat.shiftLeft_eq]
  change
    packBytesNat x 4 +
        packBytesNat (x + 32 * stepConst) 4 * 2 ^ 32 =
      packBytesNat x 4 +
        256 ^ 4 * packBytesNat (x + 32 * stepConst) 4
  rw [show (2 ^ 32 : Nat) = 256 ^ 4 by decide]
  rw [Nat.mul_comm]

theorem dense64_eq_bytes8 (x : Nat) :
    dense64 x = packBytesNat x 8 := by
  unfold dense64
  rw [dense32_eq_bytes4 x, dense32_eq_bytes4 (x + 32 * stepConst)]
  exact packW32_bytes4 x

end DenseByteFixed
