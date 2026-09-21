import DenseByteModProof

namespace DenseByteSequence

open WideGather
open WideDenseByte
open Submission

theorem pack8Nat_lt256 (x : Nat) :
    pack8Nat x < 256 := by
  have h := dense8_lt x
  rw [dense8_eq_pack8Nat] at h
  simpa using h

end DenseByteSequence
