import Spec

set_option linter.unusedSimpArgs false
set_option linter.unusedVariables false

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
  let l := (((m <<< 1) ||| (m >>> 255)) &&& M)
  let r := (((m >>> 1) ||| ((m &&& 1) <<< 255)) &&& M)
  ((m ||| r) ^^^ (l &&& m &&& r)) &&& M

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

namespace Vec8

set_option linter.unusedVariables false

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

end Vec8


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

/-! V24: verified eight-lane SWAR. One mixer call produces a full 8-cell byte. -/

theorem vec8Scalar_eq (x : Nat) :
    Vec8.scalarRef x = mixBit31Nat x := by
  unfold Vec8.scalarRef Vec8.c1 Vec8.c2 Vec8.mask32 mixBit31Nat
  rfl

def pack8SWAR8 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  Vec8.mix8SWAR x x1 x2 x3 x4 x5 x6 x7

def pack6SWAR8 (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  Vec8.mix4SWAR x x1 x2 x3 +
    16 * Vec8.mixPairSWAR x4 x5

theorem pack8SWAR8_eq (x : Nat) (h : x + 7 * stepConst < 2 ^ 64) :
    pack8SWAR8 x = pack8Nat x := by
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
  dsimp [pack8SWAR8, pack8Nat]
  rw [Vec8.mix8SWAR_eq
        x
        (x + stepConst)
        (x + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst)
        h0 h1 h2 h3 h4 h5 h6 h7]
  simp only [Vec8.mixScalarNat_eq_ref, vec8Scalar_eq]

theorem pack6SWAR8_eq (x : Nat) (h : x + 5 * stepConst < 2 ^ 64) :
    pack6SWAR8 x = pack6Nat x := by
  have h0 : x < 2 ^ 64 := by omega
  have h1 : x + stepConst < 2 ^ 64 := by omega
  have h2 : x + stepConst + stepConst < 2 ^ 64 := by omega
  have h3 : x + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  have h4 : x + stepConst + stepConst + stepConst + stepConst < 2 ^ 64 := by omega
  dsimp [pack6SWAR8, pack6Nat]
  rw [Vec8.mix4SWAR_eq
        x (x + stepConst)
        (x + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst)
        h0 h1 h2 h3]
  rw [Vec8.mixPairSWAR_eq
        (x + stepConst + stepConst + stepConst + stepConst)
        (x + stepConst + stepConst + stepConst + stepConst + stepConst)
        h4]
  simp only [Vec8.mixScalarNat_eq_ref, vec8Scalar_eq]
  omega

def packByteTailSWAR8 : Nat → Nat → Nat
  | x, 0 => pack6SWAR8 x
  | x, n + 1 => pack8SWAR8 x + 256 * packByteTailSWAR8 (advance8 x) n

set_option maxRecDepth 32768 in
theorem packByteTailSWAR8_eq (x n : Nat)
    (h : x + (8 * n + 5) * stepConst < 2 ^ 64) :
    packByteTailSWAR8 x n = packByteTailNat x n := by
  induction n generalizing x with
  | zero =>
      simp only [packByteTailSWAR8, packByteTailNat, Nat.mul_zero, Nat.zero_add] at *
      exact pack6SWAR8_eq x h
  | succ n ih =>
      simp only [packByteTailSWAR8, packByteTailNat]
      have hk : 7 ≤ 8 * (n + 1) + 5 := by omega
      have hm : 7 * stepConst ≤ (8 * (n + 1) + 5) * stepConst :=
        Nat.mul_le_mul_right stepConst hk
      have hb : x + 7 * stepConst < 2 ^ 64 :=
        Nat.lt_of_le_of_lt (Nat.add_le_add_left hm x) h
      rw [pack8SWAR8_eq x hb]
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

def initPackedSWAR8 (seed : Nat) : Nat :=
  1 + 4 * packByteTailSWAR8 (seed + 3 * stepConst) 31

theorem initPackedSWAR8_eq (n : Nat) :
    initPackedSWAR8 (caSeed n) = initPackedByteNat (caSeed n) := by
  unfold initPackedSWAR8 initPackedByteNat
  rw [packByteTailSWAR8_eq]
  have hs : caSeed n < 2 ^ 32 := by
    unfold caSeed
    exact Nat.and_lt_two_pow n (by decide)
  have hc : (2 ^ 32 - 1) + 256 * stepConst < 2 ^ 64 := by
    unfold stepConst
    decide
  unfold stepConst at *
  omega


/-! V25: persistent 8-lane progression state. -/

def mix8Packed (p0 : Nat) : Nat :=
  let u := (p0 ^^^ (p0 >>> 16)) &&& Vec8.mask8
  let y := (u * Vec8.c1) &&& Vec8.mask8
  let v := (y ^^^ (y >>> 15)) &&& Vec8.mask8
  let p := v * Vec8.c2
  (p >>> 31) % 2 +
  2 * ((p >>> 95) % 2) +
  4 * ((p >>> 159) % 2) +
  8 * ((p >>> 223) % 2) +
  16 * ((p >>> 287) % 2) +
  32 * ((p >>> 351) % 2) +
  64 * ((p >>> 415) % 2) +
  128 * ((p >>> 479) % 2)

theorem mix8Packed_eq (a b c d e f g h : Nat) :
    mix8Packed (Vec8.pack8v a b c d e f g h) =
      Vec8.mix8SWAR a b c d e f g h := by
  rfl

def octState (x : Nat) : Nat :=
  let x1 := x + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  Vec8.pack8v x x1 x2 x3 x4 x5 x6 x7

theorem mix8Packed_state_eq (x : Nat) :
    mix8Packed (octState x) = pack8SWAR8 x := by
  rfl

def octDelta : Nat :=
  Vec8.pack8v
    (8 * stepConst) (8 * stepConst) (8 * stepConst) (8 * stepConst)
    (8 * stepConst) (8 * stepConst) (8 * stepConst) (8 * stepConst)

def advanceOct (p : Nat) : Nat :=
  p + octDelta

set_option maxRecDepth 32768 in
theorem advanceOct_state (x : Nat) :
    advanceOct (octState x) = octState (advance8 x) := by
  unfold advanceOct octState octDelta advance8
  unfold Vec8.pack8v Vec8.pack256 Vec8.pack4 Vec8.pack128 Vec8.pack2
  simp only [Nat.shiftLeft_eq]
  omega

def packOctTail : Nat → Nat → Nat → Nat
  | _, x, 0 => pack6SWAR8 x
  | p, x, n + 1 =>
      mix8Packed p + 256 * packOctTail (advanceOct p) (advance8 x) n

theorem packOctTail_eq (x n : Nat) :
    packOctTail (octState x) x n = packByteTailSWAR8 x n := by
  induction n generalizing x with
  | zero =>
      rfl
  | succ n ih =>
      simp only [packOctTail, packByteTailSWAR8]
      rw [mix8Packed_state_eq, advanceOct_state, ih]

def initPackedOctProgression (seed : Nat) : Nat :=
  let x := seed + 3 * stepConst
  1 + 4 * packOctTail (octState x) x 31

theorem initPackedOctProgression_eq (seed : Nat) :
    initPackedOctProgression seed = initPackedSWAR8 seed := by
  unfold initPackedOctProgression initPackedSWAR8
  dsimp
  rw [packOctTail_eq]

/-! V27b: contract the changing scalar progression from the hot loop.

V25 carries both the packed 8-lane state and a scalar x which is advanced on
every byte.  The final six-cell tail needs only the scalar reached after all
byte transitions, so compute that final scalar once and keep it constant while
the recursive loop advances only the packed oct-state. -/

def packOctTailConst : Nat → Nat → Nat → Nat
  | finalX, _, 0 => pack6SWAR8 finalX
  | finalX, p, n + 1 =>
      mix8Packed p + 256 * packOctTailConst finalX (advanceOct p) n

set_option maxRecDepth 32768 in
theorem packOctTailConst_eq (x n : Nat) :
    packOctTailConst (x + (8 * n) * stepConst) (octState x) n =
      packByteTailSWAR8 x n := by
  induction n generalizing x with
  | zero =>
      simp [packOctTailConst, packByteTailSWAR8]
  | succ n ih =>
      simp only [packOctTailConst, packByteTailSWAR8]
      rw [mix8Packed_state_eq, advanceOct_state]
      have hcoef : 8 * (n + 1) = 8 + 8 * n := by omega
      have hfinal :
          x + (8 * (n + 1)) * stepConst =
            advance8 x + (8 * n) * stepConst := by
        rw [advance8_eq_swar, hcoef, Nat.add_mul, Nat.add_assoc]
      rw [hfinal, ih]

def initPackedOctContracted (seed : Nat) : Nat :=
  let x := seed + 3 * stepConst
  1 + 4 * packOctTailConst (x + (8 * 31) * stepConst) (octState x) 31

theorem initPackedOctContracted_eq (seed : Nat) :
    initPackedOctContracted seed = initPackedSWAR8 seed := by
  simp only [initPackedOctContracted, initPackedSWAR8]
  rw [packOctTailConst_eq]

def impl_v27 : Nat → Nat := fun n =>
  biterFast (caSteps n) (initPackedOctContracted (caSeed n))

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

theorem impl_v27_correct : ∀ n, impl_v27 n = caSpecN n := by
  intro n
  unfold impl_v27
  rw [biterFast_eq, initPackedOctContracted_eq, initPackedSWAR8_eq, initPackedByteNat_eq, initPackedByte_eq, initPackedFastBit_eq, initPackedFast_eq]
  show biter (caSteps n) (encodeRow (initRowFor (caSeed n))) =
    encodeRow (iterRow (caSteps n) (initRowFor (caSeed n)))
  exact (iter_eq (caSteps n) (initRowFor (caSeed n))
    (by simp [initRowFor, ruleWidth])).symm

end Submission



namespace GenericPack

def packW (w p q : Nat) : Nat :=
  p + (q <<< w)

def maskW (w m : Nat) : Nat :=
  packW w m m

def stage (m s p : Nat) : Nat :=
  (p ^^^ (p >>> s)) &&& m

theorem testBit_packW (w p q i : Nat) (hp : p < 2 ^ w) :
    (packW w p q).testBit i =
      if i < w then p.testBit i else q.testBit (i - w) := by
  unfold packW
  simpa [Nat.add_comm, Nat.shiftLeft_eq, Nat.mul_comm] using
    (Nat.testBit_two_pow_mul_add q hp i)

theorem testBit_maskW (w m i : Nat) (hm : m < 2 ^ w) :
    (maskW w m).testBit i =
      if i < w then m.testBit i else m.testBit (i - w) := by
  unfold maskW
  exact testBit_packW w m m i hm

theorem stage_le (m s p : Nat) :
    stage m s p ≤ m := by
  unfold stage
  exact Nat.and_le_right

theorem stage_lt_pow (w m s p : Nat) (hm : m < 2 ^ w) :
    stage m s p < 2 ^ w :=
  Nat.lt_of_le_of_lt (stage_le m s p) hm

theorem bit_false_above_pow {x k i : Nat}
    (hx : x < 2 ^ k) (hi : k ≤ i) :
    x.testBit i = false := by
  have hpow : 2 ^ k ≤ 2 ^ i :=
    Nat.pow_le_pow_right (by omega) hi
  have hxi : x < 2 ^ i := Nat.lt_of_lt_of_le hx hpow
  simp [Nat.testBit, Nat.shiftRight_eq_div_pow, Nat.div_eq_of_lt hxi]

theorem lift_stage
    (w m s p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - s))
    (hs0 : 0 < s)
    (hsw : s ≤ w) :
    stage (maskW w m) s (packW w p q) =
      packW w (stage m s p) (stage m s q) := by
  have hmw : m < 2 ^ w := by
    have hpow : 2 ^ (w - s) ≤ 2 ^ w :=
      Nat.pow_le_pow_right (by omega) (Nat.sub_le w s)
    exact Nat.lt_of_lt_of_le hm hpow
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW w (stage m s p) (stage m s q) i
      (stage_lt_pow w m s p hmw)]
  unfold stage
  rw [Nat.testBit_and, testBit_maskW w m i hmw]
  simp only [Nat.testBit_and, Nat.testBit_xor, Nat.testBit_shiftRight]
  by_cases hi : i < w
  · rw [if_pos hi, if_pos hi]
    by_cases hb : m.testBit i = true
    · have hik : i < w - s := by
        by_cases hsmall : i < w - s
        · exact hsmall
        · have hki : w - s ≤ i := by omega
          have hf := bit_false_above_pow hm hki
          rw [hf] at hb
          simp at hb
      have his : s + i < w := by omega
      rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
      simp [hi, his, hb]
    · have hbf : m.testBit i = false := by
        cases h : m.testBit i <;> simp_all
      simp [hbf]
  · have hwi : w ≤ i := by omega
    let j := i - w
    have hij : i = w + j := by dsimp [j]; omega
    have hsi : ¬ s + i < w := by omega
    have hsub : (s + i) - w = s + j := by rw [hij]; omega
    rw [if_neg hi, if_neg hi]
    rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
    simp [hi, hwi, hsi, j, hsub]

