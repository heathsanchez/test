import DenseByteSeqBoundProof

namespace DenseByteSequence

open Submission

theorem packBytesNat_add (x a b : Nat) :
    packBytesNat x (a + b) =
      packBytesNat x a +
        256 ^ a * packBytesNat (advanceBytes x a) b := by
  induction a generalizing x with
  | zero =>
      simp [packBytesNat, advanceBytes]
  | succ a ih =>
      simp only [Nat.succ_add, packBytesNat, advanceBytes, Nat.pow_succ]
      rw [ih (advance8 x), Nat.mul_add]
      have hmul :
          256 * (256 ^ a * packBytesNat (advanceBytes (advance8 x) a) b) =
            256 ^ a * 256 * packBytesNat (advanceBytes (advance8 x) a) b := by
        rw [← Nat.mul_assoc, Nat.mul_comm 256 (256 ^ a), Nat.mul_assoc]
      rw [hmul]
      exact (Nat.add_assoc _ _ _).symm

end DenseByteSequence
