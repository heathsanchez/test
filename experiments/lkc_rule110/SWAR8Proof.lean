import Spec

namespace SWAR

set_option linter.unusedSimpArgs false

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
    by_cases hm : mask2.testBit i = true
    · have hrange : i < 32 ∨ (64 ≤ i ∧ i - 64 < 32) := by
        rw [testBit_mask2] at hm
        simpa using hm
      have hi96 : i < 96 := by omega
      have his : s + i < 128 := by omega
      rw [testBit_pack128 p q i hp, testBit_pack128 p q (s + i) hp]
      simp [h128, his, hm]
    · have hmf : mask2.testBit i = false := by
        cases h : mask2.testBit i <;> simp_all
      simp [hmf]
  · rw [if_neg h128, if_neg h128]
    have hi128 : 128 ≤ i := by omega
    let j := i - 128
    have hij : i = 128 + j := by dsimp [j]; omega
    by_cases hm : mask2.testBit j = true
    · have hrange : j < 32 ∨ (64 ≤ j ∧ j - 64 < 32) := by
        rw [testBit_mask2] at hm
        simpa using hm
      have hj96 : j < 96 := by omega
      have hsj : s + j < 128 := by omega
      have hsihi : ¬s + i < 128 := by omega
      have hsub : (s + i) - 128 = s + j := by rw [hij]; omega
      rw [testBit_pack128 p q i hp, testBit_pack128 p q (s + i) hp]
      simp [h128, hi128, hsihi, j, hsub, hm]
    · have hmf : mask2.testBit j = false := by
        cases h : mask2.testBit j <;> simp_all
      simp [j, hmf]

theorem pack128_mul (p q k : Nat) :
    pack128 p q * k = pack128 (p * k) (q * k) := by
  unfold pack128
  rw [Nat.add_mul, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  congr 1
  calc
    (q * 2 ^ 128) * k = q * (2 ^ 128 * k) := Nat.mul_assoc _ _ _
    _ = q * (k * 2 ^ 128) := by rw [Nat.mul_comm (2 ^ 128) k]
    _ = (q * k) * 2 ^ 128 := (Nat.mul_assoc _ _ _).symm


/-! Complete four-lane mixer, derived from the verified 2-lane algebra. -/

theorem pack2_lt128 {a b : Nat} (ha : a < 2 ^ 64) (hb : b < 2 ^ 64) :
    pack2 a b < 2 ^ 128 := by
  unfold pack2
  rw [Nat.shiftLeft_eq]
  have ha' : a ≤ 2 ^ 64 - 1 := by omega
  have hb' : b ≤ 2 ^ 64 - 1 := by omega
  omega

theorem and_mask2_lt128 (x : Nat) :
    (x &&& mask2) < 2 ^ 128 := by
  have hle : (x &&& mask2) ≤ mask2 := Nat.and_le_right
  exact Nat.lt_of_le_of_lt hle mask2_lt128

theorem mask_pack128 (p q : Nat) (hp : p < 2 ^ 128) :
    (pack128 p q &&& mask4) =
      pack128 (p &&& mask2) (q &&& mask2) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask4]
  rw [testBit_pack128 (p &&& mask2) (q &&& mask2) i (and_mask2_lt128 p)]
  rw [testBit_pack128 p q i hp]
  simp only [Nat.testBit_and]
  by_cases h : i < 128
  · simp [h]
  · simp [h]

theorem pairY_eq (a b : Nat) (ha : a < 2 ^ 64) :
    (pairStage 16 (pack2 a b) * c1) &&& mask2 =
      pack2 (y32 a) (y32 b) := by
  simpa [pairStage] using packed_y32 a b ha

theorem pairY_mul_lt128 (a b : Nat) (ha : a < 2 ^ 64) (hb : b < 2 ^ 64) :
    pairStage 16 (pack2 a b) * c1 < 2 ^ 128 := by
  have hstage :
      pairStage 16 (pack2 a b) = pack2 (u32 a) (u32 b) := by
    simpa [pairStage] using packed_u32 a b ha
  rw [hstage, pack2_mul]
  exact pack2_lt128 (u32_mul_c1_lt64 a) (u32_mul_c1_lt64 b)

