import Spec

namespace SWAR

def mask32 : Nat := 0xffffffff

def mask2 : Nat :=
  mask32 ||| (mask32 <<< 64)

def pack2 (x y : Nat) : Nat :=
  x + (y <<< 64)

def u32 (x : Nat) : Nat :=
  (x ^^^ (x >>> 16)) &&& mask32

theorem mask32_eq : mask32 = 2 ^ 32 - 1 := by decide

theorem testBit_mask32 (i : Nat) :
    mask32.testBit i = decide (i < 32) := by
  rw [mask32_eq, Nat.testBit_two_pow_sub_one]

theorem testBit_mask2 (i : Nat) :
    mask2.testBit i =
      (decide (i < 32) || (decide (64 ≤ i) && decide (i - 64 < 32))) := by
  unfold mask2
  rw [Nat.testBit_or, Nat.testBit_shiftLeft, testBit_mask32, testBit_mask32]

theorem testBit_pack2 (x y i : Nat) (hx : x < 2 ^ 64) :
    (pack2 x y).testBit i =
      if i < 64 then x.testBit i else y.testBit (i - 64) := by
  unfold pack2
  simpa [Nat.add_comm, Nat.shiftLeft_eq, Nat.mul_comm] using
    (Nat.testBit_two_pow_mul_add y hx i)

theorem u32_lt (x : Nat) : u32 x < 2 ^ 64 := by
  unfold u32
  have hle : ((x ^^^ (x >>> 16)) &&& mask32) ≤ mask32 := Nat.and_le_right
  have hm : mask32 < 2 ^ 64 := by decide
  omega

theorem packed_u32 (x y : Nat) (hx : x < 2 ^ 64) :
    ((pack2 x y ^^^ (pack2 x y >>> 16)) &&& mask2) =
      pack2 (u32 x) (u32 y) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask2]
  rw [testBit_pack2 (u32 x) (u32 y) i (u32_lt x)]
  simp only [u32, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight,
    testBit_mask32]
  by_cases h32 : i < 32
  · have h64 : i < 64 := by omega
    have h80 : 16 + i < 64 := by omega
    rw [testBit_pack2 x y i hx, testBit_pack2 x y (16 + i) hx]
    simp [h32, h64, h80]
  · by_cases h64 : i < 64
    · have hn64 : ¬64 ≤ i := by omega
      simp [h32, h64, hn64]
    · by_cases h96 : i < 96
      · have hi64 : 64 ≤ i := by omega
        have hj32 : i - 64 < 32 := by omega
        have h16hi : ¬16 + i < 64 := by omega
        have hj16 : (16 + i) - 64 = 16 + (i - 64) := by omega
        rw [testBit_pack2 x y i hx, testBit_pack2 x y (16 + i) hx]
        simp [h32, h64, hi64, hj32, h16hi, hj16]
      · have hi64 : 64 ≤ i := by omega
        have hji : ¬i - 64 < 32 := by omega
        simp [h32, h64, hi64, hji]


def c1 : Nat := 0x7feb352d
def c2 : Nat := 0x846ca68b

def y32 (x : Nat) : Nat :=
  (u32 x * c1) &&& mask32

def v32 (x : Nat) : Nat :=
  (x ^^^ (x >>> 15)) &&& mask32

def bit31Nat (x : Nat) : Nat :=
  (x >>> 31) % 2

theorem masked32_lt32 (x : Nat) : (x &&& mask32) < 2 ^ 32 := by
  have hle : (x &&& mask32) ≤ mask32 := Nat.and_le_right
  have hm : mask32 < 2 ^ 32 := by decide
  exact Nat.lt_of_le_of_lt hle hm

theorem masked32_lt64 (x : Nat) : (x &&& mask32) < 2 ^ 64 :=
  Nat.lt_trans (masked32_lt32 x) (by decide)

theorem mask_pack2 (x y : Nat) (hx : x < 2 ^ 64) :
    (pack2 x y &&& mask2) =
      pack2 (x &&& mask32) (y &&& mask32) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask2]
  rw [testBit_pack2 (x &&& mask32) (y &&& mask32) i (masked32_lt64 x)]
  simp only [Nat.testBit_and, testBit_mask32]
  by_cases h32 : i < 32
  · have h64 : i < 64 := by omega
    rw [testBit_pack2 x y i hx]
    simp [h32, h64]
  · by_cases h64 : i < 64
    · have hn64 : ¬64 ≤ i := by omega
      simp [h32, h64, hn64]
    · by_cases h96 : i < 96
      · have hi64 : 64 ≤ i := by omega
        have hj32 : i - 64 < 32 := by omega
        rw [testBit_pack2 x y i hx]
        simp [h32, h64, hi64, hj32]
      · have hi64 : 64 ≤ i := by omega
        have hji : ¬i - 64 < 32 := by omega
        simp [h32, h64, hi64, hji]

