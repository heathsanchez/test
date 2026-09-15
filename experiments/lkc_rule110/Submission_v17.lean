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

/-! V17 base: numeric bit extraction via mod 2. -/

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

/-! V16: fuse byte production and progression advance so x1..x8 are shared. -/

def packByteTailShared : Nat → Nat → Nat
  | x, 0 =>
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
  | x, n + 1 =>
      let x1 := x + stepConst
      let x2 := x1 + stepConst
      let x3 := x2 + stepConst
      let x4 := x3 + stepConst
      let x5 := x4 + stepConst
      let x6 := x5 + stepConst
      let x7 := x6 + stepConst
      let x8 := x7 + stepConst
      mixBit31Nat x +
      2   * mixBit31Nat x1 +
      4   * mixBit31Nat x2 +
      8   * mixBit31Nat x3 +
      16  * mixBit31Nat x4 +
      32  * mixBit31Nat x5 +
      64  * mixBit31Nat x6 +
      128 * mixBit31Nat x7 +
      256 * packByteTailShared x8 n

theorem packByteTailShared_eq (x n : Nat) :
    packByteTailShared x n = packByteTailNat x n := by
  induction n generalizing x with
  | zero =>
      unfold packByteTailShared packByteTailNat pack6Nat
      rfl
  | succ n ih =>
      unfold packByteTailShared packByteTailNat pack8Nat advance8
      simp only [ih]

def initPackedShared (seed : Nat) : Nat :=
  1 + 4 * packByteTailShared (seed + 3 * stepConst) 31

theorem initPackedShared_eq (seed : Nat) :
    initPackedShared seed = initPackedByteNat seed := by
  unfold initPackedShared initPackedByteNat
  rw [packByteTailShared_eq]

def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (initPackedShared (caSeed n))

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
  rw [biterFast_eq, initPackedShared_eq, initPackedByteNat_eq, initPackedByte_eq, initPackedFastBit_eq, initPackedFast_eq]
  show biter (caSteps n) (encodeRow (initRowFor (caSeed n))) =
    encodeRow (iterRow (caSteps n) (initRowFor (caSeed n)))
  exact (iter_eq (caSteps n) (initRowFor (caSeed n))
    (by simp [initRowFor, ruleWidth])).symm

end Submission
