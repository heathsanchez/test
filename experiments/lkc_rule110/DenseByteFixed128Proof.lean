import DenseByteFixed64Proof

namespace DenseByteFixed

open GenericPack
open WideGather
open DenseByteSequence
open Submission

theorem packW64_bytes8 (x : Nat) :
    packW 64
      (packBytesNat x 8)
      (packBytesNat (x + 64 * stepConst) 8) =
      packBytesNat x 16 := by
  rw [show (16 : Nat) = 8 + 8 by decide]
  rw [packBytesNat_add x 8 8]
  rw [advanceBytes_eq]
  unfold packW
  rw [Nat.shiftLeft_eq]
  change
    packBytesNat x 8 +
        packBytesNat (x + 64 * stepConst) 8 * 2 ^ 64 =
      packBytesNat x 8 +
        256 ^ 8 * packBytesNat (x + 64 * stepConst) 8
  rw [show (2 ^ 64 : Nat) = 256 ^ 8 by decide]
  rw [Nat.mul_comm]

theorem dense128_eq_bytes16 (x : Nat) :
    dense128 x = packBytesNat x 16 := by
  unfold dense128
  rw [dense64_eq_bytes8 x, dense64_eq_bytes8 (x + 64 * stepConst)]
  exact packW64_bytes8 x

end DenseByteFixed
