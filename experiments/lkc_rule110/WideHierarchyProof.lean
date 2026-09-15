import GenericPackProof
import GenericMixProof
import Submission

namespace WideHierarchy

set_option maxRecDepth 1048576
set_option exponentiation.threshold 20000
set_option maxHeartbeats 2000000

open GenericPack
open GenericMix
open Submission

def state1 (x : Nat) : Nat := x
def state2 (x : Nat) : Nat := packW 64 (state1 x) (state1 (x + stepConst))
def state4 (x : Nat) : Nat := packW 128 (state2 x) (state2 (x + 2 * stepConst))
def state8 (x : Nat) : Nat := packW 256 (state4 x) (state4 (x + 4 * stepConst))
def state16 (x : Nat) : Nat := packW 512 (state8 x) (state8 (x + 8 * stepConst))
def state32 (x : Nat) : Nat := packW 1024 (state16 x) (state16 (x + 16 * stepConst))
def state64 (x : Nat) : Nat := packW 2048 (state32 x) (state32 (x + 32 * stepConst))
def state128 (x : Nat) : Nat := packW 4096 (state64 x) (state64 (x + 64 * stepConst))
def state256 (x : Nat) : Nat := packW 8192 (state128 x) (state128 (x + 128 * stepConst))

def mask1 : Nat := 0xffffffff
def mask2 : Nat := maskW 64 mask1
def mask4 : Nat := maskW 128 mask2
def mask8 : Nat := maskW 256 mask4
def mask16 : Nat := maskW 512 mask8
def mask32 : Nat := maskW 1024 mask16
def mask64 : Nat := maskW 2048 mask32
def mask128 : Nat := maskW 4096 mask64
def mask256 : Nat := maskW 8192 mask128

def ones1 : Nat := 1
def ones2 : Nat := maskW 64 ones1
def ones4 : Nat := maskW 128 ones2
def ones8 : Nat := maskW 256 ones4
def ones16 : Nat := maskW 512 ones8
def ones32 : Nat := maskW 1024 ones16
def ones64 : Nat := maskW 2048 ones32
def ones128 : Nat := maskW 4096 ones64
def ones256 : Nat := maskW 8192 ones128

def raw1 (x : Nat) : Nat := mixCore mask1 (state1 x)
def raw2 (x : Nat) : Nat := mixCore mask2 (state2 x)
def raw4 (x : Nat) : Nat := mixCore mask4 (state4 x)
def raw8 (x : Nat) : Nat := mixCore mask8 (state8 x)
def raw16 (x : Nat) : Nat := mixCore mask16 (state16 x)
def raw32 (x : Nat) : Nat := mixCore mask32 (state32 x)
def raw64 (x : Nat) : Nat := mixCore mask64 (state64 x)
def raw128 (x : Nat) : Nat := mixCore mask128 (state128 x)
def raw256 (x : Nat) : Nat := mixCore mask256 (state256 x)

def bits1 (x : Nat) : Nat := shrMask ones1 31 (raw1 x)
def bits2 (x : Nat) : Nat := shrMask ones2 31 (raw2 x)
def bits4 (x : Nat) : Nat := shrMask ones4 31 (raw4 x)
def bits8 (x : Nat) : Nat := shrMask ones8 31 (raw8 x)
def bits16 (x : Nat) : Nat := shrMask ones16 31 (raw16 x)
def bits32 (x : Nat) : Nat := shrMask ones32 31 (raw32 x)
def bits64 (x : Nat) : Nat := shrMask ones64 31 (raw64 x)
def bits128 (x : Nat) : Nat := shrMask ones128 31 (raw128 x)
def bits256 (x : Nat) : Nat := shrMask ones256 31 (raw256 x)

theorem state2_lt (x : Nat) (h : x + stepConst < 2 ^ 64) :
    state2 x < 2 ^ 128 := by
  unfold state2 state1
  exact packW_lt_double 64 x (x + stepConst) (by omega) h

theorem state4_lt (x : Nat) (h : x + 3 * stepConst < 2 ^ 64) :
    state4 x < 2 ^ 256 := by
  unfold state4
  apply packW_lt_double 128
  · exact state2_lt x (by omega)
  · exact state2_lt (x + 2 * stepConst) (by omega)

theorem state8_lt (x : Nat) (h : x + 7 * stepConst < 2 ^ 64) :
    state8 x < 2 ^ 512 := by
  unfold state8
  apply packW_lt_double 256
  · exact state4_lt x (by omega)
  · exact state4_lt (x + 4 * stepConst) (by omega)

theorem state16_lt (x : Nat) (h : x + 15 * stepConst < 2 ^ 64) :
    state16 x < 2 ^ 1024 := by
  unfold state16
  apply packW_lt_double 512
  · exact state8_lt x (by omega)
  · exact state8_lt (x + 8 * stepConst) (by omega)

theorem state32_lt (x : Nat) (h : x + 31 * stepConst < 2 ^ 64) :
    state32 x < 2 ^ 2048 := by
  unfold state32
  apply packW_lt_double 1024
  · exact state16_lt x (by omega)
  · exact state16_lt (x + 16 * stepConst) (by omega)

