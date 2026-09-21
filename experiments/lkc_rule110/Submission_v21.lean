import Spec

/-!
Rule 110 Stage-1 experiment.

Baseline representation follows the official verified bit-packed example.
The only semantic change is a scored-path dispatcher: public scored step counts
2, 4, and 8 are reduced by straight-line bstep chains instead of the generic
recursive iterator. All other Nat inputs use the generic iterator, and
biterFast_eq proves the dispatcher universally equivalent.
-/

namespace Submission

theorem testBit_encodeRow (row : List Bool) (i : Nat) :
    (encodeRow row).testBit i = row.getD i false := by
  induction row generalizing i with
  | nil => simp [encodeRow]
  | cons b bs ih =>
    have hrec : encodeRow (b :: bs) = 2 * encodeRow bs + (if b then 1 else 0) := rfl
    cases i with
    | zero => rw [hrec]; cases b <;> simp [Nat.testBit_zero] <;> omega
    | succ j =>
      rw [hrec, Nat.testBit_succ]
      have : (2 * encodeRow bs + (if b then 1 else 0)) / 2 = encodeRow bs := by
        cases b <;> simp <;> omega
      rw [this, ih]; rfl

theorem encodeRow_lt (row : List Bool) : encodeRow row < 2 ^ row.length := by
  induction row with
  | nil => simp [encodeRow]
  | cons b bs ih =>
    have hrec : encodeRow (b :: bs) = 2 * encodeRow bs + (if b then 1 else 0) := rfl
    rw [hrec, List.length_cons, Nat.pow_succ]; split <;> omega

@[simp] theorem length_stepRow (row : List Bool) : (stepRow row).length = row.length := by
  simp [stepRow]

theorem getD_stepRow (row : List Bool) (i : Nat) :
    (stepRow row).getD i false =
      if i < row.length then
        rule110 (row.getD ((i + row.length - 1) % row.length) false)
                (row.getD i false) (row.getD ((i + 1) % row.length) false)
      else false := by
  by_cases h : i < row.length
  · rw [List.getD_eq_getElem?_getD]; simp [stepRow, h]
  · have hlen : (stepRow row).length ≤ i := by rw [length_stepRow]; omega
    rw [List.getD_eq_getElem?_getD, List.getElem?_eq_none hlen, Option.getD_none, if_neg h]

def M : Nat := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff
theorem M_eq : M = 2 ^ 256 - 1 := by decide
theorem testBit_M (i : Nat) : M.testBit i = decide (i < 256) := by
  rw [M_eq, Nat.testBit_two_pow_sub_one]
theorem testBit_high {m : Nat} (hm : m < 2 ^ 256) {j : Nat} (hj : 256 ≤ j) : m.testBit j = false := by
  have hlt : m < 2 ^ j := Nat.lt_of_lt_of_le hm (Nat.pow_le_pow_right (by omega) hj)
  simp [Nat.testBit, Nat.shiftRight_eq_div_pow, Nat.div_eq_of_lt hlt]

theorem testBit_rotL {m : Nat} (hm : m < 2 ^ 256) {i : Nat} (hi : i < 256) :
    (((m <<< 1) ||| (m >>> 255)) &&& M).testBit i = m.testBit ((i + 255) % 256) := by
  rw [Nat.testBit_and, Nat.testBit_or, Nat.testBit_shiftLeft, Nat.testBit_shiftRight, testBit_M]
  simp only [hi, decide_true, Bool.and_true]
  rcases Nat.eq_zero_or_pos i with hi0 | hipos
  · subst hi0; simp
  · have h1 : (1 ≤ i) := hipos
    have hmod : (i + 255) % 256 = i - 1 := by omega
    have hhi : m.testBit (255 + i) = false := testBit_high hm (by omega)
    simp [h1, hmod, hhi]

theorem testBit_rotR {m : Nat} (hm : m < 2 ^ 256) {i : Nat} (hi : i < 256) :
    (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M).testBit i = m.testBit ((i + 1) % 256) := by
  rw [Nat.testBit_and, Nat.testBit_or, Nat.testBit_shiftRight, Nat.testBit_shiftLeft, testBit_M]
  simp only [hi, decide_true, Bool.and_true]
  by_cases h255 : i = 255
  · subst h255
    have hmod : (255 + 1) % 256 = 0 := by decide
    have hhi : m.testBit (1 + 255) = false := testBit_high hm (by omega)
    rw [hmod]; simp [hhi]
  · have hmod : (i + 1) % 256 = i + 1 := by omega
    have hnot : ¬ (255 ≤ i) := by omega
    simp [hmod, hnot, Nat.add_comm 1 i]