theorem pack2_mul (a b k : Nat) :
    pack2 a b * k = pack2 (a * k) (b * k) := by
  unfold pack2
  rw [Nat.add_mul, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  congr 1
  calc
    (b * 2 ^ 64) * k = b * (2 ^ 64 * k) := Nat.mul_assoc _ _ _
    _ = b * (k * 2 ^ 64) := by rw [Nat.mul_comm (2 ^ 64) k]
    _ = (b * k) * 2 ^ 64 := (Nat.mul_assoc _ _ _).symm

theorem mul_mask_pack2 (a b k : Nat) (hprod : a * k < 2 ^ 64) :
    (pack2 a b * k) &&& mask2 =
      pack2 ((a * k) &&& mask32) ((b * k) &&& mask32) := by
  rw [pack2_mul]
  exact mask_pack2 (a * k) (b * k) hprod

theorem u32_lt32 (x : Nat) : u32 x < 2 ^ 32 := by
  unfold u32
  exact masked32_lt32 _

theorem u32_mul_c1_lt64 (x : Nat) : u32 x * c1 < 2 ^ 64 := by
  calc
    u32 x * c1 < (2 ^ 32) * c1 :=
      Nat.mul_lt_mul_of_pos_right (u32_lt32 x) (by decide)
    _ < (2 ^ 32) * (2 ^ 32) :=
      Nat.mul_lt_mul_of_pos_left (by decide) (Nat.two_pow_pos 32)
    _ = 2 ^ 64 := by decide

theorem packed_y32 (x y : Nat) (hx : x < 2 ^ 64) :
    ((((pack2 x y ^^^ (pack2 x y >>> 16)) &&& mask2) * c1) &&& mask2) =
      pack2 (y32 x) (y32 y) := by
  rw [packed_u32 x y hx]
  unfold y32
  exact mul_mask_pack2 (u32 x) (u32 y) c1 (u32_mul_c1_lt64 x)

theorem y32_lt32 (x : Nat) : y32 x < 2 ^ 32 := by
  unfold y32
  exact masked32_lt32 _

theorem y32_lt64 (x : Nat) : y32 x < 2 ^ 64 :=
  Nat.lt_trans (y32_lt32 x) (by decide)

theorem packed_v32 (x y : Nat) (hx : x < 2 ^ 64) :
    ((pack2 x y ^^^ (pack2 x y >>> 15)) &&& mask2) =
      pack2 (v32 x) (v32 y) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask2]
  rw [testBit_pack2 (v32 x) (v32 y) i (by
    unfold v32
    exact masked32_lt64 _)]
  simp only [v32, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight,
    testBit_mask32]
  by_cases h32 : i < 32
  · have h64 : i < 64 := by omega
    have h79 : 15 + i < 64 := by omega
    rw [testBit_pack2 x y i hx, testBit_pack2 x y (15 + i) hx]
    simp [h32, h64, h79]
  · by_cases h64 : i < 64
    · have hn64 : ¬64 ≤ i := by omega
      simp [h32, h64, hn64]
    · by_cases h96 : i < 96
      · have hi64 : 64 ≤ i := by omega
        have hj32 : i - 64 < 32 := by omega
        have h15hi : ¬15 + i < 64 := by omega
        have hj15 : (15 + i) - 64 = 15 + (i - 64) := by omega
        rw [testBit_pack2 x y i hx, testBit_pack2 x y (15 + i) hx]
        simp [h32, h64, hi64, hj32, h15hi, hj15]
      · have hi64 : 64 ≤ i := by omega
        have hji : ¬i - 64 < 32 := by omega
        simp [h32, h64, hi64, hji]

theorem v32_lt32 (x : Nat) : v32 x < 2 ^ 32 := by
  unfold v32
  exact masked32_lt32 _

theorem v32_mul_c2_lt64 (x : Nat) : v32 x * c2 < 2 ^ 64 := by
  calc
    v32 x * c2 < (2 ^ 32) * c2 :=
      Nat.mul_lt_mul_of_pos_right (v32_lt32 x) (by decide)
    _ < (2 ^ 32) * (2 ^ 32) :=
      Nat.mul_lt_mul_of_pos_left (by decide) (Nat.two_pow_pos 32)
    _ = 2 ^ 64 := by decide

theorem packed_p2 (x y : Nat) :
    pack2 (v32 x) (v32 y) * c2 =
      pack2 (v32 x * c2) (v32 y * c2) := by
  exact pack2_mul (v32 x) (v32 y) c2

theorem bit31_pack2_low (a b : Nat) (ha : a < 2 ^ 64) :
    bit31Nat (pack2 a b) = bit31Nat a := by
  have h := congrArg Bool.toNat (testBit_pack2 a b 31 ha)
  simp only [show 31 < 64 by decide, if_pos] at h
  unfold bit31Nat
  simpa [Nat.toNat_testBit, Nat.shiftRight_eq_div_pow] using h

