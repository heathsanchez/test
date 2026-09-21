import DenseByteBaseProof

namespace DenseByteSequence

open Submission

theorem packBytesNat_lt (x n : Nat) :
    packBytesNat x n < 256 ^ n := by
  induction n generalizing x with
  | zero =>
      simp [packBytesNat]
  | succ n ih =>
      simp only [packBytesNat, Nat.pow_succ]
      have hb := pack8Nat_lt256 x
      have ht := ih (advance8 x)
      omega

end DenseByteSequence
