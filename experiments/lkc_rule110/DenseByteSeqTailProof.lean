import DenseByteSeqAddProof

namespace DenseByteSequence

open Submission

theorem packByteTailNat_eq_bytes_tail (x n : Nat) :
    packByteTailNat x n =
      packBytesNat x n +
        256 ^ n * pack6Nat (advanceBytes x n) := by
  induction n generalizing x with
  | zero =>
      simp [packByteTailNat, packBytesNat, advanceBytes]
  | succ n ih =>
      simp only [packByteTailNat, packBytesNat, advanceBytes, Nat.pow_succ]
      rw [ih (advance8 x), Nat.mul_add]
      have hmul :
          256 * (256 ^ n * pack6Nat (advanceBytes (advance8 x) n)) =
            256 ^ n * 256 * pack6Nat (advanceBytes (advance8 x) n) := by
        rw [← Nat.mul_assoc, Nat.mul_comm 256 (256 ^ n), Nat.mul_assoc]
      rw [hmul]
      exact (Nat.add_assoc _ _ _).symm

end DenseByteSequence