theorem packed_y4 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    ((((pack4 a b c d ^^^ (pack4 a b c d >>> 16)) &&& mask4) * c1) &&& mask4) =
      pack4 (y32 a) (y32 b) (y32 c) (y32 d) := by
  unfold pack4
  rw [lift_pair_stage (pack2 a b) (pack2 c d) 16 (pack2_lt128 ha hb) (by decide) (by decide)]
  rw [pack128_mul]
  rw [mask_pack128 _ _ (pairY_mul_lt128 a b ha hb)]
  rw [pairY_eq a b ha, pairY_eq c d hc]

theorem pairV_eq (a b : Nat) (ha : a < 2 ^ 64) :
    pairStage 15 (pack2 a b) =
      pack2 (v32 a) (v32 b) := by
  simpa [pairStage] using packed_v32 a b ha

theorem packed_v4 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    ((pack4 a b c d ^^^ (pack4 a b c d >>> 15)) &&& mask4) =
      pack4 (v32 a) (v32 b) (v32 c) (v32 d) := by
  unfold pack4
  rw [lift_pair_stage (pack2 a b) (pack2 c d) 15 (pack2_lt128 ha hb) (by decide) (by decide)]
  rw [pairV_eq a b ha, pairV_eq c d hc]

theorem packed_p4 (a b c d : Nat) :
    pack4 (v32 a) (v32 b) (v32 c) (v32 d) * c2 =
      pack4 (v32 a * c2) (v32 b * c2) (v32 c * c2) (v32 d * c2) := by
  unfold pack4
  rw [pack128_mul, pack2_mul, pack2_mul]

theorem bitAt_pack128_low (p q i : Nat) (hp : p < 2 ^ 128) (hi : i < 128) :
    ((pack128 p q >>> i) % 2) = ((p >>> i) % 2) := by
  have h := congrArg Bool.toNat (testBit_pack128 p q i hp)
  rw [if_pos hi] at h
  simpa [Nat.toNat_testBit, Nat.shiftRight_eq_div_pow] using h

theorem bitAt_pack128_high (p q i : Nat) (hp : p < 2 ^ 128) (hi : 128 ≤ i) :
    ((pack128 p q >>> i) % 2) = ((q >>> (i - 128)) % 2) := by
  have h := congrArg Bool.toNat (testBit_pack128 p q i hp)
  rw [if_neg (by omega : ¬i < 128)] at h
  simpa [Nat.toNat_testBit, Nat.shiftRight_eq_div_pow] using h

theorem bit31_pack4_0 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64) :
    ((pack4 a b c d >>> 31) % 2) = bit31Nat a := by
  unfold pack4
  rw [bitAt_pack128_low _ _ 31 (pack2_lt128 ha hb) (by decide)]
  exact bit31_pack2_low a b ha

theorem bit31_pack4_1 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64) :
    ((pack4 a b c d >>> 95) % 2) = bit31Nat b := by
  unfold pack4
  rw [bitAt_pack128_low _ _ 95 (pack2_lt128 ha hb) (by decide)]
  exact bit31_pack2_high a b ha

theorem bit31_pack4_2 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) :
    ((pack4 a b c d >>> 159) % 2) = bit31Nat c := by
  unfold pack4
  rw [bitAt_pack128_high _ _ 159 (pack2_lt128 ha hb) (by decide)]
  have h : 159 - 128 = 31 := by decide
  rw [h]
  exact bit31_pack2_low c d hc

theorem bit31_pack4_3 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) :
    ((pack4 a b c d >>> 223) % 2) = bit31Nat d := by
  unfold pack4
  rw [bitAt_pack128_high _ _ 223 (pack2_lt128 ha hb) (by decide)]
  have h : 223 - 128 = 95 := by decide
  rw [h]
  exact bit31_pack2_high c d hc

def mix4SWAR (a b c d : Nat) : Nat :=
  let p0 := pack4 a b c d
  let u := (p0 ^^^ (p0 >>> 16)) &&& mask4
  let y := (u * c1) &&& mask4
  let v := (y ^^^ (y >>> 15)) &&& mask4
  let p := v * c2
  (p >>> 31) % 2 +
  2 * ((p >>> 95) % 2) +
  4 * ((p >>> 159) % 2) +
  8 * ((p >>> 223) % 2)