def bstep (m : Nat) : Nat :=
  (M ^^^ (((M ^^^ m) &&& (M ^^^ (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)))
          ||| ((((m <<< 1) ||| (m >>> 255)) &&& M) &&& m &&& (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)))) &&& M

def biter : Nat → Nat → Nat
  | 0, m => m
  | t + 1, m => biter t (bstep m)

/-- Public scored paths: eliminate iterator pattern matching/recursion overhead. -/
def biterFast (t m : Nat) : Nat :=
  if t = 2 then
    bstep (bstep m)
  else if t = 4 then
    bstep (bstep (bstep (bstep m)))
  else if t = 8 then
    bstep (bstep (bstep (bstep (bstep (bstep (bstep (bstep m)))))))
  else
    biter t m

theorem biterFast_eq (t m : Nat) : biterFast t m = biter t m := by
  unfold biterFast
  by_cases h2 : t = 2
  · rw [if_pos h2]
    subst t
    rfl
  · rw [if_neg h2]
    by_cases h4 : t = 4
    · rw [if_pos h4]
      subst t
      rfl
    · rw [if_neg h4]
      by_cases h8 : t = 8
      · rw [if_pos h8]
        subst t
        rfl
      · rw [if_neg h8]

/-! Verified list-free initializer candidate. -/

def initCell (seed i : Nat) : Bool :=
  if i = 0 then true
  else if i = 1 then false
  else (caMix32 (seed + (i + 1) * 0x9e3779b9)).testBit 31

def packFrom (seed : Nat) : Nat → Nat → Nat
  | _, 0 => 0
  | start, k + 1 =>
      (if initCell seed start then 1 else 0) +
      2 * packFrom seed (start + 1) k

def initPacked (seed : Nat) : Nat := packFrom seed 0 256

theorem testBit_packFrom (seed start k i : Nat) :
    (packFrom seed start k).testBit i =
      if i < k then initCell seed (start + i) else false := by
  induction k generalizing start i with
  | zero =>
      simp [packFrom]
  | succ k ih =>
      cases i with
      | zero =>
          unfold packFrom
          cases h : initCell seed start <;> simp [Nat.testBit_zero]
      | succ i =>
          unfold packFrom
          rw [Nat.testBit_succ]
          have hdiv :
              ((if initCell seed start then 1 else 0) +
                2 * packFrom seed (start + 1) k) / 2 =
                packFrom seed (start + 1) k := by
            cases h : initCell seed start <;> simp <;> omega
          rw [hdiv, ih]
          simp only [Nat.succ_lt_succ_iff]
          congr 2 <;> omega

theorem getD_initRowFor (seed i : Nat) :
    (initRowFor seed).getD i false =
      if i < 256 then initCell seed i else false := by
  by_cases hi : i < 256
  · rw [if_pos hi]
    simp [initRowFor, ruleWidth, initCell, hi]
  · rw [if_neg hi]
    have hlen : (initRowFor seed).length ≤ i := by
      simp [initRowFor, ruleWidth]
      omega
    rw [List.getD_eq_getElem?_getD, List.getElem?_eq_none hlen, Option.getD_none]

theorem initPacked_eq (seed : Nat) :
    initPacked seed = encodeRow (initRowFor seed) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_encodeRow, getD_initRowFor]
  unfold initPacked
  rw [testBit_packFrom]
  simp

def stepConst : Nat := 0x9e3779b9

def mixCell (x : Nat) : Bool :=
  (caMix32 x).testBit 31

def packMix : Nat → Nat → Nat
  | _, 0 => 0
  | x, k + 1 =>
      (if mixCell x then 1 else 0) +
      2 * packMix (x + stepConst) k

theorem initCell_eq_mixCell (seed start : Nat) (hs : 2 ≤ start) :
    initCell seed start =
      mixCell (seed + (start + 1) * stepConst) := by
  unfold initCell mixCell stepConst
  rw [if_neg (by omega), if_neg (by omega)]

