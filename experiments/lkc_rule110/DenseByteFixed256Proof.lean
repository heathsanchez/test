import DenseByteFixed128Proof

namespace DenseByteFixed

open GenericPack
open WideGather
open DenseByteSequence
open Submission

theorem packW128_bytes16 (x : Nat) :
    packW 128
      (packBytesNat x 16)
      (packBytesNat (x + 128 * stepConst) 16) =
      packBytesNat x 32 := by
  rw [show (32 : Nat) = 16 + 16 by decide]
  rw [packBytesNat_add x 16 16]
  rw [advanceBytes_eq]
  unfold packW
  rw [Nat.shiftLeft_eq]
  change
    packBytesNat x 16 +
        packBytesNat (x + 128 * stepConst) 16 * 2 ^ 128 =
      packBytesNat x 16 +
        256 ^ 16 * packBytesNat (x + 128 * stepConst) 16
  rw [show (2 ^ 128 : Nat) = 256 ^ 16 by decide]
  rw [Nat.mul_comm]

theorem dense256_eq_bytes32 (x : Nat) :
    dense256 x = packBytesNat x 32 := by
  unfold dense256
  rw [dense128_eq_bytes16 x, dense128_eq_bytes16 (x + 128 * stepConst)]
  exact packW128_bytes16 x

end DenseByteFixed