theorem mix4SWAR_eq (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    mix4SWAR a b c d =
      mixScalarNat a + 2 * mixScalarNat b +
      4 * mixScalarNat c + 8 * mixScalarNat d := by
  simp only [mix4SWAR]
  rw [packed_y4 a b c d ha hb hc hd]
  rw [packed_v4 (y32 a) (y32 b) (y32 c) (y32 d)
      (y32_lt64 a) (y32_lt64 b) (y32_lt64 c) (y32_lt64 d)]
  rw [packed_p4]
  rw [bit31_pack4_0 _ _ _ _ (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))]
  rw [bit31_pack4_1 _ _ _ _ (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))]
  rw [bit31_pack4_2 _ _ _ _ (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))
      (v32_mul_c2_lt64 (y32 c))]
  rw [bit31_pack4_3 _ _ _ _ (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))
      (v32_mul_c2_lt64 (y32 c))]
  rfl


/-! Eight-lane lift: two proven 4-lane words separated by 256 bits. -/

def pack256 (p q : Nat) : Nat :=
  p + (q <<< 256)

def mask8 : Nat :=
  pack256 mask4 mask4

def pack8v (a b c d e f g h : Nat) : Nat :=
  pack256 (pack4 a b c d) (pack4 e f g h)

theorem mask4_lt256 : mask4 < 2 ^ 256 := by decide

theorem testBit_pack256 (p q i : Nat) (hp : p < 2 ^ 256) :
    (pack256 p q).testBit i =
      if i < 256 then p.testBit i else q.testBit (i - 256) := by
  unfold pack256
  rw [Nat.add_comm, Nat.shiftLeft_eq, Nat.mul_comm]
  exact Nat.testBit_two_pow_mul_add q hp i

theorem testBit_mask8 (i : Nat) :
    mask8.testBit i =
      if i < 256 then mask4.testBit i else mask4.testBit (i - 256) := by
  unfold mask8
  exact testBit_pack256 mask4 mask4 i mask4_lt256

def quadStage (s p : Nat) : Nat :=
  (p ^^^ (p >>> s)) &&& mask4

theorem quadStage_lt256 (s p : Nat) :
    quadStage s p < 2 ^ 256 := by
  unfold quadStage
  have hle : ((p ^^^ (p >>> s)) &&& mask4) ≤ mask4 := Nat.and_le_right
  exact Nat.lt_of_le_of_lt hle mask4_lt256

theorem mask4_true_lt224 {i : Nat} (hm : mask4.testBit i = true) :
    i < 224 := by
  rw [testBit_mask4] at hm
  by_cases h128 : i < 128
  · rw [if_pos h128] at hm
    rw [testBit_mask2] at hm
    simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq] at hm
    omega
  · rw [if_neg h128] at hm
    rw [testBit_mask2] at hm
    simp only [Bool.or_eq_true, Bool.and_eq_true, decide_eq_true_eq] at hm
    omega

theorem lift_quad_stage (p q s : Nat)
    (hp : p < 2 ^ 256) (hs0 : 0 < s) (hs : s ≤ 32) :
    ((pack256 p q ^^^ (pack256 p q >>> s)) &&& mask8) =
      pack256 (quadStage s p) (quadStage s q) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask8]
  rw [testBit_pack256 (quadStage s p) (quadStage s q) i (quadStage_lt256 s p)]
  simp only [quadStage, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight]
  by_cases h256 : i < 256
  · rw [if_pos h256, if_pos h256]
    by_cases hm : mask4.testBit i = true
    · have hi224 : i < 224 := mask4_true_lt224 hm
      have his : s + i < 256 := by omega
      rw [testBit_pack256 p q i hp, testBit_pack256 p q (s + i) hp]
      simp [h256, his, hm]
    · have hmf : mask4.testBit i = false := by
        cases h : mask4.testBit i <;> simp_all
      simp [hmf]
  · rw [if_neg h256, if_neg h256]
    have hi256 : 256 ≤ i := by omega
    let j := i - 256
    have hij : i = 256 + j := by dsimp [j]; omega
    by_cases hm : mask4.testBit j = true
    · have hj224 : j < 224 := mask4_true_lt224 hm
      have hsj : s + j < 256 := by omega
      have hsihi : ¬s + i < 256 := by omega
      have hsub : (s + i) - 256 = s + j := by rw [hij]; omega
      rw [testBit_pack256 p q i hp, testBit_pack256 p q (s + i) hp]
      simp [h256, hi256, hsihi, j, hsub, hm]
    · have hmf : mask4.testBit j = false := by
        cases h : mask4.testBit j <;> simp_all
      simp [j, hmf]