theorem state64_lt (x : Nat) (h : x + 63 * stepConst < 2 ^ 64) :
    state64 x < 2 ^ 4096 := by
  unfold state64
  apply packW_lt_double 2048
  · exact state32_lt x (by omega)
  · exact state32_lt (x + 32 * stepConst) (by omega)

theorem state128_lt (x : Nat) (h : x + 127 * stepConst < 2 ^ 64) :
    state128 x < 2 ^ 8192 := by
  unfold state128
  apply packW_lt_double 4096
  · exact state64_lt x (by omega)
  · exact state64_lt (x + 64 * stepConst) (by omega)

theorem state256_lt (x : Nat) (h : x + 255 * stepConst < 2 ^ 64) :
    state256 x < 2 ^ 16384 := by
  unfold state256
  apply packW_lt_double 8192
  · exact state128_lt x (by omega)
  · exact state128_lt (x + 128 * stepConst) (by omega)

set_option maxRecDepth 1048576 in
theorem state8_eq_octState (x : Nat) :
    state8 x = octState x := by
  unfold state8 state4 state2 state1 octState
  unfold packW Vec8.pack8v Vec8.pack256 Vec8.pack4 Vec8.pack128 Vec8.pack2
  simp only [Nat.shiftLeft_eq]
  omega

theorem raw2_eq (x : Nat) (h : x + stepConst < 2 ^ 64) :
    raw2 x = packW 64 (raw1 x) (raw1 (x + stepConst)) := by
  unfold raw2 raw1 state2 state1 mask2 mask1
  exact mixCore_double 64 0xffffffff x (x + stepConst)
    (by decide) (by omega) (by decide) (by decide) (by decide)

