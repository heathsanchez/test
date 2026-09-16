import DenseByteDefsProof

namespace DenseByteSequence

open Submission

theorem pack6Nat_lt64 (x : Nat) :
    pack6Nat x < 64 := by
  dsimp [pack6Nat]
  have h0 := mixBit31Nat_lt2 x
  have h1 := mixBit31Nat_lt2 (x + stepConst)
  have h2 := mixBit31Nat_lt2 (x + stepConst + stepConst)
  have h3 := mixBit31Nat_lt2 (x + stepConst + stepConst + stepConst)
  have h4 := mixBit31Nat_lt2 (x + stepConst + stepConst + stepConst + stepConst)
  have h5 := mixBit31Nat_lt2
    (x + stepConst + stepConst + stepConst + stepConst + stepConst)
  omega

end DenseByteSequence