theorem bit31_pack2_high (a b : Nat) (ha : a < 2 ^ 64) :
    ((pack2 a b >>> 95) % 2) = bit31Nat b := by
  have h := congrArg Bool.toNat (testBit_pack2 a b 95 ha)
  simp only [show ¬95 < 64 by decide] at h
  have hsub : 95 - 64 = 31 := by decide
  rw [hsub] at h
  unfold bit31Nat
  simpa [Nat.toNat_testBit, Nat.shiftRight_eq_div_pow] using h

def mixPairSWAR (x y : Nat) : Nat :=
  let p0 := pack2 x y
  let u := (p0 ^^^ (p0 >>> 16)) &&& mask2
  let yv := (u * c1) &&& mask2
  let v := (yv ^^^ (yv >>> 15)) &&& mask2
  let p := v * c2
  (p >>> 31) % 2 + 2 * ((p >>> 95) % 2)

def mixScalarNat (x : Nat) : Nat :=
  bit31Nat (v32 (y32 x) * c2)

theorem mixPairSWAR_eq (x y : Nat) (hx : x < 2 ^ 64) :
    mixPairSWAR x y = mixScalarNat x + 2 * mixScalarNat y := by
  simp only [mixPairSWAR]
  rw [packed_y32 x y hx]
  rw [packed_v32 (y32 x) (y32 y) (y32_lt64 x)]
  rw [packed_p2]
  change
    bit31Nat (pack2 (v32 (y32 x) * c2) (v32 (y32 y) * c2)) +
      2 * ((pack2 (v32 (y32 x) * c2) (v32 (y32 y) * c2) >>> 95) % 2) =
      mixScalarNat x + 2 * mixScalarNat y
  rw [bit31_pack2_low _ _ (v32_mul_c2_lt64 (y32 x))]
  rw [bit31_pack2_high _ _ (v32_mul_c2_lt64 (y32 x))]
  rfl


def scalarRef (x : Nat) : Nat :=
  let y := ((x ^^^ (x >>> 16)) * c1) &&& mask32
  (((y ^^^ (y >>> 15)) * c2) >>> 31) % 2

theorem y32_eq_ref (x : Nat) :
    y32 x = ((x ^^^ (x >>> 16)) * c1) &&& mask32 := by
  unfold y32 u32
  rw [mask32_eq]
  simp only [Nat.and_two_pow_sub_one_eq_mod]
  have hc : c1 < 2 ^ 32 := by decide
  simp [Nat.mul_mod, Nat.mod_eq_of_lt hc]

theorem v32_eq_raw (x : Nat) (hx : x < 2 ^ 32) :
    v32 x = x ^^^ (x >>> 15) := by
  have hs : x >>> 15 < 2 ^ 32 :=
    Nat.lt_of_le_of_lt (Nat.shiftRight_le x 15) hx
  have hz : (x ^^^ (x >>> 15)) < 2 ^ 32 :=
    Nat.xor_lt_two_pow hx hs
  unfold v32
  rw [mask32_eq]
  exact Nat.and_two_pow_sub_one_of_lt_two_pow hz

theorem mixScalarNat_eq_ref (x : Nat) :
    mixScalarNat x = scalarRef x := by
  unfold mixScalarNat scalarRef bit31Nat
  rw [y32_eq_ref]
  let y := ((x ^^^ (x >>> 16)) * c1) &&& mask32
  have hy : y < 2 ^ 32 := by
    dsimp [y]
    exact masked32_lt32 _
  have hv : v32 y = y ^^^ (y >>> 15) :=
    v32_eq_raw y hy
  rw [hv]


/-! Four-lane lift: two proven 2-lane words separated by 128 bits. -/

def pack128 (p q : Nat) : Nat :=
  p + (q <<< 128)

def mask4 : Nat :=
  pack128 mask2 mask2

def pack4 (a b c d : Nat) : Nat :=
  pack128 (pack2 a b) (pack2 c d)

theorem mask2_lt128 : mask2 < 2 ^ 128 := by decide

theorem testBit_pack128 (p q i : Nat) (hp : p < 2 ^ 128) :
    (pack128 p q).testBit i =
      if i < 128 then p.testBit i else q.testBit (i - 128) := by
  unfold pack128
  rw [Nat.add_comm, Nat.shiftLeft_eq, Nat.mul_comm]
  exact Nat.testBit_two_pow_mul_add q hp i

theorem testBit_mask4 (i : Nat) :
    mask4.testBit i =
      if i < 128 then mask2.testBit i else mask2.testBit (i - 128) := by
  unfold mask4
  exact testBit_pack128 mask2 mask2 i mask2_lt128