def shrMask (m s p : Nat) : Nat :=
  (p >>> s) &&& m

theorem shrMask_le (m s p : Nat) :
    shrMask m s p ≤ m := by
  unfold shrMask
  exact Nat.and_le_right

theorem shrMask_lt_pow (w m s p : Nat) (hm : m < 2 ^ w) :
    shrMask m s p < 2 ^ w :=
  Nat.lt_of_le_of_lt (shrMask_le m s p) hm

theorem lift_shrMask
    (w m s p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - s))
    (hs0 : 0 < s)
    (hsw : s ≤ w) :
    shrMask (maskW w m) s (packW w p q) =
      packW w (shrMask m s p) (shrMask m s q) := by
  have hmw : m < 2 ^ w := by
    have hpow : 2 ^ (w - s) ≤ 2 ^ w :=
      Nat.pow_le_pow_right (by omega) (Nat.sub_le w s)
    exact Nat.lt_of_lt_of_le hm hpow
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW w (shrMask m s p) (shrMask m s q) i
      (shrMask_lt_pow w m s p hmw)]
  unfold shrMask
  rw [Nat.testBit_and, testBit_maskW w m i hmw]
  simp only [Nat.testBit_shiftRight]
  by_cases hi : i < w
  · rw [if_pos hi, if_pos hi]
    by_cases hb : m.testBit i = true
    · have hik : i < w - s := by
        by_cases hsmall : i < w - s
        · exact hsmall
        · have hki : w - s ≤ i := by omega
          have hf := bit_false_above_pow hm hki
          rw [hf] at hb
          simp at hb
      have his : s + i < w := by omega
      rw [testBit_packW w p q (s + i) hp]
      simp [his, hb]
    · have hbf : m.testBit i = false := by
        cases h : m.testBit i <;> simp_all
      simp [hbf]
  · let j := i - w
    have hij : i = w + j := by dsimp [j]; omega
    have hsi : ¬ s + i < w := by omega
    have hsub : (s + i) - w = s + j := by rw [hij]; omega
    rw [if_neg hi, if_neg hi]
    rw [testBit_packW w p q (s + i) hp]
    simp [hsi, j, hsub]

def orStage (m s p : Nat) : Nat :=
  (p ||| (p >>> s)) &&& m

theorem orStage_le (m s p : Nat) :
    orStage m s p ≤ m := by
  unfold orStage
  exact Nat.and_le_right

theorem orStage_lt_pow (w m s p : Nat) (hm : m < 2 ^ w) :
    orStage m s p < 2 ^ w :=
  Nat.lt_of_le_of_lt (orStage_le m s p) hm

theorem lift_or_stage
    (w m s p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - s))
    (hs0 : 0 < s)
    (hsw : s ≤ w) :
    orStage (maskW w m) s (packW w p q) =
      packW w (orStage m s p) (orStage m s q) := by
  have hmw : m < 2 ^ w := by
    have hpow : 2 ^ (w - s) ≤ 2 ^ w :=
      Nat.pow_le_pow_right (by omega) (Nat.sub_le w s)
    exact Nat.lt_of_lt_of_le hm hpow
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW w (orStage m s p) (orStage m s q) i
      (orStage_lt_pow w m s p hmw)]
  unfold orStage
  rw [Nat.testBit_and, testBit_maskW w m i hmw]
  simp only [Nat.testBit_and, Nat.testBit_or, Nat.testBit_shiftRight]
  by_cases hi : i < w
  · rw [if_pos hi, if_pos hi]
    by_cases hb : m.testBit i = true
    · have hik : i < w - s := by
        by_cases hsmall : i < w - s
        · exact hsmall
        · have hki : w - s ≤ i := by omega
          have hf := bit_false_above_pow hm hki
          rw [hf] at hb
          simp at hb
      have his : s + i < w := by omega
      rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
      simp [hi, his, hb]
    · have hbf : m.testBit i = false := by
        cases h : m.testBit i <;> simp_all
      simp [hbf]
  · have hwi : w ≤ i := by omega
    let j := i - w
    have hij : i = w + j := by dsimp [j]; omega
    have hsi : ¬ s + i < w := by omega
    have hsub : (s + i) - w = s + j := by rw [hij]; omega
    rw [if_neg hi, if_neg hi]
    rw [testBit_packW w p q i hp, testBit_packW w p q (s + i) hp]
    simp [hi, hsi, j, hsub]

theorem packW_lt_double
    (w p q : Nat)
    (hp : p < 2 ^ w)
    (hq : q < 2 ^ w) :
    packW w p q < 2 ^ (w + w) := by
  unfold packW
  rw [Nat.shiftLeft_eq]
  let P := 2 ^ w
  have hP : 0 < P := by
    dsimp [P]
    exact Nat.two_pow_pos w
  have hp' : p ≤ P - 1 := by
    dsimp [P] at hp ⊢
    omega
  have hq' : q ≤ P - 1 := by
    dsimp [P] at hq ⊢
    omega
  have hmul : q * P ≤ (P - 1) * P :=
    Nat.mul_le_mul_right P hq'
  have hPP : P ≤ P * P := by
    have h1 : 1 ≤ P := by omega
    have hm := Nat.mul_le_mul_left P h1
    simpa using hm
  calc
    p + q * P ≤ (P - 1) + (P - 1) * P :=
      Nat.add_le_add hp' hmul
    _ = P * P - 1 := by
      rw [Nat.sub_mul]
      simp
      omega
    _ < P * P := by omega
    _ = 2 ^ (w + w) := by
      dsimp [P]
      rw [Nat.pow_add]

theorem packW_mul (w p q k : Nat) :
    packW w p q * k = packW w (p * k) (q * k) := by
  unfold packW
  rw [Nat.add_mul, Nat.shiftLeft_eq, Nat.shiftLeft_eq]
  congr 1
  calc
    (q * 2 ^ w) * k = q * (2 ^ w * k) := Nat.mul_assoc _ _ _
    _ = q * (k * 2 ^ w) := by rw [Nat.mul_comm (2 ^ w) k]
    _ = (q * k) * 2 ^ w := (Nat.mul_assoc _ _ _).symm

theorem and_maskW
    (w m p q : Nat)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ w) :
    (packW w p q &&& maskW w m) =
      packW w (p &&& m) (q &&& m) := by
  apply Nat.eq_of_testBit_eq
  intro i
  rw [Nat.testBit_and, testBit_maskW w m i hm]
  have hpm : (p &&& m) < 2 ^ w := by
    exact Nat.lt_of_le_of_lt Nat.and_le_right hm
  rw [testBit_packW w (p &&& m) (q &&& m) i hpm]
  rw [testBit_packW w p q i hp]
  simp only [Nat.testBit_and]
  by_cases hi : i < w <;> simp [hi]

end GenericPack



namespace GenericMix

open GenericPack

def mixCore (m p : Nat) : Nat :=
  let u := stage m 16 p
  let y := (u * Submission.Vec8.c1) &&& m
  let v := stage m 15 y
  v * Submission.Vec8.c2

theorem lt_pow_mono_exp {x a b : Nat}
    (hx : x < 2 ^ a) (hab : a ≤ b) :
    x < 2 ^ b := by
  exact Nat.lt_of_lt_of_le hx (Nat.pow_le_pow_right (by omega) hab)

theorem stage_mul_lt
    (w m s p k : Nat)
    (hmk : m * k < 2 ^ w) :
    stage m s p * k < 2 ^ w := by
  have hle : stage m s p * k ≤ m * k :=
    Nat.mul_le_mul_right k (stage_le m s p)
  exact Nat.lt_of_le_of_lt hle hmk

theorem and_mask_lt
    (w m x : Nat)
    (hm : m < 2 ^ w) :
    (x &&& m) < 2 ^ w :=
  Nat.lt_of_le_of_lt Nat.and_le_right hm