theorem packMix_eq_packFrom (seed start k : Nat) (hs : 2 ≤ start) :
    packMix (seed + (start + 1) * stepConst) k =
      packFrom seed start k := by
  induction k generalizing start with
  | zero =>
      rfl
  | succ k ih =>
      unfold packMix packFrom
      rw [initCell_eq_mixCell seed start hs]
      congr 1
      have hx :
          (seed + (start + 1) * stepConst) + stepConst =
            seed + ((start + 1) + 1) * stepConst := by
        unfold stepConst
        omega
      rw [hx]
      exact congrArg (fun z => 2 * z) (ih (start + 1) (by omega))

theorem initPacked_decomp (seed : Nat) :
    initPacked seed = 1 + 4 * packFrom seed 2 254 := by
  unfold initPacked
  change
    (if initCell seed 0 then 1 else 0) +
      2 * ((if initCell seed 1 then 1 else 0) +
        2 * packFrom seed 2 254) =
      1 + 4 * packFrom seed 2 254
  simp [initCell]
  omega

def initPackedFast (seed : Nat) : Nat :=
  1 + 4 * packMix (seed + 3 * stepConst) 254

theorem initPackedFast_eq_initPacked (seed : Nat) :
    initPackedFast seed = initPacked seed := by
  rw [initPacked_decomp]
  unfold initPackedFast
  have h := packMix_eq_packFrom seed 2 254 (by omega)
  change
    1 + 4 * packMix (seed + (2 + 1) * stepConst) 254 =
      1 + 4 * packFrom seed 2 254
  exact congrArg (fun z => 1 + 4 * z) h

theorem initPackedFast_eq (seed : Nat) :
    initPackedFast seed = encodeRow (initRowFor seed) := by
  rw [initPackedFast_eq_initPacked, initPacked_eq]


/-!
V6 composition: retain V4 arithmetic-progression reuse and compile the mixer
down to the only observable needed by the initializer: output bit 31.
-/

def mixBit31 (x : Nat) : Bool :=
  let y := ((x ^^^ (x >>> 16)) * 0x7feb352d) &&& 0xffffffff
  ((y ^^^ (y >>> 15)) * 0x846ca68b).testBit 31

theorem mixBit31_eq (x : Nat) :
    mixBit31 x = (caMix32 x).testBit 31 := by
  unfold mixBit31 caMix32
  have h31 : (0xffffffff : Nat).testBit 31 = true := by decide
  have h47 : (0xffffffff : Nat).testBit 47 = false := by decide
  simp only [Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight]
  simp [h31, h47]

def packMixBit : Nat → Nat → Nat
  | _, 0 => 0
  | x, k + 1 =>
      (if mixBit31 x then 1 else 0) +
      2 * packMixBit (x + stepConst) k

theorem packMixBit_eq_packMix (x k : Nat) :
    packMixBit x k = packMix x k := by
  induction k generalizing x with
  | zero => rfl
  | succ k ih =>
      unfold packMixBit packMix
      rw [mixBit31_eq, ih]
      rfl

def initPackedFastBit (seed : Nat) : Nat :=
  1 + 4 * packMixBit (seed + 3 * stepConst) 254

theorem initPackedFastBit_eq (seed : Nat) :
    initPackedFastBit seed = initPackedFast seed := by
  unfold initPackedFastBit initPackedFast
  rw [packMixBit_eq_packMix]

/-! V8: byte-grained initializer packing. -/

def advance8 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  x7 + stepConst

def pack8 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  (if mixBit31 x  then 1 else 0) +
  2   * (if mixBit31 x1 then 1 else 0) +
  4   * (if mixBit31 x2 then 1 else 0) +
  8   * (if mixBit31 x3 then 1 else 0) +
  16  * (if mixBit31 x4 then 1 else 0) +
  32  * (if mixBit31 x5 then 1 else 0) +
  64  * (if mixBit31 x6 then 1 else 0) +
  128 * (if mixBit31 x7 then 1 else 0)

def pack6 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  (if mixBit31 x  then 1 else 0) +
  2  * (if mixBit31 x1 then 1 else 0) +
  4  * (if mixBit31 x2 then 1 else 0) +
  8  * (if mixBit31 x3 then 1 else 0) +
  16 * (if mixBit31 x4 then 1 else 0) +
  32 * (if mixBit31 x5 then 1 else 0)

