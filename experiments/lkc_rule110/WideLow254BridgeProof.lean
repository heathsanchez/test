import WideDenseBitCharProof
import PackedTailBitCharProof

namespace WideLow254

open WideGather
open WideDenseBits
open PackedTailBits
open Submission

theorem dense256_low254_eq_tail (x : Nat) :
    dense256 x &&& (2 ^ 254 - 1) = packByteTailNat x 31 := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, Nat.testBit_two_pow_sub_one]
  rw [packByteTailNat_bit]
  by_cases hi : i < 254
  · have h256 : i < 256 := by omega
    rw [show decide (i < 254) = true by simp [hi]]
    simp only [Bool.and_true]
    rw [dense256_bit x i h256]
    rw [if_pos (by omega)]
  · rw [show decide (i < 254) = false by simp [hi]]
    simp only [Bool.and_false]
    rw [if_neg (by omega)]

end WideLow254