theorem pack256_mul (p q k : Nat) :
    pack256 p q * k = pack256 (p * k) (q * k) := by
  unfold pack256
  rw [Nat.add_mul, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  congr 1
  calc
    (q * 2 ^ 256) * k = q * (2 ^ 256 * k) := Nat.mul_assoc _ _ _
    _ = q * (k * 2 ^ 256) := by rw [Nat.mul_comm (2 ^ 256) k]
    _ = (q * k) * 2 ^ 256 := (Nat.mul_assoc _ _ _).symm

theorem pack128_lt256 {p q : Nat} (hp : p < 2 ^ 128) (hq : q < 2 ^ 128) :
    pack128 p q < 2 ^ 256 := by
  unfold pack128
  rw [Nat.shiftLeft_eq]
  have hp' : p ≤ 2 ^ 128 - 1 := by omega
  have hq' : q ≤ 2 ^ 128 - 1 := by omega
  have hm := Nat.mul_le_mul_right (2 ^ 128) hq'
  calc
    p + q * 2 ^ 128 ≤ (2 ^ 128 - 1) + (2 ^ 128 - 1) * 2 ^ 128 :=
      Nat.add_le_add hp' hm
    _ < 2 ^ 256 := by decide

theorem pack4_lt256 {a b c d : Nat}
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    pack4 a b c d < 2 ^ 256 := by
  unfold pack4
  exact pack128_lt256 (pack2_lt128 ha hb) (pack2_lt128 hc hd)

theorem and_mask4_lt256 (x : Nat) :
    (x &&& mask4) < 2 ^ 256 := by
  have hle : (x &&& mask4) ≤ mask4 := Nat.and_le_right
  exact Nat.lt_of_le_of_lt hle mask4_lt256

theorem mask_pack256 (p q : Nat) (hp : p < 2 ^ 256) :
    (pack256 p q &&& mask8) =
      pack256 (p &&& mask4) (q &&& mask4) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_mask8]
  rw [testBit_pack256 (p &&& mask4) (q &&& mask4) i (and_mask4_lt256 p)]
  rw [testBit_pack256 p q i hp]
  simp only [Nat.testBit_and]
  by_cases h : i < 256
  · simp [h]
  · simp [h]

theorem pack4_mul (a b c d k : Nat) :
    pack4 a b c d * k =
      pack4 (a * k) (b * k) (c * k) (d * k) := by
  unfold pack4
  rw [pack128_mul, pack2_mul, pack2_mul]

