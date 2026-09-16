import DenseByteSeqPowProof

namespace DenseByteSequence

open GenericPack
open Submission

theorem packBytesNat_double (x n : Nat) :
    packW (8 * n)
      (packBytesNat x n)
      (packBytesNat (x + (8 * n) * stepConst) n) =
      packBytesNat x (n + n) := by
  unfold packW
  rw [packBytesNat_add x n n]
  rw [advanceBytes_eq]
  rw [Nat.shiftLeft_eq]
  rw [← pow256_eq_pow2 n]
  rw [Nat.mul_comm
    (packBytesNat (x + (8 * n) * stepConst) n)
    (256 ^ n)]

theorem packBytesNat_one (x : Nat) :
    packBytesNat x 1 = pack8Nat x := by
  simp [packBytesNat]

end DenseByteSequence