theorem mixCore_lt
    (w m p : Nat)
    (hc2 : m * Submission.Vec8.c2 < 2 ^ w) :
    mixCore m p < 2 ^ w := by
  unfold mixCore
  exact stage_mul_lt w m 15
    (((stage m 16 p * Submission.Vec8.c1) &&& m))
    Submission.Vec8.c2 hc2

theorem mixCore_double
    (w m p q : Nat)
    (hw : 32 ≤ w)
    (hp : p < 2 ^ w)
    (hm : m < 2 ^ (w - 32))
    (hc1 : m * Submission.Vec8.c1 < 2 ^ w)
    (hc2 : m * Submission.Vec8.c2 < 2 ^ w) :
    mixCore (maskW w m) (packW w p q) =
      packW w (mixCore m p) (mixCore m q) := by
  have hmw : m < 2 ^ w :=
    lt_pow_mono_exp hm (by omega)
  have hm16 : m < 2 ^ (w - 16) :=
    lt_pow_mono_exp hm (by omega)
  have hm15 : m < 2 ^ (w - 15) :=
    lt_pow_mono_exp hm (by omega)
  have hp1 :
      stage m 16 p * Submission.Vec8.c1 < 2 ^ w :=
    stage_mul_lt w m 16 p Submission.Vec8.c1 hc1
  have hy :
      ((stage m 16 p * Submission.Vec8.c1) &&& m) < 2 ^ w :=
    and_mask_lt w m _ hmw
  simp only [mixCore]
  rw [lift_stage w m 16 p q hp hm16 (by decide) (by omega)]
  rw [packW_mul]
  rw [and_maskW w m
        (stage m 16 p * Submission.Vec8.c1)
        (stage m 16 q * Submission.Vec8.c1)
        hp1 hmw]
  rw [lift_stage w m 15
        ((stage m 16 p * Submission.Vec8.c1) &&& m)
        ((stage m 16 q * Submission.Vec8.c1) &&& m)
        hy hm15 (by decide) (by omega)]
  rw [packW_mul]

end GenericMix



namespace GatherPair

open GenericPack

def lowMask (g : Nat) : Nat := 2 ^ (2 * g) - 1

theorem testBit_lowMask (g i : Nat) :
    (lowMask g).testBit i = decide (i < 2 * g) := by
  unfold lowMask
  rw [Nat.testBit_two_pow_sub_one]

def gatherPair (g p q : Nat) : Nat :=
  orStage (lowMask g) (64 * g - g) (packW (64 * g) p q)

theorem gatherPair_eq
    (g p q : Nat)
    (hg : 0 < g)
    (hp : p < 2 ^ g)
    (hq : q < 2 ^ g) :
    gatherPair g p q = packW g p q := by
  have hp64 : p < 2 ^ (64 * g) := by
    exact Nat.lt_of_lt_of_le hp
      (Nat.pow_le_pow_right (by omega) (by omega))
  apply Nat.eq_of_testBit_eq
  intro i
  rw [testBit_packW g p q i hp]
  unfold gatherPair orStage
  rw [Nat.testBit_and, testBit_lowMask]
  simp only [Nat.testBit_or, Nat.testBit_shiftRight]
  by_cases h2 : i < 2 * g
  · simp only [h2, decide_true, Bool.and_true]
    by_cases h1 : i < g
    · rw [if_pos h1]
      have hi64 : i < 64 * g := by omega
      have hs64 : 64 * g - g + i < 64 * g := by omega
      rw [testBit_packW (64 * g) p q i hp64]
      rw [testBit_packW (64 * g) p q (64 * g - g + i) hp64]
      have hsrcHigh : g ≤ 64 * g - g + i := by omega
      have hfalse := bit_false_above_pow hp hsrcHigh
      simp [hi64, hs64, hfalse]
    · have hgi : g ≤ i := by omega
      rw [if_neg h1]
      have hi64 : i < 64 * g := by omega
      have hsHigh : 64 * g ≤ 64 * g - g + i := by omega
      have hsNot : ¬ (64 * g - g + i < 64 * g) := by omega
      have hsub : (64 * g - g + i) - 64 * g = i - g := by omega
      rw [testBit_packW (64 * g) p q i hp64]
      rw [testBit_packW (64 * g) p q (64 * g - g + i) hp64]
      have hpi : p.testBit i = false := bit_false_above_pow hp hgi
      simp [hi64, hsNot, hsub, hpi]
  · have h2f : decide (i < 2 * g) = false := by simp [h2]
    rw [h2f, Bool.and_false]
    by_cases h1 : i < g
    · omega
    · rw [if_neg h1]
      have hiq : g ≤ i - g := by omega
      have hqf := bit_false_above_pow hq hiq
      exact hqf.symm

end GatherPair



namespace WideProgression

open GenericPack
open Submission

def laneOnes256 : Nat := 0x1000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001000000000000000100000000000000010000000000000001
def laneIndex256 : Nat := 0xff00000000000000fe00000000000000fd00000000000000fc00000000000000fb00000000000000fa00000000000000f900000000000000f800000000000000f700000000000000f600000000000000f500000000000000f400000000000000f300000000000000f200000000000000f100000000000000f000000000000000ef00000000000000ee00000000000000ed00000000000000ec00000000000000eb00000000000000ea00000000000000e900000000000000e800000000000000e700000000000000e600000000000000e500000000000000e400000000000000e300000000000000e200000000000000e100000000000000e000000000000000df00000000000000de00000000000000dd00000000000000dc00000000000000db00000000000000da00000000000000d900000000000000d800000000000000d700000000000000d600000000000000d500000000000000d400000000000000d300000000000000d200000000000000d100000000000000d000000000000000cf00000000000000ce00000000000000cd00000000000000cc00000000000000cb00000000000000ca00000000000000c900000000000000c800000000000000c700000000000000c600000000000000c500000000000000c400000000000000c300000000000000c200000000000000c100000000000000c000000000000000bf00000000000000be00000000000000bd00000000000000bc00000000000000bb00000000000000ba00000000000000b900000000000000b800000000000000b700000000000000b600000000000000b500000000000000b400000000000000b300000000000000b200000000000000b100000000000000b000000000000000af00000000000000ae00000000000000ad00000000000000ac00000000000000ab00000000000000aa00000000000000a900000000000000a800000000000000a700000000000000a600000000000000a500000000000000a400000000000000a300000000000000a200000000000000a100000000000000a0000000000000009f000000000000009e000000000000009d000000000000009c000000000000009b000000000000009a0000000000000099000000000000009800000000000000970000000000000096000000000000009500000000000000940000000000000093000000000000009200000000000000910000000000000090000000000000008f000000000000008e000000000000008d000000000000008c000000000000008b000000000000008a0000000000000089000000000000008800000000000000870000000000000086000000000000008500000000000000840000000000000083000000000000008200000000000000810000000000000080000000000000007f000000000000007e000000000000007d000000000000007c000000000000007b000000000000007a0000000000000079000000000000007800000000000000770000000000000076000000000000007500000000000000740000000000000073000000000000007200000000000000710000000000000070000000000000006f000000000000006e000000000000006d000000000000006c000000000000006b000000000000006a0000000000000069000000000000006800000000000000670000000000000066000000000000006500000000000000640000000000000063000000000000006200000000000000610000000000000060000000000000005f000000000000005e000000000000005d000000000000005c000000000000005b000000000000005a0000000000000059000000000000005800000000000000570000000000000056000000000000005500000000000000540000000000000053000000000000005200000000000000510000000000000050000000000000004f000000000000004e000000000000004d000000000000004c000000000000004b000000000000004a0000000000000049000000000000004800000000000000470000000000000046000000000000004500000000000000440000000000000043000000000000004200000000000000410000000000000040000000000000003f000000000000003e000000000000003d000000000000003c000000000000003b000000000000003a0000000000000039000000000000003800000000000000370000000000000036000000000000003500000000000000340000000000000033000000000000003200000000000000310000000000000030000000000000002f000000000000002e000000000000002d000000000000002c000000000000002b000000000000002a0000000000000029000000000000002800000000000000270000000000000026000000000000002500000000000000240000000000000023000000000000002200000000000000210000000000000020000000000000001f000000000000001e000000000000001d000000000000001c000000000000001b000000000000001a0000000000000019000000000000001800000000000000170000000000000016000000000000001500000000000000140000000000000013000000000000001200000000000000110000000000000010000000000000000f000000000000000e000000000000000d000000000000000c000000000000000b000000000000000a0000000000000009000000000000000800000000000000070000000000000006000000000000000500000000000000040000000000000003000000000000000200000000000000010000000000000000

def state8 (x : Nat) : Nat := octState x
def state16 (x : Nat) : Nat :=
  packW 512 (state8 x) (state8 (x + 8 * stepConst))
def state32 (x : Nat) : Nat :=
  packW 1024 (state16 x) (state16 (x + 16 * stepConst))
def state64 (x : Nat) : Nat :=
  packW 2048 (state32 x) (state32 (x + 32 * stepConst))
def state128 (x : Nat) : Nat :=
  packW 4096 (state64 x) (state64 (x + 64 * stepConst))
def state256 (x : Nat) : Nat :=
  packW 8192 (state128 x) (state128 (x + 128 * stepConst))

def wideProgression (x : Nat) : Nat :=
  x * laneOnes256 + stepConst * laneIndex256

set_option maxRecDepth 1048576 in
set_option maxHeartbeats 800000 in
theorem wideProgression_eq_state256 (x : Nat) :
    wideProgression x = state256 x := by
  unfold wideProgression laneOnes256 laneIndex256
  unfold state256 state128 state64 state32 state16 state8
  unfold octState
  unfold Vec8.pack8v Vec8.pack256 Vec8.pack4 Vec8.pack128 Vec8.pack2
  unfold packW
  simp only [Nat.shiftLeft_eq]
  unfold stepConst
  omega

end WideProgression



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



namespace WideGather

open GenericPack
open GatherPair
open WideHierarchy
open Submission

set_option maxRecDepth 1048576
set_option exponentiation.threshold 20000
set_option maxHeartbeats 4000000

def dense1 (x : Nat) : Nat := bits1 x
theorem dense1_lt (x : Nat) : dense1 x < 2 ^ 1 := by
  unfold dense1 bits1 ones1
  exact shrMask_lt_pow 1 1 31 (raw1 x) (by decide)

def dense2 (x : Nat) : Nat :=
  packW 1 (dense1 x) (dense1 (x + 1 * stepConst))

