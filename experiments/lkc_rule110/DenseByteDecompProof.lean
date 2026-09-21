import DenseByteSixProof

namespace DenseByteSequence

open Submission

theorem pack8Nat_decomp6 (x : Nat) :
    pack8Nat x =
      pack6Nat x +
        64 * (mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst) +
        2 * mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)) := by
  dsimp [pack8Nat, pack6Nat]
  omega

end DenseByteSequence
