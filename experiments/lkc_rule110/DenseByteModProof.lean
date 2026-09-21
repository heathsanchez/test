import DenseByteDecompProof

namespace DenseByteSequence

open Submission

theorem pack8Nat_mod64_eq_pack6Nat (x : Nat) :
    pack8Nat x % 64 = pack6Nat x := by
  rw [pack8Nat_decomp6]
  rw [Nat.add_mul_mod_self_left]
  exact Nat.mod_eq_of_lt (pack6Nat_lt64 x)

end DenseByteSequence