theorem dense2_lt (x : Nat) : dense2 x < 2 ^ 2 := by
  unfold dense2
  exact packW_lt_double 1
    (dense1 x) (dense1 (x + 1 * stepConst))
    (dense1_lt x) (dense1_lt (x + 1 * stepConst))

def dense4 (x : Nat) : Nat :=
  packW 2 (dense2 x) (dense2 (x + 2 * stepConst))

theorem dense4_lt (x : Nat) : dense4 x < 2 ^ 4 := by
  unfold dense4
  exact packW_lt_double 2
    (dense2 x) (dense2 (x + 2 * stepConst))
    (dense2_lt x) (dense2_lt (x + 2 * stepConst))

def dense8 (x : Nat) : Nat :=
  packW 4 (dense4 x) (dense4 (x + 4 * stepConst))

theorem dense8_lt (x : Nat) : dense8 x < 2 ^ 8 := by
  unfold dense8
  exact packW_lt_double 4
    (dense4 x) (dense4 (x + 4 * stepConst))
    (dense4_lt x) (dense4_lt (x + 4 * stepConst))

def dense16 (x : Nat) : Nat :=
  packW 8 (dense8 x) (dense8 (x + 8 * stepConst))

theorem dense16_lt (x : Nat) : dense16 x < 2 ^ 16 := by
  unfold dense16
  exact packW_lt_double 8
    (dense8 x) (dense8 (x + 8 * stepConst))
    (dense8_lt x) (dense8_lt (x + 8 * stepConst))

def dense32 (x : Nat) : Nat :=
  packW 16 (dense16 x) (dense16 (x + 16 * stepConst))

theorem dense32_lt (x : Nat) : dense32 x < 2 ^ 32 := by
  unfold dense32
  exact packW_lt_double 16
    (dense16 x) (dense16 (x + 16 * stepConst))
    (dense16_lt x) (dense16_lt (x + 16 * stepConst))

def dense64 (x : Nat) : Nat :=
  packW 32 (dense32 x) (dense32 (x + 32 * stepConst))

theorem dense64_lt (x : Nat) : dense64 x < 2 ^ 64 := by
  unfold dense64
  exact packW_lt_double 32
    (dense32 x) (dense32 (x + 32 * stepConst))
    (dense32_lt x) (dense32_lt (x + 32 * stepConst))

def dense128 (x : Nat) : Nat :=
  packW 64 (dense64 x) (dense64 (x + 64 * stepConst))

theorem dense128_lt (x : Nat) : dense128 x < 2 ^ 128 := by
  unfold dense128
  exact packW_lt_double 64
    (dense64 x) (dense64 (x + 64 * stepConst))
    (dense64_lt x) (dense64_lt (x + 64 * stepConst))

def dense256 (x : Nat) : Nat :=
  packW 128 (dense128 x) (dense128 (x + 128 * stepConst))

theorem dense256_lt (x : Nat) : dense256 x < 2 ^ 256 := by
  unfold dense256
  exact packW_lt_double 128
    (dense128 x) (dense128 (x + 128 * stepConst))
    (dense128_lt x) (dense128_lt (x + 128 * stepConst))

def phys1_1 (x : Nat) : Nat := dense1 x
theorem phys1_1_lt (x : Nat) : phys1_1 x < 2 ^ 64 := by
  unfold phys1_1
  exact Nat.lt_of_lt_of_le (dense1_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys1_2 (x : Nat) : Nat :=
  packW 64 (phys1_1 x)
    (phys1_1 (x + 1 * stepConst))

theorem phys1_2_lt (x : Nat) :
    phys1_2 x < 2 ^ 128 := by
  unfold phys1_2
  simpa [show 64 + 64 = 128 by decide] using
    (packW_lt_double 64
      (phys1_1 x)
      (phys1_1 (x + 1 * stepConst))
      (phys1_1_lt x)
      (phys1_1_lt (x + 1 * stepConst)))

def phys1_4 (x : Nat) : Nat :=
  packW 128 (phys1_2 x)
    (phys1_2 (x + 2 * stepConst))

theorem phys1_4_lt (x : Nat) :
    phys1_4 x < 2 ^ 256 := by
  unfold phys1_4
  simpa [show 128 + 128 = 256 by decide] using
    (packW_lt_double 128
      (phys1_2 x)
      (phys1_2 (x + 2 * stepConst))
      (phys1_2_lt x)
      (phys1_2_lt (x + 2 * stepConst)))

def phys1_8 (x : Nat) : Nat :=
  packW 256 (phys1_4 x)
    (phys1_4 (x + 4 * stepConst))

theorem phys1_8_lt (x : Nat) :
    phys1_8 x < 2 ^ 512 := by
  unfold phys1_8
  simpa [show 256 + 256 = 512 by decide] using
    (packW_lt_double 256
      (phys1_4 x)
      (phys1_4 (x + 4 * stepConst))
      (phys1_4_lt x)
      (phys1_4_lt (x + 4 * stepConst)))

def phys1_16 (x : Nat) : Nat :=
  packW 512 (phys1_8 x)
    (phys1_8 (x + 8 * stepConst))

theorem phys1_16_lt (x : Nat) :
    phys1_16 x < 2 ^ 1024 := by
  unfold phys1_16
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys1_8 x)
      (phys1_8 (x + 8 * stepConst))
      (phys1_8_lt x)
      (phys1_8_lt (x + 8 * stepConst)))

def phys1_32 (x : Nat) : Nat :=
  packW 1024 (phys1_16 x)
    (phys1_16 (x + 16 * stepConst))

theorem phys1_32_lt (x : Nat) :
    phys1_32 x < 2 ^ 2048 := by
  unfold phys1_32
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys1_16 x)
      (phys1_16 (x + 16 * stepConst))
      (phys1_16_lt x)
      (phys1_16_lt (x + 16 * stepConst)))

def phys1_64 (x : Nat) : Nat :=
  packW 2048 (phys1_32 x)
    (phys1_32 (x + 32 * stepConst))

theorem phys1_64_lt (x : Nat) :
    phys1_64 x < 2 ^ 4096 := by
  unfold phys1_64
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys1_32 x)
      (phys1_32 (x + 32 * stepConst))
      (phys1_32_lt x)
      (phys1_32_lt (x + 32 * stepConst)))

def phys1_128 (x : Nat) : Nat :=
  packW 4096 (phys1_64 x)
    (phys1_64 (x + 64 * stepConst))

theorem phys1_128_lt (x : Nat) :
    phys1_128 x < 2 ^ 8192 := by
  unfold phys1_128
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys1_64 x)
      (phys1_64 (x + 64 * stepConst))
      (phys1_64_lt x)
      (phys1_64_lt (x + 64 * stepConst)))

def phys1_256 (x : Nat) : Nat :=
  packW 8192 (phys1_128 x)
    (phys1_128 (x + 128 * stepConst))

theorem phys1_256_lt (x : Nat) :
    phys1_256 x < 2 ^ 16384 := by
  unfold phys1_256
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys1_128 x)
      (phys1_128 (x + 128 * stepConst))
      (phys1_128_lt x)
      (phys1_128_lt (x + 128 * stepConst)))

def phys2_1 (x : Nat) : Nat := dense2 x
theorem phys2_1_lt (x : Nat) : phys2_1 x < 2 ^ 128 := by
  unfold phys2_1
  exact Nat.lt_of_lt_of_le (dense2_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys2_2 (x : Nat) : Nat :=
  packW 128 (phys2_1 x)
    (phys2_1 (x + 2 * stepConst))

theorem phys2_2_lt (x : Nat) :
    phys2_2 x < 2 ^ 256 := by
  unfold phys2_2
  simpa [show 128 + 128 = 256 by decide] using
    (packW_lt_double 128
      (phys2_1 x)
      (phys2_1 (x + 2 * stepConst))
      (phys2_1_lt x)
      (phys2_1_lt (x + 2 * stepConst)))

def phys2_4 (x : Nat) : Nat :=
  packW 256 (phys2_2 x)
    (phys2_2 (x + 4 * stepConst))

theorem phys2_4_lt (x : Nat) :
    phys2_4 x < 2 ^ 512 := by
  unfold phys2_4
  simpa [show 256 + 256 = 512 by decide] using
    (packW_lt_double 256
      (phys2_2 x)
      (phys2_2 (x + 4 * stepConst))
      (phys2_2_lt x)
      (phys2_2_lt (x + 4 * stepConst)))

def phys2_8 (x : Nat) : Nat :=
  packW 512 (phys2_4 x)
    (phys2_4 (x + 8 * stepConst))

theorem phys2_8_lt (x : Nat) :
    phys2_8 x < 2 ^ 1024 := by
  unfold phys2_8
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys2_4 x)
      (phys2_4 (x + 8 * stepConst))
      (phys2_4_lt x)
      (phys2_4_lt (x + 8 * stepConst)))

def phys2_16 (x : Nat) : Nat :=
  packW 1024 (phys2_8 x)
    (phys2_8 (x + 16 * stepConst))

theorem phys2_16_lt (x : Nat) :
    phys2_16 x < 2 ^ 2048 := by
  unfold phys2_16
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys2_8 x)
      (phys2_8 (x + 16 * stepConst))
      (phys2_8_lt x)
      (phys2_8_lt (x + 16 * stepConst)))

def phys2_32 (x : Nat) : Nat :=
  packW 2048 (phys2_16 x)
    (phys2_16 (x + 32 * stepConst))

theorem phys2_32_lt (x : Nat) :
    phys2_32 x < 2 ^ 4096 := by
  unfold phys2_32
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys2_16 x)
      (phys2_16 (x + 32 * stepConst))
      (phys2_16_lt x)
      (phys2_16_lt (x + 32 * stepConst)))

def phys2_64 (x : Nat) : Nat :=
  packW 4096 (phys2_32 x)
    (phys2_32 (x + 64 * stepConst))

theorem phys2_64_lt (x : Nat) :
    phys2_64 x < 2 ^ 8192 := by
  unfold phys2_64
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys2_32 x)
      (phys2_32 (x + 64 * stepConst))
      (phys2_32_lt x)
      (phys2_32_lt (x + 64 * stepConst)))

def phys2_128 (x : Nat) : Nat :=
  packW 8192 (phys2_64 x)
    (phys2_64 (x + 128 * stepConst))