def pairStage (s p : Nat) : Nat :=
  (p ^^^ (p >>> s)) &&& mask2

theorem pairStage_lt128 (s p : Nat) :
    pairStage s p < 2 ^ 128 := by
  unfold pairStage
  have hle : ((p ^^^ (p >>> s)) &&& mask2) ≤ mask2 := Nat.and_le_right
  exact Nat.lt_of_le_of_lt hle mask2_lt128

theorem lift_pair_stage (p q s : Nat)
    (hp : p < 2 ^ 128) (hs0 : 0 < s) (hs : s ≤ 32) :
    ((pack128 p q ^^^ (pack128 p q >>> s)) &&& mask4) =
      pack128 (pairStage s p) (pairStage s q) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask4]
  rw [testBit_pack128 (pairStage s p) (pairStage s q) i (pairStage_lt128 s p)]
  simp only [pairStage, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight]
  by_cases h128 : i < 128
  · rw [if_pos h128, if_pos h128]
    by_cases h32 : i < 32
    · have his : s + i < 128 := by omega
      rw [Nat.testBit_xor, Nat.testBit_shiftRight]
      rw [testBit_pack128 p q i hp, testBit_pack128 p q (s+i) hp]
      simp [h128, his, h32, testBit_mask2]
    · by_cases h64 : i < 64
      · have hn64 : ¬64 ≤ i := by omega
        simp [h32, h64, hn64, testBit_mask2]
      · by_cases h96 : i < 96
        · have hi64 : 64 ≤ i := by omega
          have hj32 : i - 64 < 32 := by omega
          have his : s + i < 128 := by omega
          rw [Nat.testBit_xor, Nat.testBit_shiftRight]
          rw [testBit_pack128 p q i hp, testBit_pack128 p q (s+i) hp]
          simp [h128, his, h32, h64, hi64, hj32, testBit_mask2]
        · have hi64 : 64 ≤ i := by omega
          have hji : ¬i - 64 < 32 := by omega
          simp [h32, h64, hi64, hji, testBit_mask2]
  · rw [if_neg h128, if_neg h128]
    by_cases h256 : i < 256
    · have hi128 : 128 ≤ i := by omega
      let j := i - 128
      have hj128 : j < 128 := by dsimp [j]; omega
      have hij : i = 128 + j := by dsimp [j]; omega
      by_cases hj32 : j < 32
      · have hsj : s + j < 128 := by omega
        have hsihi : ¬s + i < 128 := by omega
        have hslt256 : s + i < 256 := by
          rw [hij]
          omega
        rw [Nat.testBit_xor, Nat.testBit_shiftRight]
        rw [testBit_pack128 p q i hp, testBit_pack128 p q (s+i) hp]
        have hsub : (s + i) - 128 = s + j := by rw [hij]; omega
        simp [h128, hi128, h256, hsihi, hslt256, hj32, hsub, testBit_mask2]
      · by_cases hj64 : j < 64
        · have hn64 : ¬64 ≤ j := by omega
          simp [hj32, hj64, hn64, testBit_mask2]
        · by_cases hj96 : j < 96
          · have hj64le : 64 ≤ j := by omega
            have hjj32 : j - 64 < 32 := by omega
            have hsihi : ¬s + i < 128 := by omega
            have hslt256 : s + i < 256 := by
              rw [hij]
              omega
            rw [Nat.testBit_xor, Nat.testBit_shiftRight]
            rw [testBit_pack128 p q i hp, testBit_pack128 p q (s+i) hp]
            have hsub : (s + i) - 128 = s + j := by rw [hij]; omega
            simp [h128, hi128, h256, hsihi, hslt256, hj32, hj64, hj64le,
              hjj32, hsub, testBit_mask2]
          · have hj64le : 64 ≤ j := by omega
            have hjj : ¬j - 64 < 32 := by omega
            simp [hj32, hj64, hj64le, hjj, testBit_mask2]
    · have hi256 : 256 ≤ i := by omega
      have hj : ¬(i - 128 < 128) := by omega
      have hj32 : ¬(i - 128 < 32) := by omega
      have hj64 : 64 ≤ i - 128 := by omega
      have hjj : ¬(i - 128) - 64 < 32 := by omega
      simp [h128, h256, hi256, hj, hj32, hj64, hjj, testBit_mask2]

theorem pack128_mul (p q k : Nat) :
    pack128 p q * k = pack128 (p * k) (q * k) := by
  unfold pack128
  rw [Nat.add_mul, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  congr 1
  calc
    (q * 2 ^ 128) * k = q * (2 ^ 128 * k) := Nat.mul_assoc _ _ _
    _ = q * (k * 2 ^ 128) := by rw [Nat.mul_comm (2 ^ 128) k]
    _ = (q * k) * 2 ^ 128 := (Nat.mul_assoc _ _ _).symm

end SWAR
