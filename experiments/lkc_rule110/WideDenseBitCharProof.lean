import WideDenseByteProof

namespace WideDenseBits

set_option maxRecDepth 1048576
set_option maxHeartbeats 2000000

open GenericPack
open WideGather
open WideDenseByte
open Submission

theorem dense1_bit (x i : Nat) (hi : i < 1) :
    (dense1 x).testBit i = mixBit31 (x + i * stepConst) := by
  have hi0 : i = 0 := by omega
  subst i
  rw [dense1_eq_nat, mixBit31Nat_eq]
  cases h : mixBit31 x <;> simp [h, Nat.testBit_zero]

theorem dense2_bit (x i : Nat) (hi : i < 2) :
    (dense2 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense2
  rw [testBit_packW 1 (dense1 x) (dense1 (x + 1 * stepConst)) i (dense1_lt x)]
  by_cases h : i < 1
  · rw [if_pos h, dense1_bit x i h]
  · rw [if_neg h, dense1_bit (x + 1 * stepConst) (i - 1) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense4_bit (x i : Nat) (hi : i < 4) :
    (dense4 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense4
  rw [testBit_packW 2 (dense2 x) (dense2 (x + 2 * stepConst)) i (dense2_lt x)]
  by_cases h : i < 2
  · rw [if_pos h, dense2_bit x i h]
  · rw [if_neg h, dense2_bit (x + 2 * stepConst) (i - 2) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense8_bit (x i : Nat) (hi : i < 8) :
    (dense8 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense8
  rw [testBit_packW 4 (dense4 x) (dense4 (x + 4 * stepConst)) i (dense4_lt x)]
  by_cases h : i < 4
  · rw [if_pos h, dense4_bit x i h]
  · rw [if_neg h, dense4_bit (x + 4 * stepConst) (i - 4) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense16_bit (x i : Nat) (hi : i < 16) :
    (dense16 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense16
  rw [testBit_packW 8 (dense8 x) (dense8 (x + 8 * stepConst)) i (dense8_lt x)]
  by_cases h : i < 8
  · rw [if_pos h, dense8_bit x i h]
  · rw [if_neg h, dense8_bit (x + 8 * stepConst) (i - 8) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense32_bit (x i : Nat) (hi : i < 32) :
    (dense32 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense32
  rw [testBit_packW 16 (dense16 x) (dense16 (x + 16 * stepConst)) i (dense16_lt x)]
  by_cases h : i < 16
  · rw [if_pos h, dense16_bit x i h]
  · rw [if_neg h, dense16_bit (x + 16 * stepConst) (i - 16) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense64_bit (x i : Nat) (hi : i < 64) :
    (dense64 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense64
  rw [testBit_packW 32 (dense32 x) (dense32 (x + 32 * stepConst)) i (dense32_lt x)]
  by_cases h : i < 32
  · rw [if_pos h, dense32_bit x i h]
  · rw [if_neg h, dense32_bit (x + 32 * stepConst) (i - 32) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense128_bit (x i : Nat) (hi : i < 128) :
    (dense128 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense128
  rw [testBit_packW 64 (dense64 x) (dense64 (x + 64 * stepConst)) i (dense64_lt x)]
  by_cases h : i < 64
  · rw [if_pos h, dense64_bit x i h]
  · rw [if_neg h, dense64_bit (x + 64 * stepConst) (i - 64) (by omega)]
    congr 1
    unfold stepConst
    omega

theorem dense256_bit (x i : Nat) (hi : i < 256) :
    (dense256 x).testBit i = mixBit31 (x + i * stepConst) := by
  unfold dense256
  rw [testBit_packW 128 (dense128 x) (dense128 (x + 128 * stepConst)) i (dense128_lt x)]
  by_cases h : i < 128
  · rw [if_pos h, dense128_bit x i h]
  · rw [if_neg h, dense128_bit (x + 128 * stepConst) (i - 128) (by omega)]
    congr 1
    unfold stepConst
    omega

end WideDenseBits
