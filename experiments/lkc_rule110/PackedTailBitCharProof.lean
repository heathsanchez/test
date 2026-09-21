import DenseByteDefsProof
import Submission

namespace PackedTailBits

open Submission

theorem packMixBit_bit (x k i : Nat) :
    (packMixBit x k).testBit i =
      if i < k then mixBit31 (x + i * stepConst) else false := by
  induction k generalizing x i with
  | zero =>
      simp [packMixBit]
  | succ k ih =>
      cases i with
      | zero =>
          unfold packMixBit
          cases h : mixBit31 x <;> simp [h, Nat.testBit_zero]
      | succ i =>
          unfold packMixBit
          rw [Nat.testBit_succ]
          have hdiv :
              ((if mixBit31 x then 1 else 0) +
                2 * packMixBit (x + stepConst) k) / 2 =
                packMixBit (x + stepConst) k := by
            cases h : mixBit31 x <;> simp [h] <;> omega
          rw [hdiv, ih]
          simp only [Nat.succ_lt_succ_iff]
          by_cases h : i < k
          · rw [if_pos h, if_pos h]
            congr 1
            unfold stepConst
            omega
          · rw [if_neg h, if_neg h]

theorem packByteTailNat_bit (x n i : Nat) :
    (packByteTailNat x n).testBit i =
      if i < 8 * n + 6 then mixBit31 (x + i * stepConst) else false := by
  rw [packByteTailNat_eq, packByteTail_eq, packMixBit_bit]

end PackedTailBits
