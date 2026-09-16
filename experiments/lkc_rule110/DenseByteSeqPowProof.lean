import DenseByteSeqTailProof

namespace DenseByteSequence

theorem pow256_eq_pow2 (n : Nat) :
    256 ^ n = 2 ^ (8 * n) := by
  induction n with
  | zero =>
      simp
  | succ n ih =>
      rw [Nat.pow_succ, Nat.mul_succ, Nat.pow_add, ← ih]
      rw [show 2 ^ 8 = 256 by decide]

end DenseByteSequence
