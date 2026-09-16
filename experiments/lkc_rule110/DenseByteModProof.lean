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

theorem pack8Nat_mod64_eq_pack6Nat (x : Nat) :
    pack8Nat x % 64 = pack6Nat x := by
  rw [pack8Nat_decomp6]
  have hl := pack6Nat_lt64 x
  rw [Nat.add_mod, Nat.mod_eq_of_lt hl]
  have hm :
      (64 * (mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst) +
        2 * mixBit31Nat
          (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst))) % 64 = 0 := by
    rw [Nat.mul_mod]
    simp
  rw [hm]
  simp

end DenseByteSequence
