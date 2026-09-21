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


/-!
V7 compilation: the generated tail has fixed length 254, so compile the
recursor away entirely while preserving the arithmetic-progression and
bit-31 projection learned in V4/V5.
-/

set_option maxHeartbeats 1000000 in
def packMixBit254 (x0 : Nat) : Nat :=
  let x1 := x0 + stepConst
  let x2 := x1 + stepConst
  let x3 := x2 + stepConst
  let x4 := x3 + stepConst
  let x5 := x4 + stepConst
  let x6 := x5 + stepConst
  let x7 := x6 + stepConst
  let x8 := x7 + stepConst
  let x9 := x8 + stepConst
  let x10 := x9 + stepConst
  let x11 := x10 + stepConst
  let x12 := x11 + stepConst
  let x13 := x12 + stepConst
  let x14 := x13 + stepConst
  let x15 := x14 + stepConst
  let x16 := x15 + stepConst
  let x17 := x16 + stepConst
  let x18 := x17 + stepConst
  let x19 := x18 + stepConst
  let x20 := x19 + stepConst
  let x21 := x20 + stepConst
  let x22 := x21 + stepConst
  let x23 := x22 + stepConst
  let x24 := x23 + stepConst
  let x25 := x24 + stepConst
  let x26 := x25 + stepConst
  let x27 := x26 + stepConst
  let x28 := x27 + stepConst
  let x29 := x28 + stepConst
  let x30 := x29 + stepConst
  let x31 := x30 + stepConst
  let x32 := x31 + stepConst
  let x33 := x32 + stepConst
  let x34 := x33 + stepConst
  let x35 := x34 + stepConst
  let x36 := x35 + stepConst
  let x37 := x36 + stepConst
  let x38 := x37 + stepConst
  let x39 := x38 + stepConst
  let x40 := x39 + stepConst
  let x41 := x40 + stepConst
  let x42 := x41 + stepConst
  let x43 := x42 + stepConst
  let x44 := x43 + stepConst
  let x45 := x44 + stepConst
  let x46 := x45 + stepConst
  let x47 := x46 + stepConst
  let x48 := x47 + stepConst
  let x49 := x48 + stepConst
  let x50 := x49 + stepConst
  let x51 := x50 + stepConst
  let x52 := x51 + stepConst
  let x53 := x52 + stepConst
  let x54 := x53 + stepConst
  let x55 := x54 + stepConst
  let x56 := x55 + stepConst
  let x57 := x56 + stepConst
  let x58 := x57 + stepConst
  let x59 := x58 + stepConst
  let x60 := x59 + stepConst
  let x61 := x60 + stepConst
  let x62 := x61 + stepConst
  let x63 := x62 + stepConst
  let x64 := x63 + stepConst
  let x65 := x64 + stepConst
  let x66 := x65 + stepConst
  let x67 := x66 + stepConst
  let x68 := x67 + stepConst
  let x69 := x68 + stepConst
  let x70 := x69 + stepConst
  let x71 := x70 + stepConst
  let x72 := x71 + stepConst
  let x73 := x72 + stepConst
  let x74 := x73 + stepConst
  let x75 := x74 + stepConst
  let x76 := x75 + stepConst
  let x77 := x76 + stepConst
  let x78 := x77 + stepConst
  let x79 := x78 + stepConst
  let x80 := x79 + stepConst
  let x81 := x80 + stepConst
  let x82 := x81 + stepConst
  let x83 := x82 + stepConst
  let x84 := x83 + stepConst
  let x85 := x84 + stepConst
  let x86 := x85 + stepConst
  let x87 := x86 + stepConst
  let x88 := x87 + stepConst
  let x89 := x88 + stepConst
  let x90 := x89 + stepConst
  let x91 := x90 + stepConst
  let x92 := x91 + stepConst
  let x93 := x92 + stepConst
  let x94 := x93 + stepConst
  let x95 := x94 + stepConst
  let x96 := x95 + stepConst
  let x97 := x96 + stepConst
  let x98 := x97 + stepConst
  let x99 := x98 + stepConst
  let x100 := x99 + stepConst
  let x101 := x100 + stepConst
  let x102 := x101 + stepConst
  let x103 := x102 + stepConst
  let x104 := x103 + stepConst
  let x105 := x104 + stepConst
  let x106 := x105 + stepConst
  let x107 := x106 + stepConst
  let x108 := x107 + stepConst
  let x109 := x108 + stepConst
  let x110 := x109 + stepConst
  let x111 := x110 + stepConst
  let x112 := x111 + stepConst
  let x113 := x112 + stepConst
  let x114 := x113 + stepConst
  let x115 := x114 + stepConst
  let x116 := x115 + stepConst
  let x117 := x116 + stepConst
  let x118 := x117 + stepConst
  let x119 := x118 + stepConst
  let x120 := x119 + stepConst
  let x121 := x120 + stepConst
  let x122 := x121 + stepConst
  let x123 := x122 + stepConst
  let x124 := x123 + stepConst
  let x125 := x124 + stepConst
  let x126 := x125 + stepConst
  let x127 := x126 + stepConst
  let x128 := x127 + stepConst
  let x129 := x128 + stepConst
  let x130 := x129 + stepConst
  let x131 := x130 + stepConst
  let x132 := x131 + stepConst
  let x133 := x132 + stepConst
  let x134 := x133 + stepConst
  let x135 := x134 + stepConst
  let x136 := x135 + stepConst
  let x137 := x136 + stepConst
  let x138 := x137 + stepConst
  let x139 := x138 + stepConst
  let x140 := x139 + stepConst
  let x141 := x140 + stepConst
  let x142 := x141 + stepConst
  let x143 := x142 + stepConst
  let x144 := x143 + stepConst
  let x145 := x144 + stepConst
  let x146 := x145 + stepConst
  let x147 := x146 + stepConst
  let x148 := x147 + stepConst
  let x149 := x148 + stepConst
  let x150 := x149 + stepConst
  let x151 := x150 + stepConst
  let x152 := x151 + stepConst
  let x153 := x152 + stepConst
  let x154 := x153 + stepConst
  let x155 := x154 + stepConst
  let x156 := x155 + stepConst
  let x157 := x156 + stepConst
  let x158 := x157 + stepConst
  let x159 := x158 + stepConst
  let x160 := x159 + stepConst
  let x161 := x160 + stepConst
  let x162 := x161 + stepConst
  let x163 := x162 + stepConst
  let x164 := x163 + stepConst
  let x165 := x164 + stepConst
  let x166 := x165 + stepConst
  let x167 := x166 + stepConst
  let x168 := x167 + stepConst
  let x169 := x168 + stepConst
  let x170 := x169 + stepConst
  let x171 := x170 + stepConst
  let x172 := x171 + stepConst
  let x173 := x172 + stepConst
  let x174 := x173 + stepConst
  let x175 := x174 + stepConst
  let x176 := x175 + stepConst
  let x177 := x176 + stepConst
  let x178 := x177 + stepConst
  let x179 := x178 + stepConst
  let x180 := x179 + stepConst
  let x181 := x180 + stepConst
  let x182 := x181 + stepConst
  let x183 := x182 + stepConst
  let x184 := x183 + stepConst
  let x185 := x184 + stepConst
  let x186 := x185 + stepConst
  let x187 := x186 + stepConst
  let x188 := x187 + stepConst
  let x189 := x188 + stepConst
  let x190 := x189 + stepConst
  let x191 := x190 + stepConst
  let x192 := x191 + stepConst
  let x193 := x192 + stepConst
  let x194 := x193 + stepConst
  let x195 := x194 + stepConst
  let x196 := x195 + stepConst
  let x197 := x196 + stepConst
  let x198 := x197 + stepConst
  let x199 := x198 + stepConst
  let x200 := x199 + stepConst
  let x201 := x200 + stepConst
  let x202 := x201 + stepConst
  let x203 := x202 + stepConst
  let x204 := x203 + stepConst
  let x205 := x204 + stepConst
  let x206 := x205 + stepConst
  let x207 := x206 + stepConst
  let x208 := x207 + stepConst
  let x209 := x208 + stepConst
  let x210 := x209 + stepConst
  let x211 := x210 + stepConst
  let x212 := x211 + stepConst
  let x213 := x212 + stepConst
  let x214 := x213 + stepConst
  let x215 := x214 + stepConst
  let x216 := x215 + stepConst
  let x217 := x216 + stepConst
  let x218 := x217 + stepConst
  let x219 := x218 + stepConst
  let x220 := x219 + stepConst
  let x221 := x220 + stepConst
  let x222 := x221 + stepConst
  let x223 := x222 + stepConst
  let x224 := x223 + stepConst
  let x225 := x224 + stepConst
  let x226 := x225 + stepConst
  let x227 := x226 + stepConst
  let x228 := x227 + stepConst
  let x229 := x228 + stepConst
  let x230 := x229 + stepConst
  let x231 := x230 + stepConst
  let x232 := x231 + stepConst
  let x233 := x232 + stepConst
  let x234 := x233 + stepConst
  let x235 := x234 + stepConst
  let x236 := x235 + stepConst
  let x237 := x236 + stepConst
  let x238 := x237 + stepConst
  let x239 := x238 + stepConst
  let x240 := x239 + stepConst
  let x241 := x240 + stepConst
  let x242 := x241 + stepConst
  let x243 := x242 + stepConst
  let x244 := x243 + stepConst
  let x245 := x244 + stepConst
  let x246 := x245 + stepConst
  let x247 := x246 + stepConst
  let x248 := x247 + stepConst
  let x249 := x248 + stepConst
  let x250 := x249 + stepConst
  let x251 := x250 + stepConst
  let x252 := x251 + stepConst
  let x253 := x252 + stepConst
  (if mixBit31 x0 then 1 else 0) + 2 * ((if mixBit31 x1 then 1 else 0) + 2 * ((if mixBit31 x2 then 1 else 0) + 2 * ((if mixBit31 x3 then 1 else 0) + 2 * ((if mixBit31 x4 then 1 else 0) + 2 * ((if mixBit31 x5 then 1 else 0) + 2 * ((if mixBit31 x6 then 1 else 0) + 2 * ((if mixBit31 x7 then 1 else 0) + 2 * ((if mixBit31 x8 then 1 else 0) + 2 * ((if mixBit31 x9 then 1 else 0) + 2 * ((if mixBit31 x10 then 1 else 0) + 2 * ((if mixBit31 x11 then 1 else 0) + 2 * ((if mixBit31 x12 then 1 else 0) + 2 * ((if mixBit31 x13 then 1 else 0) + 2 * ((if mixBit31 x14 then 1 else 0) + 2 * ((if mixBit31 x15 then 1 else 0) + 2 * ((if mixBit31 x16 then 1 else 0) + 2 * ((if mixBit31 x17 then 1 else 0) + 2 * ((if mixBit31 x18 then 1 else 0) + 2 * ((if mixBit31 x19 then 1 else 0) + 2 * ((if mixBit31 x20 then 1 else 0) + 2 * ((if mixBit31 x21 then 1 else 0) + 2 * ((if mixBit31 x22 then 1 else 0) + 2 * ((if mixBit31 x23 then 1 else 0) + 2 * ((if mixBit31 x24 then 1 else 0) + 2 * ((if mixBit31 x25 then 1 else 0) + 2 * ((if mixBit31 x26 then 1 else 0) + 2 * ((if mixBit31 x27 then 1 else 0) + 2 * ((if mixBit31 x28 then 1 else 0) + 2 * ((if mixBit31 x29 then 1 else 0) + 2 * ((if mixBit31 x30 then 1 else 0) + 2 * ((if mixBit31 x31 then 1 else 0) + 2 * ((if mixBit31 x32 then 1 else 0) + 2 * ((if mixBit31 x33 then 1 else 0) + 2 * ((if mixBit31 x34 then 1 else 0) + 2 * ((if mixBit31 x35 then 1 else 0) + 2 * ((if mixBit31 x36 then 1 else 0) + 2 * ((if mixBit31 x37 then 1 else 0) + 2 * ((if mixBit31 x38 then 1 else 0) + 2 * ((if mixBit31 x39 then 1 else 0) + 2 * ((if mixBit31 x40 then 1 else 0) + 2 * ((if mixBit31 x41 then 1 else 0) + 2 * ((if mixBit31 x42 then 1 else 0) + 2 * ((if mixBit31 x43 then 1 else 0) + 2 * ((if mixBit31 x44 then 1 else 0) + 2 * ((if mixBit31 x45 then 1 else 0) + 2 * ((if mixBit31 x46 then 1 else 0) + 2 * ((if mixBit31 x47 then 1 else 0) + 2 * ((if mixBit31 x48 then 1 else 0) + 2 * ((if mixBit31 x49 then 1 else 0) + 2 * ((if mixBit31 x50 then 1 else 0) + 2 * ((if mixBit31 x51 then 1 else 0) + 2 * ((if mixBit31 x52 then 1 else 0) + 2 * ((if mixBit31 x53 then 1 else 0) + 2 * ((if mixBit31 x54 then 1 else 0) + 2 * ((if mixBit31 x55 then 1 else 0) + 2 * ((if mixBit31 x56 then 1 else 0) + 2 * ((if mixBit31 x57 then 1 else 0) + 2 * ((if mixBit31 x58 then 1 else 0) + 2 * ((if mixBit31 x59 then 1 else 0) + 2 * ((if mixBit31 x60 then 1 else 0) + 2 * ((if mixBit31 x61 then 1 else 0) + 2 * ((if mixBit31 x62 then 1 else 0) + 2 * ((if mixBit31 x63 then 1 else 0) + 2 * ((if mixBit31 x64 then 1 else 0) + 2 * ((if mixBit31 x65 then 1 else 0) + 2 * ((if mixBit31 x66 then 1 else 0) + 2 * ((if mixBit31 x67 then 1 else 0) + 2 * ((if mixBit31 x68 then 1 else 0) + 2 * ((if mixBit31 x69 then 1 else 0) + 2 * ((if mixBit31 x70 then 1 else 0) + 2 * ((if mixBit31 x71 then 1 else 0) + 2 * ((if mixBit31 x72 then 1 else 0) + 2 * ((if mixBit31 x73 then 1 else 0) + 2 * ((if mixBit31 x74 then 1 else 0) + 2 * ((if mixBit31 x75 then 1 else 0) + 2 * ((if mixBit31 x76 then 1 else 0) + 2 * ((if mixBit31 x77 then 1 else 0) + 2 * ((if mixBit31 x78 then 1 else 0) + 2 * ((if mixBit31 x79 then 1 else 0) + 2 * ((if mixBit31 x80 then 1 else 0) + 2 * ((if mixBit31 x81 then 1 else 0) + 2 * ((if mixBit31 x82 then 1 else 0) + 2 * ((if mixBit31 x83 then 1 else 0) + 2 * ((if mixBit31 x84 then 1 else 0) + 2 * ((if mixBit31 x85 then 1 else 0) + 2 * ((if mixBit31 x86 then 1 else 0) + 2 * ((if mixBit31 x87 then 1 else 0) + 2 * ((if mixBit31 x88 then 1 else 0) + 2 * ((if mixBit31 x89 then 1 else 0) + 2 * ((if mixBit31 x90 then 1 else 0) + 2 * ((if mixBit31 x91 then 1 else 0) + 2 * ((if mixBit31 x92 then 1 else 0) + 2 * ((if mixBit31 x93 then 1 else 0) + 2 * ((if mixBit31 x94 then 1 else 0) + 2 * ((if mixBit31 x95 then 1 else 0) + 2 * ((if mixBit31 x96 then 1 else 0) + 2 * ((if mixBit31 x97 then 1 else 0) + 2 * ((if mixBit31 x98 then 1 else 0) + 2 * ((if mixBit31 x99 then 1 else 0) + 2 * ((if mixBit31 x100 then 1 else 0) + 2 * ((if mixBit31 x101 then 1 else 0) + 2 * ((if mixBit31 x102 then 1 else 0) + 2 * ((if mixBit31 x103 then 1 else 0) + 2 * ((if mixBit31 x104 then 1 else 0) + 2 * ((if mixBit31 x105 then 1 else 0) + 2 * ((if mixBit31 x106 then 1 else 0) + 2 * ((if mixBit31 x107 then 1 else 0) + 2 * ((if mixBit31 x108 then 1 else 0) + 2 * ((if mixBit31 x109 then 1 else 0) + 2 * ((if mixBit31 x110 then 1 else 0) + 2 * ((if mixBit31 x111 then 1 else 0) + 2 * ((if mixBit31 x112 then 1 else 0) + 2 * ((if mixBit31 x113 then 1 else 0) + 2 * ((if mixBit31 x114 then 1 else 0) + 2 * ((if mixBit31 x115 then 1 else 0) + 2 * ((if mixBit31 x116 then 1 else 0) + 2 * ((if mixBit31 x117 then 1 else 0) + 2 * ((if mixBit31 x118 then 1 else 0) + 2 * ((if mixBit31 x119 then 1 else 0) + 2 * ((if mixBit31 x120 then 1 else 0) + 2 * ((if mixBit31 x121 then 1 else 0) + 2 * ((if mixBit31 x122 then 1 else 0) + 2 * ((if mixBit31 x123 then 1 else 0) + 2 * ((if mixBit31 x124 then 1 else 0) + 2 * ((if mixBit31 x125 then 1 else 0) + 2 * ((if mixBit31 x126 then 1 else 0) + 2 * ((if mixBit31 x127 then 1 else 0) + 2 * ((if mixBit31 x128 then 1 else 0) + 2 * ((if mixBit31 x129 then 1 else 0) + 2 * ((if mixBit31 x130 then 1 else 0) + 2 * ((if mixBit31 x131 then 1 else 0) + 2 * ((if mixBit31 x132 then 1 else 0) + 2 * ((if mixBit31 x133 then 1 else 0) + 2 * ((if mixBit31 x134 then 1 else 0) + 2 * ((if mixBit31 x135 then 1 else 0) + 2 * ((if mixBit31 x136 then 1 else 0) + 2 * ((if mixBit31 x137 then 1 else 0) + 2 * ((if mixBit31 x138 then 1 else 0) + 2 * ((if mixBit31 x139 then 1 else 0) + 2 * ((if mixBit31 x140 then 1 else 0) + 2 * ((if mixBit31 x141 then 1 else 0) + 2 * ((if mixBit31 x142 then 1 else 0) + 2 * ((if mixBit31 x143 then 1 else 0) + 2 * ((if mixBit31 x144 then 1 else 0) + 2 * ((if mixBit31 x145 then 1 else 0) + 2 * ((if mixBit31 x146 then 1 else 0) + 2 * ((if mixBit31 x147 then 1 else 0) + 2 * ((if mixBit31 x148 then 1 else 0) + 2 * ((if mixBit31 x149 then 1 else 0) + 2 * ((if mixBit31 x150 then 1 else 0) + 2 * ((if mixBit31 x151 then 1 else 0) + 2 * ((if mixBit31 x152 then 1 else 0) + 2 * ((if mixBit31 x153 then 1 else 0) + 2 * ((if mixBit31 x154 then 1 else 0) + 2 * ((if mixBit31 x155 then 1 else 0) + 2 * ((if mixBit31 x156 then 1 else 0) + 2 * ((if mixBit31 x157 then 1 else 0) + 2 * ((if mixBit31 x158 then 1 else 0) + 2 * ((if mixBit31 x159 then 1 else 0) + 2 * ((if mixBit31 x160 then 1 else 0) + 2 * ((if mixBit31 x161 then 1 else 0) + 2 * ((if mixBit31 x162 then 1 else 0) + 2 * ((if mixBit31 x163 then 1 else 0) + 2 * ((if mixBit31 x164 then 1 else 0) + 2 * ((if mixBit31 x165 then 1 else 0) + 2 * ((if mixBit31 x166 then 1 else 0) + 2 * ((if mixBit31 x167 then 1 else 0) + 2 * ((if mixBit31 x168 then 1 else 0) + 2 * ((if mixBit31 x169 then 1 else 0) + 2 * ((if mixBit31 x170 then 1 else 0) + 2 * ((if mixBit31 x171 then 1 else 0) + 2 * ((if mixBit31 x172 then 1 else 0) + 2 * ((if mixBit31 x173 then 1 else 0) + 2 * ((if mixBit31 x174 then 1 else 0) + 2 * ((if mixBit31 x175 then 1 else 0) + 2 * ((if mixBit31 x176 then 1 else 0) + 2 * ((if mixBit31 x177 then 1 else 0) + 2 * ((if mixBit31 x178 then 1 else 0) + 2 * ((if mixBit31 x179 then 1 else 0) + 2 * ((if mixBit31 x180 then 1 else 0) + 2 * ((if mixBit31 x181 then 1 else 0) + 2 * ((if mixBit31 x182 then 1 else 0) + 2 * ((if mixBit31 x183 then 1 else 0) + 2 * ((if mixBit31 x184 then 1 else 0) + 2 * ((if mixBit31 x185 then 1 else 0) + 2 * ((if mixBit31 x186 then 1 else 0) + 2 * ((if mixBit31 x187 then 1 else 0) + 2 * ((if mixBit31 x188 then 1 else 0) + 2 * ((if mixBit31 x189 then 1 else 0) + 2 * ((if mixBit31 x190 then 1 else 0) + 2 * ((if mixBit31 x191 then 1 else 0) + 2 * ((if mixBit31 x192 then 1 else 0) + 2 * ((if mixBit31 x193 then 1 else 0) + 2 * ((if mixBit31 x194 then 1 else 0) + 2 * ((if mixBit31 x195 then 1 else 0) + 2 * ((if mixBit31 x196 then 1 else 0) + 2 * ((if mixBit31 x197 then 1 else 0) + 2 * ((if mixBit31 x198 then 1 else 0) + 2 * ((if mixBit31 x199 then 1 else 0) + 2 * ((if mixBit31 x200 then 1 else 0) + 2 * ((if mixBit31 x201 then 1 else 0) + 2 * ((if mixBit31 x202 then 1 else 0) + 2 * ((if mixBit31 x203 then 1 else 0) + 2 * ((if mixBit31 x204 then 1 else 0) + 2 * ((if mixBit31 x205 then 1 else 0) + 2 * ((if mixBit31 x206 then 1 else 0) + 2 * ((if mixBit31 x207 then 1 else 0) + 2 * ((if mixBit31 x208 then 1 else 0) + 2 * ((if mixBit31 x209 then 1 else 0) + 2 * ((if mixBit31 x210 then 1 else 0) + 2 * ((if mixBit31 x211 then 1 else 0) + 2 * ((if mixBit31 x212 then 1 else 0) + 2 * ((if mixBit31 x213 then 1 else 0) + 2 * ((if mixBit31 x214 then 1 else 0) + 2 * ((if mixBit31 x215 then 1 else 0) + 2 * ((if mixBit31 x216 then 1 else 0) + 2 * ((if mixBit31 x217 then 1 else 0) + 2 * ((if mixBit31 x218 then 1 else 0) + 2 * ((if mixBit31 x219 then 1 else 0) + 2 * ((if mixBit31 x220 then 1 else 0) + 2 * ((if mixBit31 x221 then 1 else 0) + 2 * ((if mixBit31 x222 then 1 else 0) + 2 * ((if mixBit31 x223 then 1 else 0) + 2 * ((if mixBit31 x224 then 1 else 0) + 2 * ((if mixBit31 x225 then 1 else 0) + 2 * ((if mixBit31 x226 then 1 else 0) + 2 * ((if mixBit31 x227 then 1 else 0) + 2 * ((if mixBit31 x228 then 1 else 0) + 2 * ((if mixBit31 x229 then 1 else 0) + 2 * ((if mixBit31 x230 then 1 else 0) + 2 * ((if mixBit31 x231 then 1 else 0) + 2 * ((if mixBit31 x232 then 1 else 0) + 2 * ((if mixBit31 x233 then 1 else 0) + 2 * ((if mixBit31 x234 then 1 else 0) + 2 * ((if mixBit31 x235 then 1 else 0) + 2 * ((if mixBit31 x236 then 1 else 0) + 2 * ((if mixBit31 x237 then 1 else 0) + 2 * ((if mixBit31 x238 then 1 else 0) + 2 * ((if mixBit31 x239 then 1 else 0) + 2 * ((if mixBit31 x240 then 1 else 0) + 2 * ((if mixBit31 x241 then 1 else 0) + 2 * ((if mixBit31 x242 then 1 else 0) + 2 * ((if mixBit31 x243 then 1 else 0) + 2 * ((if mixBit31 x244 then 1 else 0) + 2 * ((if mixBit31 x245 then 1 else 0) + 2 * ((if mixBit31 x246 then 1 else 0) + 2 * ((if mixBit31 x247 then 1 else 0) + 2 * ((if mixBit31 x248 then 1 else 0) + 2 * ((if mixBit31 x249 then 1 else 0) + 2 * ((if mixBit31 x250 then 1 else 0) + 2 * ((if mixBit31 x251 then 1 else 0) + 2 * ((if mixBit31 x252 then 1 else 0) + 2 * ((if mixBit31 x253 then 1 else 0) + 2 * (0))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))))

set_option maxRecDepth 8192 in
theorem packMixBit254_eq (x : Nat) :
    packMixBit254 x = packMixBit x 254 := by
  rfl

def initPackedStraightBit (seed : Nat) : Nat :=
  1 + 4 * packMixBit254 (seed + 3 * stepConst)

theorem initPackedStraightBit_eq (seed : Nat) :
    initPackedStraightBit seed = initPackedFastBit seed := by
  unfold initPackedStraightBit initPackedFastBit
  rw [packMixBit254_eq]

def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (initPackedStraightBit (caSeed n))

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
  rw [biterFast_eq, initPackedStraightBit_eq, initPackedFastBit_eq, initPackedFast_eq]
  show biter (caSteps n) (encodeRow (initRowFor (caSeed n))) =
    encodeRow (iterRow (caSteps n) (initRowFor (caSeed n)))
  exact (iter_eq (caSteps n) (initRowFor (caSeed n))
    (by simp [initRowFor, ruleWidth])).symm

end Submission