theorem raw4_eq (x : Nat) (h : x + 3 * stepConst < 2 ^ 64) :
    raw4 x = packW 128 (raw2 x) (raw2 (x + 2 * stepConst)) := by
  unfold raw4 state4 mask4
  exact mixCore_double 128 mask2 (state2 x) (state2 (x + 2 * stepConst))
    (by decide) (state2_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw8_eq (x : Nat) (h : x + 7 * stepConst < 2 ^ 64) :
    raw8 x = packW 256 (raw4 x) (raw4 (x + 4 * stepConst)) := by
  unfold raw8 state8 mask8
  exact mixCore_double 256 mask4 (state4 x) (state4 (x + 4 * stepConst))
    (by decide) (state4_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw16_eq (x : Nat) (h : x + 15 * stepConst < 2 ^ 64) :
    raw16 x = packW 512 (raw8 x) (raw8 (x + 8 * stepConst)) := by
  unfold raw16 state16 mask16
  exact mixCore_double 512 mask8 (state8 x) (state8 (x + 8 * stepConst))
    (by decide) (state8_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw32_eq (x : Nat) (h : x + 31 * stepConst < 2 ^ 64) :
    raw32 x = packW 1024 (raw16 x) (raw16 (x + 16 * stepConst)) := by
  unfold raw32 state32 mask32
  exact mixCore_double 1024 mask16 (state16 x) (state16 (x + 16 * stepConst))
    (by decide) (state16_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw64_eq (x : Nat) (h : x + 63 * stepConst < 2 ^ 64) :
    raw64 x = packW 2048 (raw32 x) (raw32 (x + 32 * stepConst)) := by
  unfold raw64 state64 mask64
  exact mixCore_double 2048 mask32 (state32 x) (state32 (x + 32 * stepConst))
    (by decide) (state32_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw128_eq (x : Nat) (h : x + 127 * stepConst < 2 ^ 64) :
    raw128 x = packW 4096 (raw64 x) (raw64 (x + 64 * stepConst)) := by
  unfold raw128 state128 mask128
  exact mixCore_double 4096 mask64 (state64 x) (state64 (x + 64 * stepConst))
    (by decide) (state64_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw256_eq (x : Nat) (h : x + 255 * stepConst < 2 ^ 64) :
    raw256 x = packW 8192 (raw128 x) (raw128 (x + 128 * stepConst)) := by
  unfold raw256 state256 mask256
  exact mixCore_double 8192 mask128 (state128 x) (state128 (x + 128 * stepConst))
    (by decide) (state128_lt x (by omega)) (by decide) (by decide) (by decide)

theorem raw1_lt (x : Nat) : raw1 x < 2 ^ 64 := by
  unfold raw1 mask1
  exact mixCore_lt 64 0xffffffff x (by decide)

theorem raw2_lt (x : Nat) : raw2 x < 2 ^ 128 := by
  unfold raw2 mask2
  exact mixCore_lt 128 mask2 (state2 x) (by decide)
theorem raw4_lt (x : Nat) : raw4 x < 2 ^ 256 := by
  unfold raw4 mask4
  exact mixCore_lt 256 mask4 (state4 x) (by decide)
theorem raw8_lt (x : Nat) : raw8 x < 2 ^ 512 := by
  unfold raw8 mask8
  exact mixCore_lt 512 mask8 (state8 x) (by decide)
theorem raw16_lt (x : Nat) : raw16 x < 2 ^ 1024 := by
  unfold raw16 mask16
  exact mixCore_lt 1024 mask16 (state16 x) (by decide)
theorem raw32_lt (x : Nat) : raw32 x < 2 ^ 2048 := by
  unfold raw32 mask32
  exact mixCore_lt 2048 mask32 (state32 x) (by decide)
theorem raw64_lt (x : Nat) : raw64 x < 2 ^ 4096 := by
  unfold raw64 mask64
  exact mixCore_lt 4096 mask64 (state64 x) (by decide)
theorem raw128_lt (x : Nat) : raw128 x < 2 ^ 8192 := by
  unfold raw128 mask128
  exact mixCore_lt 8192 mask128 (state128 x) (by decide)

theorem bits2_eq (x : Nat) (h : x + stepConst < 2 ^ 64) :
    bits2 x = packW 64 (bits1 x) (bits1 (x + stepConst)) := by
  unfold bits2 ones2
  rw [raw2_eq x h]
  exact lift_shrMask 64 ones1 31 (raw1 x) (raw1 (x + stepConst))
    (raw1_lt x) (by decide) (by decide) (by decide)

theorem bits4_eq (x : Nat) (h : x + 3 * stepConst < 2 ^ 64) :
    bits4 x = packW 128 (bits2 x) (bits2 (x + 2 * stepConst)) := by
  unfold bits4 ones4
  rw [raw4_eq x h]
  exact lift_shrMask 128 ones2 31 (raw2 x) (raw2 (x + 2 * stepConst))
    (raw2_lt x) (by decide) (by decide) (by decide)

theorem bits8_eq (x : Nat) (h : x + 7 * stepConst < 2 ^ 64) :
    bits8 x = packW 256 (bits4 x) (bits4 (x + 4 * stepConst)) := by
  unfold bits8 ones8
  rw [raw8_eq x h]
  exact lift_shrMask 256 ones4 31 (raw4 x) (raw4 (x + 4 * stepConst))
    (raw4_lt x) (by decide) (by decide) (by decide)

theorem bits16_eq (x : Nat) (h : x + 15 * stepConst < 2 ^ 64) :
    bits16 x = packW 512 (bits8 x) (bits8 (x + 8 * stepConst)) := by
  unfold bits16 ones16
  rw [raw16_eq x h]
  exact lift_shrMask 512 ones8 31 (raw8 x) (raw8 (x + 8 * stepConst))
    (raw8_lt x) (by decide) (by decide) (by decide)

theorem bits32_eq (x : Nat) (h : x + 31 * stepConst < 2 ^ 64) :
    bits32 x = packW 1024 (bits16 x) (bits16 (x + 16 * stepConst)) := by
  unfold bits32 ones32
  rw [raw32_eq x h]
  exact lift_shrMask 1024 ones16 31 (raw16 x) (raw16 (x + 16 * stepConst))
    (raw16_lt x) (by decide) (by decide) (by decide)

theorem bits64_eq (x : Nat) (h : x + 63 * stepConst < 2 ^ 64) :
    bits64 x = packW 2048 (bits32 x) (bits32 (x + 32 * stepConst)) := by
  unfold bits64 ones64
  rw [raw64_eq x h]
  exact lift_shrMask 2048 ones32 31 (raw32 x) (raw32 (x + 32 * stepConst))
    (raw32_lt x) (by decide) (by decide) (by decide)

theorem bits128_eq (x : Nat) (h : x + 127 * stepConst < 2 ^ 64) :
    bits128 x = packW 4096 (bits64 x) (bits64 (x + 64 * stepConst)) := by
  unfold bits128 ones128
  rw [raw128_eq x h]
  exact lift_shrMask 4096 ones64 31 (raw64 x) (raw64 (x + 64 * stepConst))
    (raw64_lt x) (by decide) (by decide) (by decide)

theorem bits256_eq (x : Nat) (h : x + 255 * stepConst < 2 ^ 64) :
    bits256 x = packW 8192 (bits128 x) (bits128 (x + 128 * stepConst)) := by
  unfold bits256 ones256
  rw [raw256_eq x h]
  exact lift_shrMask 8192 ones128 31 (raw128 x) (raw128 (x + 128 * stepConst))
    (raw128_lt x) (by decide) (by decide) (by decide)

theorem and_one_mod2 (n : Nat) :
    n &&& 1 = n % 2 := by
  have h1 : (1 : Nat) = 2 ^ 1 - 1 := by decide
  rw [h1, Nat.and_two_pow_sub_one_eq_mod]

theorem bits1_eq_mix (x : Nat) :
    bits1 x = mixBit31Nat x := by
  unfold bits1 ones1 raw1 state1 mixCore shrMask mask1
  rw [and_one_mod2]
  change Vec8.mixScalarNat x = mixBit31Nat x
  rw [Vec8.mixScalarNat_eq_ref, vec8Scalar_eq]

end WideHierarchy