def packByteTail : Nat → Nat → Nat
  | x, 0 => pack6 x
  | x, n + 1 => pack8 x + 256 * packByteTail (advance8 x) n

theorem packMixBit_six (x : Nat) :
    packMixBit x 6 = pack6 x := by
  unfold pack6
  simp only [packMixBit]
  omega

theorem packMixBit_eight (x k : Nat) :
    packMixBit x (k + 8) =
      pack8 x + 256 * packMixBit (advance8 x) k := by
  unfold pack8 advance8
  simp only [packMixBit]
  omega

theorem packByteTail_eq (x n : Nat) :
    packByteTail x n = packMixBit x (8 * n + 6) := by
  induction n generalizing x with
  | zero =>
      simp only [packByteTail, Nat.mul_zero, Nat.zero_add]
      exact (packMixBit_six x).symm
  | succ n ih =>
      unfold packByteTail
      rw [ih (advance8 x)]
      have hn : 8 * (n + 1) + 6 = (8 * n + 6) + 8 := by omega
      rw [hn]
      exact (packMixBit_eight x (8 * n + 6)).symm

def initPackedByte (seed : Nat) : Nat :=
  1 + 4 * packByteTail (seed + 3 * stepConst) 31

theorem initPackedByte_eq (seed : Nat) :
    initPackedByte seed = initPackedFastBit seed := by
  unfold initPackedByte initPackedFastBit
  rw [packByteTail_eq]

/-! V15: numeric bit extraction via mod 2. -/

def mixBit31Nat (x : Nat) : Nat :=
  let y := ((x ^^^ (x >>> 16)) * 0x7feb352d) &&& 0xffffffff
  (((y ^^^ (y >>> 15)) * 0x846ca68b) >>> 31) % 2

theorem boolToNat_eq_if (b : Bool) :
    b.toNat = if b then 1 else 0 := by
  cases b <;> rfl

theorem mixBit31Nat_eq (x : Nat) :
    mixBit31Nat x = (mixBit31 x).toNat := by
  unfold mixBit31Nat mixBit31
  rw [Nat.toNat_testBit]
  simp [Nat.shiftRight_eq_div_pow]


namespace Vec2

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

end Vec2

namespace Vec4

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

theorem pairY_mul_lt128 (a b : Nat) (ha : a < 2 ^ 64) (_hb : b < 2 ^ 64) :
    pairStage 16 (pack2 a b) * c1 < 2 ^ 128 := by
  have hstage :
      pairStage 16 (pack2 a b) = pack2 (u32 a) (u32 b) := by
    simpa [pairStage] using packed_u32 a b ha
  rw [hstage, pack2_mul]
  exact pack2_lt128 (u32_mul_c1_lt64 a) (u32_mul_c1_lt64 b)

theorem packed_y4 (a b c d : Nat)
    (ha : a < 2 ^ 64) (hb : b < 2 ^ 64)
    (hc : c < 2 ^ 64) (_hd : d < 2 ^ 64) :
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
    (hc : c < 2 ^ 64) (_hd : d < 2 ^ 64) :
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

end Vec4


theorem vecScalar_eq (x : Nat) :
    Vec2.scalarRef x = mixBit31Nat x := by
  unfold Vec2.scalarRef Vec2.c1 Vec2.c2 Vec2.mask32 mixBit31Nat
  rfl