theorem phys2_128_lt (x : Nat) :
    phys2_128 x < 2 ^ 16384 := by
  unfold phys2_128
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys2_64 x)
      (phys2_64 (x + 128 * stepConst))
      (phys2_64_lt x)
      (phys2_64_lt (x + 128 * stepConst)))

def phys4_1 (x : Nat) : Nat := dense4 x
theorem phys4_1_lt (x : Nat) : phys4_1 x < 2 ^ 256 := by
  unfold phys4_1
  exact Nat.lt_of_lt_of_le (dense4_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys4_2 (x : Nat) : Nat :=
  packW 256 (phys4_1 x)
    (phys4_1 (x + 4 * stepConst))

theorem phys4_2_lt (x : Nat) :
    phys4_2 x < 2 ^ 512 := by
  unfold phys4_2
  simpa [show 256 + 256 = 512 by decide] using
    (packW_lt_double 256
      (phys4_1 x)
      (phys4_1 (x + 4 * stepConst))
      (phys4_1_lt x)
      (phys4_1_lt (x + 4 * stepConst)))

def phys4_4 (x : Nat) : Nat :=
  packW 512 (phys4_2 x)
    (phys4_2 (x + 8 * stepConst))

theorem phys4_4_lt (x : Nat) :
    phys4_4 x < 2 ^ 1024 := by
  unfold phys4_4
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys4_2 x)
      (phys4_2 (x + 8 * stepConst))
      (phys4_2_lt x)
      (phys4_2_lt (x + 8 * stepConst)))

def phys4_8 (x : Nat) : Nat :=
  packW 1024 (phys4_4 x)
    (phys4_4 (x + 16 * stepConst))

theorem phys4_8_lt (x : Nat) :
    phys4_8 x < 2 ^ 2048 := by
  unfold phys4_8
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys4_4 x)
      (phys4_4 (x + 16 * stepConst))
      (phys4_4_lt x)
      (phys4_4_lt (x + 16 * stepConst)))

def phys4_16 (x : Nat) : Nat :=
  packW 2048 (phys4_8 x)
    (phys4_8 (x + 32 * stepConst))

theorem phys4_16_lt (x : Nat) :
    phys4_16 x < 2 ^ 4096 := by
  unfold phys4_16
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys4_8 x)
      (phys4_8 (x + 32 * stepConst))
      (phys4_8_lt x)
      (phys4_8_lt (x + 32 * stepConst)))

def phys4_32 (x : Nat) : Nat :=
  packW 4096 (phys4_16 x)
    (phys4_16 (x + 64 * stepConst))

theorem phys4_32_lt (x : Nat) :
    phys4_32 x < 2 ^ 8192 := by
  unfold phys4_32
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys4_16 x)
      (phys4_16 (x + 64 * stepConst))
      (phys4_16_lt x)
      (phys4_16_lt (x + 64 * stepConst)))

def phys4_64 (x : Nat) : Nat :=
  packW 8192 (phys4_32 x)
    (phys4_32 (x + 128 * stepConst))

theorem phys4_64_lt (x : Nat) :
    phys4_64 x < 2 ^ 16384 := by
  unfold phys4_64
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys4_32 x)
      (phys4_32 (x + 128 * stepConst))
      (phys4_32_lt x)
      (phys4_32_lt (x + 128 * stepConst)))

def phys8_1 (x : Nat) : Nat := dense8 x
theorem phys8_1_lt (x : Nat) : phys8_1 x < 2 ^ 512 := by
  unfold phys8_1
  exact Nat.lt_of_lt_of_le (dense8_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys8_2 (x : Nat) : Nat :=
  packW 512 (phys8_1 x)
    (phys8_1 (x + 8 * stepConst))

theorem phys8_2_lt (x : Nat) :
    phys8_2 x < 2 ^ 1024 := by
  unfold phys8_2
  simpa [show 512 + 512 = 1024 by decide] using
    (packW_lt_double 512
      (phys8_1 x)
      (phys8_1 (x + 8 * stepConst))
      (phys8_1_lt x)
      (phys8_1_lt (x + 8 * stepConst)))

def phys8_4 (x : Nat) : Nat :=
  packW 1024 (phys8_2 x)
    (phys8_2 (x + 16 * stepConst))

theorem phys8_4_lt (x : Nat) :
    phys8_4 x < 2 ^ 2048 := by
  unfold phys8_4
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys8_2 x)
      (phys8_2 (x + 16 * stepConst))
      (phys8_2_lt x)
      (phys8_2_lt (x + 16 * stepConst)))

def phys8_8 (x : Nat) : Nat :=
  packW 2048 (phys8_4 x)
    (phys8_4 (x + 32 * stepConst))

theorem phys8_8_lt (x : Nat) :
    phys8_8 x < 2 ^ 4096 := by
  unfold phys8_8
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys8_4 x)
      (phys8_4 (x + 32 * stepConst))
      (phys8_4_lt x)
      (phys8_4_lt (x + 32 * stepConst)))

def phys8_16 (x : Nat) : Nat :=
  packW 4096 (phys8_8 x)
    (phys8_8 (x + 64 * stepConst))

theorem phys8_16_lt (x : Nat) :
    phys8_16 x < 2 ^ 8192 := by
  unfold phys8_16
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys8_8 x)
      (phys8_8 (x + 64 * stepConst))
      (phys8_8_lt x)
      (phys8_8_lt (x + 64 * stepConst)))

def phys8_32 (x : Nat) : Nat :=
  packW 8192 (phys8_16 x)
    (phys8_16 (x + 128 * stepConst))

theorem phys8_32_lt (x : Nat) :
    phys8_32 x < 2 ^ 16384 := by
  unfold phys8_32
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys8_16 x)
      (phys8_16 (x + 128 * stepConst))
      (phys8_16_lt x)
      (phys8_16_lt (x + 128 * stepConst)))

def phys16_1 (x : Nat) : Nat := dense16 x
theorem phys16_1_lt (x : Nat) : phys16_1 x < 2 ^ 1024 := by
  unfold phys16_1
  exact Nat.lt_of_lt_of_le (dense16_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys16_2 (x : Nat) : Nat :=
  packW 1024 (phys16_1 x)
    (phys16_1 (x + 16 * stepConst))

theorem phys16_2_lt (x : Nat) :
    phys16_2 x < 2 ^ 2048 := by
  unfold phys16_2
  simpa [show 1024 + 1024 = 2048 by decide] using
    (packW_lt_double 1024
      (phys16_1 x)
      (phys16_1 (x + 16 * stepConst))
      (phys16_1_lt x)
      (phys16_1_lt (x + 16 * stepConst)))

def phys16_4 (x : Nat) : Nat :=
  packW 2048 (phys16_2 x)
    (phys16_2 (x + 32 * stepConst))

theorem phys16_4_lt (x : Nat) :
    phys16_4 x < 2 ^ 4096 := by
  unfold phys16_4
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys16_2 x)
      (phys16_2 (x + 32 * stepConst))
      (phys16_2_lt x)
      (phys16_2_lt (x + 32 * stepConst)))

def phys16_8 (x : Nat) : Nat :=
  packW 4096 (phys16_4 x)
    (phys16_4 (x + 64 * stepConst))

theorem phys16_8_lt (x : Nat) :
    phys16_8 x < 2 ^ 8192 := by
  unfold phys16_8
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys16_4 x)
      (phys16_4 (x + 64 * stepConst))
      (phys16_4_lt x)
      (phys16_4_lt (x + 64 * stepConst)))

def phys16_16 (x : Nat) : Nat :=
  packW 8192 (phys16_8 x)
    (phys16_8 (x + 128 * stepConst))

theorem phys16_16_lt (x : Nat) :
    phys16_16 x < 2 ^ 16384 := by
  unfold phys16_16
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys16_8 x)
      (phys16_8 (x + 128 * stepConst))
      (phys16_8_lt x)
      (phys16_8_lt (x + 128 * stepConst)))

def phys32_1 (x : Nat) : Nat := dense32 x
theorem phys32_1_lt (x : Nat) : phys32_1 x < 2 ^ 2048 := by
  unfold phys32_1
  exact Nat.lt_of_lt_of_le (dense32_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys32_2 (x : Nat) : Nat :=
  packW 2048 (phys32_1 x)
    (phys32_1 (x + 32 * stepConst))

theorem phys32_2_lt (x : Nat) :
    phys32_2 x < 2 ^ 4096 := by
  unfold phys32_2
  simpa [show 2048 + 2048 = 4096 by decide] using
    (packW_lt_double 2048
      (phys32_1 x)
      (phys32_1 (x + 32 * stepConst))
      (phys32_1_lt x)
      (phys32_1_lt (x + 32 * stepConst)))

def phys32_4 (x : Nat) : Nat :=
  packW 4096 (phys32_2 x)
    (phys32_2 (x + 64 * stepConst))

theorem phys32_4_lt (x : Nat) :
    phys32_4 x < 2 ^ 8192 := by
  unfold phys32_4
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys32_2 x)
      (phys32_2 (x + 64 * stepConst))
      (phys32_2_lt x)
      (phys32_2_lt (x + 64 * stepConst)))

def phys32_8 (x : Nat) : Nat :=
  packW 8192 (phys32_4 x)
    (phys32_4 (x + 128 * stepConst))

theorem phys32_8_lt (x : Nat) :
    phys32_8 x < 2 ^ 16384 := by
  unfold phys32_8
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys32_4 x)
      (phys32_4 (x + 128 * stepConst))
      (phys32_4_lt x)
      (phys32_4_lt (x + 128 * stepConst)))

def phys64_1 (x : Nat) : Nat := dense64 x
theorem phys64_1_lt (x : Nat) : phys64_1 x < 2 ^ 4096 := by
  unfold phys64_1
  exact Nat.lt_of_lt_of_le (dense64_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys64_2 (x : Nat) : Nat :=
  packW 4096 (phys64_1 x)
    (phys64_1 (x + 64 * stepConst))

theorem phys64_2_lt (x : Nat) :
    phys64_2 x < 2 ^ 8192 := by
  unfold phys64_2
  simpa [show 4096 + 4096 = 8192 by decide] using
    (packW_lt_double 4096
      (phys64_1 x)
      (phys64_1 (x + 64 * stepConst))
      (phys64_1_lt x)
      (phys64_1_lt (x + 64 * stepConst)))

def phys64_4 (x : Nat) : Nat :=
  packW 8192 (phys64_2 x)
    (phys64_2 (x + 128 * stepConst))

theorem phys64_4_lt (x : Nat) :
    phys64_4 x < 2 ^ 16384 := by
  unfold phys64_4
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys64_2 x)
      (phys64_2 (x + 128 * stepConst))
      (phys64_2_lt x)
      (phys64_2_lt (x + 128 * stepConst)))

