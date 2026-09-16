import DenseByteSeqTailProof

namespace DenseByteSequence

theorem pow256_eq_pow2 (n : Nat) :
    256 ^ n = 2 ^ (8 * n) := by
  rw [show 256 = 2 ^ 8 by decide]
  exact (Nat.pow_mul 2 8 n).symm

end DenseByteSequence