theorem quadU_eq (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    quadStage 16 (pack4 a b c d) =
      pack4 (u32 a) (u32 b) (u32 c) (u32 d) := by
  unfold quadStage pack4
  rw [lift_pair_stage (pack2 a b) (pack2 c d) 16 (pack2_lt128 ha hb) (by decide) (by decide)]
  have e0 :
      pairStage 16 (pack2 a b) = pack2 (u32 a) (u32 b) := by
    simpa [pairStage] using packed_u32 a b ha
  have e1 :
      pairStage 16 (pack2 c d) = pack2 (u32 c) (u32 d) := by
    simpa [pairStage] using packed_u32 c d hc
  rw [e0, e1]

theorem quadU_mul_c1_lt256 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    quadStage 16 (pack4 a b c d) * c1 < 2 ^ 256 := by
  rw [quadU_eq a b c d ha hb hc hd, pack4_mul]
  exact pack4_lt256
    (u32_mul_c1_lt64 a) (u32_mul_c1_lt64 b)
    (u32_mul_c1_lt64 c) (u32_mul_c1_lt64 d)

theorem quadY_eq (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    (quadStage 16 (pack4 a b c d) * c1) &&& mask4 =
      pack4 (y32 a) (y32 b) (y32 c) (y32 d) := by
  simpa [quadStage] using packed_y4 a b c d ha hb hc hd

theorem packed_y8 (a b c d e f g h : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64)
    (he : e < 2 ^ 64) (hf : f < 2 ^ 64)
    (hg : g < 2 ^ 64) (hh : h < 2 ^ 64) :
    ((((pack8v a b c d e f g h ^^^ (pack8v a b c d e f g h >>> 16)) &&& mask8) * c1) &&& mask8) =
      pack8v (y32 a) (y32 b) (y32 c) (y32 d)
        (y32 e) (y32 f) (y32 g) (y32 h) := by
  unfold pack8v
  rw [lift_quad_stage
        (pack4 a b c d) (pack4 e f g h) 16
        (pack4_lt256 ha hb hc hd) (by decide) (by decide)]
  rw [pack256_mul]
  rw [mask_pack256 _ _ (quadU_mul_c1_lt256 a b c d ha hb hc hd)]
  rw [quadY_eq a b c d ha hb hc hd, quadY_eq e f g h he hf hg hh]

theorem quadV_eq (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64) :
    quadStage 15 (pack4 a b c d) =
      pack4 (v32 a) (v32 b) (v32 c) (v32 d) := by
  simpa [quadStage] using packed_v4 a b c d ha hb hc hd

theorem packed_v8 (a b c d e f g h : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64)
    (he : e < 2 ^ 64) (hf : f < 2 ^ 64)
    (hg : g < 2 ^ 64) (hh : h < 2 ^ 64) :
    ((pack8v a b c d e f g h ^^^ (pack8v a b c d e f g h >>> 15)) &&& mask8) =
      pack8v (v32 a) (v32 b) (v32 c) (v32 d)
        (v32 e) (v32 f) (v32 g) (v32 h) := by
  unfold pack8v
  rw [lift_quad_stage
        (pack4 a b c d) (pack4 e f g h) 15
        (pack4_lt256 ha hb hc hd) (by decide) (by decide)]
  rw [quadV_eq a b c d ha hb hc hd, quadV_eq e f g h he hf hg hh]

theorem packed_p8 (a b c d e f g h : Nat) :
    pack8v (v32 a) (v32 b) (v32 c) (v32 d)
        (v32 e) (v32 f) (v32 g) (v32 h) * c2 =
      pack8v (v32 a * c2) (v32 b * c2) (v32 c * c2) (v32 d * c2)
        (v32 e * c2) (v32 f * c2) (v32 g * c2) (v32 h * c2) := by
  unfold pack8v
  rw [pack256_mul, pack4_mul, pack4_mul]

theorem bitAt_pack256_low (p q i : Nat) (hp : p < 2 ^ 256) (hi : i < 256) :
    ((pack256 p q >>> i) % 2) = ((p >>> i) % 2) := by
  have h := congrArg Bool.toNat (testBit_pack256 p q i hp)
  rw [if_pos hi] at h
  simpa [Nat.toNat_testBit, Nat.shiftRight_eq_div_pow] using h

theorem bitAt_pack256_high (p q i : Nat) (hp : p < 2 ^ 256) (hi : 256 ≤ i) :
    ((pack256 p q >>> i) % 2) = ((q >>> (i - 256)) % 2) := by
  have h := congrArg Bool.toNat (testBit_pack256 p q i hp)
  rw [if_neg (by omega : ¬i < 256)] at h
  simpa [Nat.toNat_testBit, Nat.shiftRight_eq_div_pow] using h

def mix8SWAR (a b c d e f g h : Nat) : Nat :=
  let p0 := pack8v a b c d e f g h
  let u := (p0 ^^^ (p0 >>> 16)) &&& mask8
  let y := (u * c1) &&& mask8
  let v := (y ^^^ (y >>> 15)) &&& mask8
  let p := v * c2
  (p >>> 31) % 2 +
  2 * ((p >>> 95) % 2) +
  4 * ((p >>> 159) % 2) +
  8 * ((p >>> 223) % 2) +
  16 * ((p >>> 287) % 2) +
  32 * ((p >>> 351) % 2) +
  64 * ((p >>> 415) % 2) +
  128 * ((p >>> 479) % 2)

theorem mix8SWAR_eq (a b c d e f g h : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (hd : d < 2 ^ 64)
    (he : e < 2 ^ 64) (hf : f < 2 ^ 64)
    (hg : g < 2 ^ 64) (hh : h < 2 ^ 64) :
    mix8SWAR a b c d e f g h =
      mixScalarNat a + 2 * mixScalarNat b +
      4 * mixScalarNat c + 8 * mixScalarNat d +
      16 * mixScalarNat e + 32 * mixScalarNat f +
      64 * mixScalarNat g + 128 * mixScalarNat h := by
  simp only [mix8SWAR]
  rw [packed_y8 a b c d e f g h ha hb hc hd he hf hg hh]
  rw [packed_v8
        (y32 a) (y32 b) (y32 c) (y32 d)
        (y32 e) (y32 f) (y32 g) (y32 h)
        (y32_lt64 a) (y32_lt64 b) (y32_lt64 c) (y32_lt64 d)
        (y32_lt64 e) (y32_lt64 f) (y32_lt64 g) (y32_lt64 h)]
  rw [packed_p8]
  let p := pack4
      (v32 (y32 a) * c2) (v32 (y32 b) * c2)
      (v32 (y32 c) * c2) (v32 (y32 d) * c2)
  let q := pack4
      (v32 (y32 e) * c2) (v32 (y32 f) * c2)
      (v32 (y32 g) * c2) (v32 (y32 h) * c2)
  have hp : p < 2 ^ 256 := by
    dsimp [p]
    exact pack4_lt256
      (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))
      (v32_mul_c2_lt64 (y32 c)) (v32_mul_c2_lt64 (y32 d))
  change
    ((pack256 p q >>> 31) % 2) +
      2 * ((pack256 p q >>> 95) % 2) +
      4 * ((pack256 p q >>> 159) % 2) +
      8 * ((pack256 p q >>> 223) % 2) +
      16 * ((pack256 p q >>> 287) % 2) +
      32 * ((pack256 p q >>> 351) % 2) +
      64 * ((pack256 p q >>> 415) % 2) +
      128 * ((pack256 p q >>> 479) % 2) =
    mixScalarNat a + 2 * mixScalarNat b +
      4 * mixScalarNat c + 8 * mixScalarNat d +
      16 * mixScalarNat e + 32 * mixScalarNat f +
      64 * mixScalarNat g + 128 * mixScalarNat h
  rw [bitAt_pack256_low p q 31 hp (by decide)]
  rw [bitAt_pack256_low p q 95 hp (by decide)]
  rw [bitAt_pack256_low p q 159 hp (by decide)]
  rw [bitAt_pack256_low p q 223 hp (by decide)]
  rw [bitAt_pack256_high p q 287 hp (by decide)]
  rw [bitAt_pack256_high p q 351 hp (by decide)]
  rw [bitAt_pack256_high p q 415 hp (by decide)]
  rw [bitAt_pack256_high p q 479 hp (by decide)]
  have h287 : 287 - 256 = 31 := by decide
  have h351 : 351 - 256 = 95 := by decide
  have h415 : 415 - 256 = 159 := by decide
  have h479 : 479 - 256 = 223 := by decide
  rw [h287, h351, h415, h479]
  dsimp [p, q]
  rw [bit31_pack4_0 _ _ _ _
      (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))]
  rw [bit31_pack4_1 _ _ _ _
      (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))]
  rw [bit31_pack4_2 _ _ _ _
      (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))
      (v32_mul_c2_lt64 (y32 c))]
  rw [bit31_pack4_3 _ _ _ _
      (v32_mul_c2_lt64 (y32 a)) (v32_mul_c2_lt64 (y32 b))
      (v32_mul_c2_lt64 (y32 c))]
  rw [bit31_pack4_0 _ _ _ _
      (v32_mul_c2_lt64 (y32 e)) (v32_mul_c2_lt64 (y32 f))]
  rw [bit31_pack4_1 _ _ _ _
      (v32_mul_c2_lt64 (y32 e)) (v32_mul_c2_lt64 (y32 f))]
  rw [bit31_pack4_2 _ _ _ _
      (v32_mul_c2_lt64 (y32 e)) (v32_mul_c2_lt64 (y32 f))
      (v32_mul_c2_lt64 (y32 g))]
  rw [bit31_pack4_3 _ _ _ _
      (v32_mul_c2_lt64 (y32 e)) (v32_mul_c2_lt64 (y32 f))
      (v32_mul_c2_lt64 (y32 g))]
  rfl

end SWAR