def pack8Nat (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  mixBit31Nat x +
  2   * mixBit31Nat x1 +
  4   * mixBit31Nat x2 +
  8   * mixBit31Nat x3 +
  16  * mixBit31Nat x4 +
  32  * mixBit31Nat x5 +
  64  * mixBit31Nat x6 +
  128 * mixBit31Nat x7

def pack6Nat (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  mixBit31Nat x +
  2  * mixBit31Nat x1 +
  4  * mixBit31Nat x2 +
  8  * mixBit31Nat x3 +
  16 * mixBit31Nat x4 +
  32 * mixBit31Nat x5

theorem pack8Nat_eq (x : Nat) :
    pack8Nat x = pack8 x := by
  unfold pack8Nat pack8
  simp only [mixBit31Nat_eq, boolToNat_eq_if]

theorem pack6Nat_eq (x : Nat) :
    pack6Nat x = pack6 x := by
  unfold pack6Nat pack6
  simp only [mixBit31Nat_eq, boolToNat_eq_if]

def packByteTailNat : Nat → Nat → Nat
  | x, 0 => pack6Nat x
  | x, n + 1 => pack8Nat x + 256 * packByteTailNat (advance8 x) n

theorem packByteTailNat_eq (x n : Nat) :
    packByteTailNat x n = packByteTail x n := by
  induction n generalizing x with
  | zero =>
      unfold packByteTailNat packByteTail
      exact pack6Nat_eq x
  | succ n ih =>
      unfold packByteTailNat packByteTail
      rw [pack8Nat_eq, ih]

def initPackedByteNat (seed : Nat) : Nat :=
  1 + 4 * packByteTailNat (seed + 3 * stepConst) 31

theorem initPackedByteNat_eq (seed : Nat) :
    initPackedByteNat seed = initPackedByte seed := by
  unfold initPackedByteNat initPackedByte
  rw [packByteTailNat_eq]

/-! V20: true two-lane SWAR mixer composed onto V15. -/

def pack8SWAR (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  Vec2.mixPairSWAR x x1 +
  4  * Vec2.mixPairSWAR x2 x3 +
  16 * Vec2.mixPairSWAR x4 x5 +
  64 * Vec2.mixPairSWAR x6 x7

def pack6SWAR (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  Vec2.mixPairSWAR x x1 +
  4  * Vec2.mixPairSWAR x2 x3 +
  16 * Vec2.mixPairSWAR x4 x5

theorem pack8SWAR_eq (x : Nat) (h : x + 7 * stepConst < 2 ^ 64) :
    pack8SWAR x = pack8Nat x := by
  have h0 : x < 2 ^ 64 := by omega
  have h2 : x + stepConst + stepConst < 2 ^ 64 := by omega
  have h4 : x + stepConst + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  have h6 :
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst <
        2 ^ 64 := by omega
  dsimp [pack8SWAR, pack8Nat]
  rw [Vec2.mixPairSWAR_eq x (x + stepConst) h0]
  rw [Vec2.mixPairSWAR_eq
        (x + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst) h2]
  rw [Vec2.mixPairSWAR_eq
        (x + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst) h4]
  rw [Vec2.mixPairSWAR_eq
        (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)
        h6]
  simp only [Vec2.mixScalarNat_eq_ref, vecScalar_eq]
  omega

theorem pack6SWAR_eq (x : Nat) (h : x + 5 * stepConst < 2 ^ 64) :
    pack6SWAR x = pack6Nat x := by
  have h0 : x < 2 ^ 64 := by omega
  have h2 : x + stepConst + stepConst < 2 ^ 64 := by omega
  have h4 : x + stepConst + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  dsimp [pack6SWAR, pack6Nat]
  rw [Vec2.mixPairSWAR_eq x (x + stepConst) h0]
  rw [Vec2.mixPairSWAR_eq
        (x + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst) h2]
  rw [Vec2.mixPairSWAR_eq
        (x + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst) h4]
  simp only [Vec2.mixScalarNat_eq_ref, vecScalar_eq]
  omega

def packByteTailSWAR : Nat → Nat → Nat
  | x, 0 => pack6SWAR x
  | x, n + 1 => pack8SWAR x + 256 * packByteTailSWAR (advance8 x) n

theorem advance8_eq_swar (x : Nat) :
    advance8 x = x + 8 * stepConst := by
  simp only [advance8]
  omega

set_option maxRecDepth 32768 in
theorem packByteTailSWAR_eq (x n : Nat)
    (h : x + (8 * n + 5) * stepConst < 2 ^ 64) :
    packByteTailSWAR x n = packByteTailNat x n := by
  induction n generalizing x with
  | zero =>
      simp only [packByteTailSWAR, packByteTailNat, Nat.mul_zero, Nat.zero_add] at *
      exact pack6SWAR_eq x h
  | succ n ih =>
      simp only [packByteTailSWAR, packByteTailNat]
      have hk : 7 ≤ 8 * (n + 1) + 5 := by omega
      have hm : 7 * stepConst ≤ (8 * (n + 1) + 5) * stepConst :=
        Nat.mul_le_mul_right stepConst hk
      have hb : x + 7 * stepConst < 2 ^ 64 :=
        Nat.lt_of_le_of_lt (Nat.add_le_add_left hm x) h
      rw [pack8SWAR_eq x hb]
      have heq :
          advance8 x + (8 * n + 5) * stepConst =
            x + (8 * (n + 1) + 5) * stepConst := by
        rw [advance8_eq_swar, Nat.add_assoc, ← Nat.add_mul]
        have hcoef : 8 + (8 * n + 5) = 8 * (n + 1) + 5 := by omega
        rw [hcoef]
      have hr :
          advance8 x + (8 * n + 5) * stepConst < 2 ^ 64 := by
        rw [heq]
        exact h
      rw [ih (advance8 x) hr]

def initPackedSWAR (seed : Nat) : Nat :=
  1 + 4 * packByteTailSWAR (seed + 3 * stepConst) 31

theorem initPackedSWAR_eq (n : Nat) :
    initPackedSWAR (caSeed n) = initPackedByteNat (caSeed n) := by
  unfold initPackedSWAR initPackedByteNat
  rw [packByteTailSWAR_eq]
  have hs : caSeed n < 2 ^ 32 := by
    unfold caSeed
    exact Nat.and_lt_two_pow n (by decide)
  have hc : (2 ^ 32 - 1) + 256 * stepConst < 2 ^ 64 := by
    unfold stepConst
    decide
  unfold stepConst at *
  omega

/-! V21: verified four-lane SWAR, composed from the independently checked Vec4 lift. -/

theorem vec4Scalar_eq (x : Nat) :
    Vec4.scalarRef x = mixBit31Nat x := by
  unfold Vec4.scalarRef Vec4.c1 Vec4.c2 Vec4.mask32 mixBit31Nat
  rfl

def pack8SWAR4 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  Vec4.mix4SWAR x x1 x2 x3 +
    16 * Vec4.mix4SWAR x4 x5 x6 x7

def pack6SWAR4 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  Vec4.mix4SWAR x x1 x2 x3 +
    16 * Vec2.mixPairSWAR x4 x5

theorem pack8SWAR4_eq (x : Nat) (h : x + 7 * stepConst < 2 ^ 64) :
    pack8SWAR4 x = pack8Nat x := by
  have h0 : x < 2 ^ 64 := by omega
  have h1 : x + stepConst < 2 ^ 64 := by omega
  have h2 : x + stepConst + stepConst < 2 ^ 64 := by omega
  have h3 : x + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  have h4 : x + stepConst + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  have h5 : x + stepConst + stepConst + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  have h6 :
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst <
        2 ^ 64 := by omega
  have h7 :
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst <
        2 ^ 64 := by omega
  dsimp [pack8SWAR4, pack8Nat]
  rw [Vec4.mix4SWAR_eq
        x (x + stepConst)
        (x + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst) h0 h1 h2 h3]
  rw [Vec4.mix4SWAR_eq
        (x + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)
        h4 h5 h6 h7]
  simp only [Vec4.mixScalarNat_eq_ref, vec4Scalar_eq]
  omega

theorem pack6SWAR4_eq (x : Nat) (h : x + 5 * stepConst < 2 ^ 64) :
    pack6SWAR4 x = pack6Nat x := by
  have h0 : x < 2 ^ 64 := by omega
  have h1 : x + stepConst < 2 ^ 64 := by omega
  have h2 : x + stepConst + stepConst < 2 ^ 64 := by omega
  have h3 : x + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  have h4 : x + stepConst + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  dsimp [pack6SWAR4, pack6Nat]
  rw [Vec4.mix4SWAR_eq
        x (x + stepConst)
        (x + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst) h0 h1 h2 h3]
  rw [Vec2.mixPairSWAR_eq
        (x + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst) h4]
  simp only [Vec4.mixScalarNat_eq_ref, vec4Scalar_eq,
             Vec2.mixScalarNat_eq_ref, vecScalar_eq]
  omega

def packByteTailSWAR4 : Nat → Nat → Nat
  | x, 0 => pack6SWAR4 x
  | x, n + 1 => pack8SWAR4 x + 256 * packByteTailSWAR4 (advance8 x) n

set_option maxRecDepth 32768 in
theorem packByteTailSWAR4_eq (x n : Nat)
    (h : x + (8 * n + 5) * stepConst < 2 ^ 64) :
    packByteTailSWAR4 x n = packByteTailNat x n := by
  induction n generalizing x with
  | zero =>
      simp only [packByteTailSWAR4, packByteTailNat, Nat.mul_zero, Nat.zero_add] at *
      exact pack6SWAR4_eq x h
  | succ n ih =>
      simp only [packByteTailSWAR4, packByteTailNat]
      have hk : 7 ≤ 8 * (n + 1) + 5 := by omega
      have hm : 7 * stepConst ≤ (8 * (n + 1) + 5) * stepConst :=
        Nat.mul_le_mul_right stepConst hk
      have hb : x + 7 * stepConst < 2 ^ 64 :=
        Nat.lt_of_le_of_lt (Nat.add_le_add_left hm x) h
      rw [pack8SWAR4_eq x hb]
      have heq :
          advance8 x + (8 * n + 5) * stepConst =
            x + (8 * (n + 1) + 5) * stepConst := by
        rw [advance8_eq_swar, Nat.add_assoc, ← Nat.add_mul]
        have hcoef : 8 + (8 * n + 5) = 8 * (n + 1) + 5 := by omega
        rw [hcoef]
      have hr :
          advance8 x + (8 * n + 5) * stepConst < 2 ^ 64 := by
        rw [heq]
        exact h
      rw [ih (advance8 x) hr]

def initPackedSWAR4 (seed : Nat) : Nat :=
  1 + 4 * packByteTailSWAR4 (seed + 3 * stepConst) 31

theorem initPackedSWAR4_eq (n : Nat) :
    initPackedSWAR4 (caSeed n) = initPackedByteNat (caSeed n) := by
  unfold initPackedSWAR4 initPackedByteNat
  rw [packByteTailSWAR4_eq]
  have hs : caSeed n < 2 ^ 32 := by
    unfold caSeed
    exact Nat.and_lt_two_pow n (by decide)
  have hc : (2 ^ 32 - 1) + 256 * stepConst < 2 ^ 64 := by
    unfold stepConst
    decide
  unfold stepConst at *
  omega

def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (initPackedSWAR4 (caSeed n))

theorem step_eq {row : List Bool} (hlen : row.length = 256) :
    encodeRow (stepRow row) = bstep (encodeRow row) := by
  have hm : encodeRow row < 2 ^ 256 := hlen ▸ encodeRow_lt row
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_encodeRow, getD_stepRow, hlen]
  by_cases hi : i < 256
  · rw [if_pos hi]
    have he : i + 256 - 1 = i + 255 := by omega
    rw [he]
    simp only [bstep, Nat.testBit_and, Nat.testBit_xor, Nat.testBit_or, testBit_M,
               testBit_rotL hm hi, testBit_rotR hm hi, testBit_encodeRow, hi, decide_true]
    generalize row.getD ((i + 255) % 256) false = a
    generalize row.getD i false = b
    generalize row.getD ((i + 1) % 256) false = c
    cases a <;> cases b <;> cases c <;> decide
  · rw [if_neg hi]
    unfold bstep
    rw [Nat.testBit_and, testBit_M, decide_eq_false hi, Bool.and_false]

theorem iter_eq : ∀ (n : Nat) (row : List Bool), row.length = 256 →
    encodeRow (iterRow n row) = biter n (encodeRow row) := by
  intro n
  induction n with
  | zero => intro row _; rfl
  | succ k ih =>
    intro row hlen
    show encodeRow (iterRow k (stepRow row)) = biter k (bstep (encodeRow row))
    rw [ih (stepRow row) (by rw [length_stepRow, hlen]), step_eq hlen]

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFast_eq, initPackedSWAR4_eq, initPackedByteNat_eq, initPackedByte_eq, initPackedFastBit_eq, initPackedFast_eq]
  show biter (caSteps n) (encodeRow (initRowFor (caSeed n))) =
    encodeRow (iterRow (caSteps n) (initRowFor (caSeed n)))
  exact (iter_eq (caSteps n) (initRowFor (caSeed n))
    (by simp [initRowFor, ruleWidth])).symm

end Submission