def phys128_1 (x : Nat) : Nat := dense128 x
theorem phys128_1_lt (x : Nat) : phys128_1 x < 2 ^ 8192 := by
  unfold phys128_1
  exact Nat.lt_of_lt_of_le (dense128_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

def phys128_2 (x : Nat) : Nat :=
  packW 8192 (phys128_1 x)
    (phys128_1 (x + 128 * stepConst))

theorem phys128_2_lt (x : Nat) :
    phys128_2 x < 2 ^ 16384 := by
  unfold phys128_2
  simpa [show 8192 + 8192 = 16384 by decide] using
    (packW_lt_double 8192
      (phys128_1 x)
      (phys128_1 (x + 128 * stepConst))
      (phys128_1_lt x)
      (phys128_1_lt (x + 128 * stepConst)))

def phys256_1 (x : Nat) : Nat := dense256 x
theorem phys256_1_lt (x : Nat) : phys256_1 x < 2 ^ 16384 := by
  unfold phys256_1
  exact Nat.lt_of_lt_of_le (dense256_lt x)
    (Nat.pow_le_pow_right (by omega) (by decide))

theorem bits1_phys (x : Nat) : bits1 x = phys1_1 x := by rfl

theorem bits2_phys (x : Nat)
    (h : x + 1 * stepConst < 2 ^ 64) :
    bits2 x = phys1_2 x := by
  rw [bits2_eq x h]
  unfold phys1_2 phys1_1 dense1
  simp

theorem bits4_phys (x : Nat)
    (h : x + 3 * stepConst < 2 ^ 64) :
    bits4 x = phys1_4 x := by
  unfold phys1_4
  rw [bits4_eq x h]
  rw [bits2_phys x (by omega)]
  rw [bits2_phys (x + 2 * stepConst) (by omega)]

theorem bits8_phys (x : Nat)
    (h : x + 7 * stepConst < 2 ^ 64) :
    bits8 x = phys1_8 x := by
  unfold phys1_8
  rw [bits8_eq x h]
  rw [bits4_phys x (by omega)]
  rw [bits4_phys (x + 4 * stepConst) (by omega)]

theorem bits16_phys (x : Nat)
    (h : x + 15 * stepConst < 2 ^ 64) :
    bits16 x = phys1_16 x := by
  unfold phys1_16
  rw [bits16_eq x h]
  rw [bits8_phys x (by omega)]
  rw [bits8_phys (x + 8 * stepConst) (by omega)]

theorem bits32_phys (x : Nat)
    (h : x + 31 * stepConst < 2 ^ 64) :
    bits32 x = phys1_32 x := by
  unfold phys1_32
  rw [bits32_eq x h]
  rw [bits16_phys x (by omega)]
  rw [bits16_phys (x + 16 * stepConst) (by omega)]

theorem bits64_phys (x : Nat)
    (h : x + 63 * stepConst < 2 ^ 64) :
    bits64 x = phys1_64 x := by
  unfold phys1_64
  rw [bits64_eq x h]
  rw [bits32_phys x (by omega)]
  rw [bits32_phys (x + 32 * stepConst) (by omega)]

theorem bits128_phys (x : Nat)
    (h : x + 127 * stepConst < 2 ^ 64) :
    bits128 x = phys1_128 x := by
  unfold phys1_128
  rw [bits128_eq x h]
  rw [bits64_phys x (by omega)]
  rw [bits64_phys (x + 64 * stepConst) (by omega)]

theorem bits256_phys (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    bits256 x = phys1_256 x := by
  unfold phys1_256
  rw [bits256_eq x h]
  rw [bits128_phys x (by omega)]
  rw [bits128_phys (x + 128 * stepConst) (by omega)]
def stageMask1_2 : Nat := lowMask 1
def stageMask1_4 : Nat :=
  maskW 128 stageMask1_2
def stageMask1_8 : Nat :=
  maskW 256 stageMask1_4
def stageMask1_16 : Nat :=
  maskW 512 stageMask1_8
def stageMask1_32 : Nat :=
  maskW 1024 stageMask1_16
def stageMask1_64 : Nat :=
  maskW 2048 stageMask1_32
def stageMask1_128 : Nat :=
  maskW 4096 stageMask1_64
def stageMask1_256 : Nat :=
  maskW 8192 stageMask1_128

theorem stage1_2 (x : Nat) :
    orStage stageMask1_2 63 (phys1_2 x) =
      phys2_1 x := by
  unfold stageMask1_2 phys1_2 phys2_1 dense2
  exact gatherPair_eq 1 (dense1 x)
    (dense1 (x + 1 * stepConst))
    (by decide) (dense1_lt x)
    (dense1_lt (x + 1 * stepConst))

theorem stage1_4 (x : Nat) :
    orStage stageMask1_4 63 (phys1_4 x) =
      phys2_2 x := by
  unfold stageMask1_4 phys1_4 phys2_2
  rw [lift_or_stage 128 stageMask1_2 63
        (phys1_2 x)
        (phys1_2 (x + 2 * stepConst))
        (phys1_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_2 x]
  rw [stage1_2 (x + 2 * stepConst)]

theorem stage1_8 (x : Nat) :
    orStage stageMask1_8 63 (phys1_8 x) =
      phys2_4 x := by
  unfold stageMask1_8 phys1_8 phys2_4
  rw [lift_or_stage 256 stageMask1_4 63
        (phys1_4 x)
        (phys1_4 (x + 4 * stepConst))
        (phys1_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_4 x]
  rw [stage1_4 (x + 4 * stepConst)]

theorem stage1_16 (x : Nat) :
    orStage stageMask1_16 63 (phys1_16 x) =
      phys2_8 x := by
  unfold stageMask1_16 phys1_16 phys2_8
  rw [lift_or_stage 512 stageMask1_8 63
        (phys1_8 x)
        (phys1_8 (x + 8 * stepConst))
        (phys1_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_8 x]
  rw [stage1_8 (x + 8 * stepConst)]

theorem stage1_32 (x : Nat) :
    orStage stageMask1_32 63 (phys1_32 x) =
      phys2_16 x := by
  unfold stageMask1_32 phys1_32 phys2_16
  rw [lift_or_stage 1024 stageMask1_16 63
        (phys1_16 x)
        (phys1_16 (x + 16 * stepConst))
        (phys1_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_16 x]
  rw [stage1_16 (x + 16 * stepConst)]

theorem stage1_64 (x : Nat) :
    orStage stageMask1_64 63 (phys1_64 x) =
      phys2_32 x := by
  unfold stageMask1_64 phys1_64 phys2_32
  rw [lift_or_stage 2048 stageMask1_32 63
        (phys1_32 x)
        (phys1_32 (x + 32 * stepConst))
        (phys1_32_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_32 x]
  rw [stage1_32 (x + 32 * stepConst)]

theorem stage1_128 (x : Nat) :
    orStage stageMask1_128 63 (phys1_128 x) =
      phys2_64 x := by
  unfold stageMask1_128 phys1_128 phys2_64
  rw [lift_or_stage 4096 stageMask1_64 63
        (phys1_64 x)
        (phys1_64 (x + 64 * stepConst))
        (phys1_64_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_64 x]
  rw [stage1_64 (x + 64 * stepConst)]

theorem stage1_256 (x : Nat) :
    orStage stageMask1_256 63 (phys1_256 x) =
      phys2_128 x := by
  unfold stageMask1_256 phys1_256 phys2_128
  rw [lift_or_stage 8192 stageMask1_128 63
        (phys1_128 x)
        (phys1_128 (x + 128 * stepConst))
        (phys1_128_lt x) (by decide) (by decide) (by decide)]
  rw [stage1_128 x]
  rw [stage1_128 (x + 128 * stepConst)]

def stageMask2_2 : Nat := lowMask 2
def stageMask2_4 : Nat :=
  maskW 256 stageMask2_2
def stageMask2_8 : Nat :=
  maskW 512 stageMask2_4
def stageMask2_16 : Nat :=
  maskW 1024 stageMask2_8
def stageMask2_32 : Nat :=
  maskW 2048 stageMask2_16
def stageMask2_64 : Nat :=
  maskW 4096 stageMask2_32
def stageMask2_128 : Nat :=
  maskW 8192 stageMask2_64

theorem stage2_2 (x : Nat) :
    orStage stageMask2_2 126 (phys2_2 x) =
      phys4_1 x := by
  unfold stageMask2_2 phys2_2 phys4_1 dense4
  exact gatherPair_eq 2 (dense2 x)
    (dense2 (x + 2 * stepConst))
    (by decide) (dense2_lt x)
    (dense2_lt (x + 2 * stepConst))

theorem stage2_4 (x : Nat) :
    orStage stageMask2_4 126 (phys2_4 x) =
      phys4_2 x := by
  unfold stageMask2_4 phys2_4 phys4_2
  rw [lift_or_stage 256 stageMask2_2 126
        (phys2_2 x)
        (phys2_2 (x + 4 * stepConst))
        (phys2_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_2 x]
  rw [stage2_2 (x + 4 * stepConst)]

theorem stage2_8 (x : Nat) :
    orStage stageMask2_8 126 (phys2_8 x) =
      phys4_4 x := by
  unfold stageMask2_8 phys2_8 phys4_4
  rw [lift_or_stage 512 stageMask2_4 126
        (phys2_4 x)
        (phys2_4 (x + 8 * stepConst))
        (phys2_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_4 x]
  rw [stage2_4 (x + 8 * stepConst)]

theorem stage2_16 (x : Nat) :
    orStage stageMask2_16 126 (phys2_16 x) =
      phys4_8 x := by
  unfold stageMask2_16 phys2_16 phys4_8
  rw [lift_or_stage 1024 stageMask2_8 126
        (phys2_8 x)
        (phys2_8 (x + 16 * stepConst))
        (phys2_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_8 x]
  rw [stage2_8 (x + 16 * stepConst)]

theorem stage2_32 (x : Nat) :
    orStage stageMask2_32 126 (phys2_32 x) =
      phys4_16 x := by
  unfold stageMask2_32 phys2_32 phys4_16
  rw [lift_or_stage 2048 stageMask2_16 126
        (phys2_16 x)
        (phys2_16 (x + 32 * stepConst))
        (phys2_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_16 x]
  rw [stage2_16 (x + 32 * stepConst)]

theorem stage2_64 (x : Nat) :
    orStage stageMask2_64 126 (phys2_64 x) =
      phys4_32 x := by
  unfold stageMask2_64 phys2_64 phys4_32
  rw [lift_or_stage 4096 stageMask2_32 126
        (phys2_32 x)
        (phys2_32 (x + 64 * stepConst))
        (phys2_32_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_32 x]
  rw [stage2_32 (x + 64 * stepConst)]

theorem stage2_128 (x : Nat) :
    orStage stageMask2_128 126 (phys2_128 x) =
      phys4_64 x := by
  unfold stageMask2_128 phys2_128 phys4_64
  rw [lift_or_stage 8192 stageMask2_64 126
        (phys2_64 x)
        (phys2_64 (x + 128 * stepConst))
        (phys2_64_lt x) (by decide) (by decide) (by decide)]
  rw [stage2_64 x]
  rw [stage2_64 (x + 128 * stepConst)]

def stageMask4_2 : Nat := lowMask 4
def stageMask4_4 : Nat :=
  maskW 512 stageMask4_2
def stageMask4_8 : Nat :=
  maskW 1024 stageMask4_4
def stageMask4_16 : Nat :=
  maskW 2048 stageMask4_8
def stageMask4_32 : Nat :=
  maskW 4096 stageMask4_16
def stageMask4_64 : Nat :=
  maskW 8192 stageMask4_32

theorem stage4_2 (x : Nat) :
    orStage stageMask4_2 252 (phys4_2 x) =
      phys8_1 x := by
  unfold stageMask4_2 phys4_2 phys8_1 dense8
  exact gatherPair_eq 4 (dense4 x)
    (dense4 (x + 4 * stepConst))
    (by decide) (dense4_lt x)
    (dense4_lt (x + 4 * stepConst))

theorem stage4_4 (x : Nat) :
    orStage stageMask4_4 252 (phys4_4 x) =
      phys8_2 x := by
  unfold stageMask4_4 phys4_4 phys8_2
  rw [lift_or_stage 512 stageMask4_2 252
        (phys4_2 x)
        (phys4_2 (x + 8 * stepConst))
        (phys4_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_2 x]
  rw [stage4_2 (x + 8 * stepConst)]

theorem stage4_8 (x : Nat) :
    orStage stageMask4_8 252 (phys4_8 x) =
      phys8_4 x := by
  unfold stageMask4_8 phys4_8 phys8_4
  rw [lift_or_stage 1024 stageMask4_4 252
        (phys4_4 x)
        (phys4_4 (x + 16 * stepConst))
        (phys4_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_4 x]
  rw [stage4_4 (x + 16 * stepConst)]

theorem stage4_16 (x : Nat) :
    orStage stageMask4_16 252 (phys4_16 x) =
      phys8_8 x := by
  unfold stageMask4_16 phys4_16 phys8_8
  rw [lift_or_stage 2048 stageMask4_8 252
        (phys4_8 x)
        (phys4_8 (x + 32 * stepConst))
        (phys4_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_8 x]
  rw [stage4_8 (x + 32 * stepConst)]

theorem stage4_32 (x : Nat) :
    orStage stageMask4_32 252 (phys4_32 x) =
      phys8_16 x := by
  unfold stageMask4_32 phys4_32 phys8_16
  rw [lift_or_stage 4096 stageMask4_16 252
        (phys4_16 x)
        (phys4_16 (x + 64 * stepConst))
        (phys4_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_16 x]
  rw [stage4_16 (x + 64 * stepConst)]

theorem stage4_64 (x : Nat) :
    orStage stageMask4_64 252 (phys4_64 x) =
      phys8_32 x := by
  unfold stageMask4_64 phys4_64 phys8_32
  rw [lift_or_stage 8192 stageMask4_32 252
        (phys4_32 x)
        (phys4_32 (x + 128 * stepConst))
        (phys4_32_lt x) (by decide) (by decide) (by decide)]
  rw [stage4_32 x]
  rw [stage4_32 (x + 128 * stepConst)]

def stageMask8_2 : Nat := lowMask 8
def stageMask8_4 : Nat :=
  maskW 1024 stageMask8_2
def stageMask8_8 : Nat :=
  maskW 2048 stageMask8_4
def stageMask8_16 : Nat :=
  maskW 4096 stageMask8_8
def stageMask8_32 : Nat :=
  maskW 8192 stageMask8_16

theorem stage8_2 (x : Nat) :
    orStage stageMask8_2 504 (phys8_2 x) =
      phys16_1 x := by
  unfold stageMask8_2 phys8_2 phys16_1 dense16
  exact gatherPair_eq 8 (dense8 x)
    (dense8 (x + 8 * stepConst))
    (by decide) (dense8_lt x)
    (dense8_lt (x + 8 * stepConst))

theorem stage8_4 (x : Nat) :
    orStage stageMask8_4 504 (phys8_4 x) =
      phys16_2 x := by
  unfold stageMask8_4 phys8_4 phys16_2
  rw [lift_or_stage 1024 stageMask8_2 504
        (phys8_2 x)
        (phys8_2 (x + 16 * stepConst))
        (phys8_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_2 x]
  rw [stage8_2 (x + 16 * stepConst)]

theorem stage8_8 (x : Nat) :
    orStage stageMask8_8 504 (phys8_8 x) =
      phys16_4 x := by
  unfold stageMask8_8 phys8_8 phys16_4
  rw [lift_or_stage 2048 stageMask8_4 504
        (phys8_4 x)
        (phys8_4 (x + 32 * stepConst))
        (phys8_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_4 x]
  rw [stage8_4 (x + 32 * stepConst)]

theorem stage8_16 (x : Nat) :
    orStage stageMask8_16 504 (phys8_16 x) =
      phys16_8 x := by
  unfold stageMask8_16 phys8_16 phys16_8
  rw [lift_or_stage 4096 stageMask8_8 504
        (phys8_8 x)
        (phys8_8 (x + 64 * stepConst))
        (phys8_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_8 x]
  rw [stage8_8 (x + 64 * stepConst)]

theorem stage8_32 (x : Nat) :
    orStage stageMask8_32 504 (phys8_32 x) =
      phys16_16 x := by
  unfold stageMask8_32 phys8_32 phys16_16
  rw [lift_or_stage 8192 stageMask8_16 504
        (phys8_16 x)
        (phys8_16 (x + 128 * stepConst))
        (phys8_16_lt x) (by decide) (by decide) (by decide)]
  rw [stage8_16 x]
  rw [stage8_16 (x + 128 * stepConst)]

def stageMask16_2 : Nat := lowMask 16
def stageMask16_4 : Nat :=
  maskW 2048 stageMask16_2
def stageMask16_8 : Nat :=
  maskW 4096 stageMask16_4
def stageMask16_16 : Nat :=
  maskW 8192 stageMask16_8

theorem stage16_2 (x : Nat) :
    orStage stageMask16_2 1008 (phys16_2 x) =
      phys32_1 x := by
  unfold stageMask16_2 phys16_2 phys32_1 dense32
  exact gatherPair_eq 16 (dense16 x)
    (dense16 (x + 16 * stepConst))
    (by decide) (dense16_lt x)
    (dense16_lt (x + 16 * stepConst))

theorem stage16_4 (x : Nat) :
    orStage stageMask16_4 1008 (phys16_4 x) =
      phys32_2 x := by
  unfold stageMask16_4 phys16_4 phys32_2
  rw [lift_or_stage 2048 stageMask16_2 1008
        (phys16_2 x)
        (phys16_2 (x + 32 * stepConst))
        (phys16_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage16_2 x]
  rw [stage16_2 (x + 32 * stepConst)]

theorem stage16_8 (x : Nat) :
    orStage stageMask16_8 1008 (phys16_8 x) =
      phys32_4 x := by
  unfold stageMask16_8 phys16_8 phys32_4
  rw [lift_or_stage 4096 stageMask16_4 1008
        (phys16_4 x)
        (phys16_4 (x + 64 * stepConst))
        (phys16_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage16_4 x]
  rw [stage16_4 (x + 64 * stepConst)]

theorem stage16_16 (x : Nat) :
    orStage stageMask16_16 1008 (phys16_16 x) =
      phys32_8 x := by
  unfold stageMask16_16 phys16_16 phys32_8
  rw [lift_or_stage 8192 stageMask16_8 1008
        (phys16_8 x)
        (phys16_8 (x + 128 * stepConst))
        (phys16_8_lt x) (by decide) (by decide) (by decide)]
  rw [stage16_8 x]
  rw [stage16_8 (x + 128 * stepConst)]

def stageMask32_2 : Nat := lowMask 32
def stageMask32_4 : Nat :=
  maskW 4096 stageMask32_2
def stageMask32_8 : Nat :=
  maskW 8192 stageMask32_4

theorem stage32_2 (x : Nat) :
    orStage stageMask32_2 2016 (phys32_2 x) =
      phys64_1 x := by
  unfold stageMask32_2 phys32_2 phys64_1 dense64
  exact gatherPair_eq 32 (dense32 x)
    (dense32 (x + 32 * stepConst))
    (by decide) (dense32_lt x)
    (dense32_lt (x + 32 * stepConst))

theorem stage32_4 (x : Nat) :
    orStage stageMask32_4 2016 (phys32_4 x) =
      phys64_2 x := by
  unfold stageMask32_4 phys32_4 phys64_2
  rw [lift_or_stage 4096 stageMask32_2 2016
        (phys32_2 x)
        (phys32_2 (x + 64 * stepConst))
        (phys32_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage32_2 x]
  rw [stage32_2 (x + 64 * stepConst)]

theorem stage32_8 (x : Nat) :
    orStage stageMask32_8 2016 (phys32_8 x) =
      phys64_4 x := by
  unfold stageMask32_8 phys32_8 phys64_4
  rw [lift_or_stage 8192 stageMask32_4 2016
        (phys32_4 x)
        (phys32_4 (x + 128 * stepConst))
        (phys32_4_lt x) (by decide) (by decide) (by decide)]
  rw [stage32_4 x]
  rw [stage32_4 (x + 128 * stepConst)]

def stageMask64_2 : Nat := lowMask 64
def stageMask64_4 : Nat :=
  maskW 8192 stageMask64_2

theorem stage64_2 (x : Nat) :
    orStage stageMask64_2 4032 (phys64_2 x) =
      phys128_1 x := by
  unfold stageMask64_2 phys64_2 phys128_1 dense128
  exact gatherPair_eq 64 (dense64 x)
    (dense64 (x + 64 * stepConst))
    (by decide) (dense64_lt x)
    (dense64_lt (x + 64 * stepConst))

theorem stage64_4 (x : Nat) :
    orStage stageMask64_4 4032 (phys64_4 x) =
      phys128_2 x := by
  unfold stageMask64_4 phys64_4 phys128_2
  rw [lift_or_stage 8192 stageMask64_2 4032
        (phys64_2 x)
        (phys64_2 (x + 128 * stepConst))
        (phys64_2_lt x) (by decide) (by decide) (by decide)]
  rw [stage64_2 x]
  rw [stage64_2 (x + 128 * stepConst)]

def stageMask128_2 : Nat := lowMask 128

theorem stage128_2 (x : Nat) :
    orStage stageMask128_2 8064 (phys128_2 x) =
      phys256_1 x := by
  unfold stageMask128_2 phys128_2 phys256_1 dense256
  exact gatherPair_eq 128 (dense128 x)
    (dense128 (x + 128 * stepConst))
    (by decide) (dense128_lt x)
    (dense128_lt (x + 128 * stepConst))


def compactTree (q0 : Nat) : Nat :=
  let q1 := orStage stageMask1_256 63 q0
  let q2 := orStage stageMask2_128 126 q1
  let q3 := orStage stageMask4_64 252 q2
  let q4 := orStage stageMask8_32 504 q3
  let q5 := orStage stageMask16_16 1008 q4
  let q6 := orStage stageMask32_8 2016 q5
  let q7 := orStage stageMask64_4 4032 q6
  let q8 := orStage stageMask128_2 8064 q7
  q8

theorem compactTree_bits256 (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    compactTree (bits256 x) = dense256 x := by
  rw [bits256_phys x h]
  simp only [compactTree]
  rw [stage1_256 x]
  rw [stage2_128 x]
  rw [stage4_64 x]
  rw [stage8_32 x]
  rw [stage16_16 x]
  rw [stage32_8 x]
  rw [stage64_4 x]
  rw [stage128_2 x]
  rfl

end WideGather



namespace WideDenseByte

open GenericPack
open WideHierarchy
open WideGather
open Submission

set_option maxRecDepth 1048576
set_option maxHeartbeats 1000000

theorem dense1_eq_nat (x : Nat) :
    dense1 x = mixBit31Nat x := by
  unfold dense1
  exact bits1_eq_mix x

theorem dense8_eq_pack8Nat (x : Nat) :
    dense8 x = pack8Nat x := by
  unfold dense8 dense4 dense2 packW pack8Nat
  rw [dense1_eq_nat, dense1_eq_nat, dense1_eq_nat, dense1_eq_nat,
      dense1_eq_nat, dense1_eq_nat, dense1_eq_nat, dense1_eq_nat]
  simp only [Nat.shiftLeft_eq]
  have h2 : x + 2 * stepConst = x + stepConst + stepConst := by omega
  have h3 : x + 2 * stepConst + 1 * stepConst =
      x + stepConst + stepConst + stepConst := by omega
  have h4 : x + 4 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst := by omega
  have h5 : x + 4 * stepConst + 1 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst + stepConst := by omega
  have h6 : x + 4 * stepConst + 2 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst := by omega
  have h7 : x + 4 * stepConst + 2 * stepConst + 1 * stepConst =
      x + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst + stepConst := by omega
  rw [h7, h6, h5, h4, h3, h2]
  simp only [Nat.one_mul, Nat.pow_succ, Nat.pow_zero, Nat.mul_one]
  omega

end WideDenseByte



namespace DenseByteSequence

open GenericPack
open WideGather
open WideDenseByte
open Submission

def advanceBytes : Nat → Nat → Nat
  | x, 0 => x
  | x, n + 1 => advanceBytes (advance8 x) n

def packBytesNat : Nat → Nat → Nat
  | _, 0 => 0
  | x, n + 1 => pack8Nat x + 256 * packBytesNat (advance8 x) n

theorem advanceBytes_eq (x n : Nat) :
    advanceBytes x n = x + (8 * n) * stepConst := by
  induction n generalizing x with
  | zero =>
      simp [advanceBytes]
  | succ n ih =>
      simp only [advanceBytes]
      rw [ih (advance8 x), advance8_eq_swar]
      unfold stepConst
      omega

theorem mixBit31Nat_lt2 (x : Nat) :
    mixBit31Nat x < 2 := by
  unfold mixBit31Nat
  exact Nat.mod_lt _ (by decide)

end DenseByteSequence



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



namespace WideFast

open GenericPack
open GenericMix
open WideHierarchy
open WideGather
open WideLow254
open Submission

set_option maxRecDepth 1048576
set_option exponentiation.threshold 20000
set_option maxHeartbeats 4000000

def wideMask : Nat := 0xffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff00000000ffffffff

theorem wideMask_eq : wideMask = mask256 := by decide

theorem laneOnes_eq :
    WideProgression.laneOnes256 = ones256 := by decide

theorem state8_match (x : Nat) :
    state8 x = WideProgression.state8 x := by
  unfold WideProgression.state8
  exact state8_eq_octState x

theorem state16_match (x : Nat) :
    state16 x = WideProgression.state16 x := by
  unfold state16 WideProgression.state16
  rw [state8_match x, state8_match (x + 8 * stepConst)]

theorem state32_match (x : Nat) :
    state32 x = WideProgression.state32 x := by
  unfold state32 WideProgression.state32
  rw [state16_match x, state16_match (x + 16 * stepConst)]

theorem state64_match (x : Nat) :
    state64 x = WideProgression.state64 x := by
  unfold state64 WideProgression.state64
  rw [state32_match x, state32_match (x + 32 * stepConst)]

theorem state128_match (x : Nat) :
    state128 x = WideProgression.state128 x := by
  unfold state128 WideProgression.state128
  rw [state64_match x, state64_match (x + 64 * stepConst)]

theorem state256_match (x : Nat) :
    state256 x = WideProgression.state256 x := by
  unfold state256 WideProgression.state256
  rw [state128_match x, state128_match (x + 128 * stepConst)]

def fastProgression (x : Nat) : Nat :=
  WideProgression.wideProgression x

theorem fastProgression_eq (x : Nat) :
    fastProgression x = state256 x := by
  unfold fastProgression
  rw [WideProgression.wideProgression_eq_state256]
  exact (state256_match x).symm

def fastRaw (x : Nat) : Nat :=
  mixCore wideMask (fastProgression x)

theorem fastRaw_eq (x : Nat) :
    fastRaw x = raw256 x := by
  unfold fastRaw raw256
  rw [wideMask_eq, fastProgression_eq]

def fastSparse (x : Nat) : Nat :=
  shrMask WideProgression.laneOnes256 31 (fastRaw x)

theorem fastSparse_eq (x : Nat) :
    fastSparse x = bits256 x := by
  unfold fastSparse bits256
  rw [laneOnes_eq, fastRaw_eq]

def compactMask1 : Nat := 0x300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003000000000000000000000000000000030000000000000000000000000000000300000000000000000000000000000003
def compactMask2 : Nat := 0xf000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f000000000000000000000000000000000000000000000000000000000000000f
def compactMask3 : Nat := 0xff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ff
def compactMask4 : Nat := 0xffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffff
def compactMask5 : Nat := 0xffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffff
def compactMask6 : Nat := 0xffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffff
def compactMask7 : Nat := 0xffffffffffffffffffffffffffffffff000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000ffffffffffffffffffffffffffffffff
def compactMask8 : Nat := 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff

theorem compactMask1_eq : compactMask1 = stageMask1_256 := by decide
theorem compactMask2_eq : compactMask2 = stageMask2_128 := by decide
theorem compactMask3_eq : compactMask3 = stageMask4_64 := by decide
theorem compactMask4_eq : compactMask4 = stageMask8_32 := by decide
theorem compactMask5_eq : compactMask5 = stageMask16_16 := by decide
theorem compactMask6_eq : compactMask6 = stageMask32_8 := by decide
theorem compactMask7_eq : compactMask7 = stageMask64_4 := by decide
theorem compactMask8_eq : compactMask8 = stageMask128_2 := by decide

def compactFast (q0 : Nat) : Nat :=
  let q1 := orStage compactMask1 63 q0
  let q2 := orStage compactMask2 126 q1
  let q3 := orStage compactMask3 252 q2
  let q4 := orStage compactMask4 504 q3
  let q5 := orStage compactMask5 1008 q4
  let q6 := orStage compactMask6 2016 q5
  let q7 := orStage compactMask7 4032 q6
  let q8 := orStage compactMask8 8064 q7
  q8

theorem compactFast_eq (q : Nat) :
    compactFast q = compactTree q := by
  simp only [compactFast, compactTree]
  rw [compactMask1_eq, compactMask2_eq, compactMask3_eq, compactMask4_eq,
      compactMask5_eq, compactMask6_eq, compactMask7_eq, compactMask8_eq]

def fastPayload (x : Nat) : Nat :=
  compactFast (fastSparse x) &&& (2 ^ 254 - 1)

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
  exact dense256_low254_eq_tail x

def fastInit (seed : Nat) : Nat :=
  let x := seed + 3 * stepConst
  1 + 4 * fastPayload x

theorem fastInit_ca_eq (n : Nat) :
    fastInit (caSeed n) = initPackedByteNat (caSeed n) := by
  have hs : caSeed n < 2 ^ 32 := by
    unfold caSeed
    exact Nat.and_lt_two_pow n (by decide)
  have hb :
      caSeed n + 3 * stepConst + 255 * stepConst < 2 ^ 64 := by
    have hc : (2 ^ 32 - 1) + 258 * stepConst < 2 ^ 64 := by
      unfold stepConst
      decide
    omega
  dsimp [fastInit, initPackedByteNat]
  rw [fastPayload_eq (caSeed n + 3 * stepConst) hb]

theorem fastInit_v27_eq (n : Nat) :
    fastInit (caSeed n) = initPackedOctContracted (caSeed n) := by
  calc
    fastInit (caSeed n) = initPackedByteNat (caSeed n) := fastInit_ca_eq n
    _ = initPackedSWAR8 (caSeed n) := (initPackedSWAR8_eq n).symm
    _ = initPackedOctContracted (caSeed n) := (initPackedOctContracted_eq (caSeed n)).symm

end WideFast



namespace Submission

def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (WideFast.fastInit (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n

end Submission
