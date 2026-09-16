import DenseByteSeqPowProof

namespace DenseByteSequence

open GenericPack
open Submission

theorem shift_bytes_eq (q n : Nat) :
    q <<< (8 * n) = 256 ^ n * q := by
  rw [Nat.shiftLeft_eq]
  rw [← pow256_eq_pow2 n]
  exact Nat.mul_comm q (256 ^ n)

theorem packBytesNat_double (x n : Nat) :
    packW (8 * n)
      (packBytesNat x n)
      (packBytesNat (x + (8 * n) * stepConst) n) =
      packBytesNat x (n + n) := by
  calc
    packW (8 * n)
        (packBytesNat x n)
        (packBytesNat (x + (8 * n) * stepConst) n)
      =
        packBytesNat x n +
          256 ^ n * packBytesNat (x + (8 * n) * stepConst) n := by
            unfold packW
            rw [shift_bytes_eq]
    _ =
        packBytesNat x n +
          256 ^ n * packBytesNat (advanceBytes x n) n := by
            rw [advanceBytes_eq]
    _ = packBytesNat x (n + n) := by
          exact (packBytesNat_add x n n).symm

theorem packBytesNat_one (x : Nat) :
    packBytesNat x 1 = pack8Nat x := by
  rfl

end DenseByteSequence
