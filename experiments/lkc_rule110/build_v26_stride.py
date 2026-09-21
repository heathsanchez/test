from pathlib import Path

src = Path("experiments/lkc_rule110/Submission_v25.lean").read_text()

marker = """def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (initPackedOctProgression (caSeed n))"""

block = r'''/-! V26: contract the duplicated scalar progression to one verified stride add. -/

def octStride : Nat := 0x4f1bbcdc8

theorem octStride_eq : octStride = 8 * stepConst := by
  decide

theorem advance8_eq_stride (x : Nat) :
    advance8 x = x + octStride := by
  rw [advance8_eq_swar, octStride_eq]

def packOctTailStride : Nat → Nat → Nat → Nat
  | _, x, 0 => pack6SWAR8 x
  | p, x, n + 1 =>
      mix8Packed p + 256 * packOctTailStride (advanceOct p) (x + octStride) n

theorem packOctTailStride_eq (x n : Nat) :
    packOctTailStride (octState x) x n = packOctTail (octState x) x n := by
  induction n generalizing x with
  | zero =>
      rfl
  | succ n ih =>
      simp only [packOctTailStride, packOctTail]
      rw [advanceOct_state, advance8_eq_stride, ih]

def initPackedOctStride (seed : Nat) : Nat :=
  let x := seed + 3 * stepConst
  1 + 4 * packOctTailStride (octState x) x 31

theorem initPackedOctStride_eq (seed : Nat) :
    initPackedOctStride seed = initPackedOctProgression seed := by
  unfold initPackedOctStride initPackedOctProgression
  dsimp
  rw [packOctTailStride_eq]

'''

assert marker in src
src = src.replace(marker, block + """def impl : Nat → Nat := fun n =>
  biterFast (caSteps n) (initPackedOctStride (caSeed n))""")

old = "rw [biterFast_eq, initPackedOctProgression_eq, initPackedSWAR8_eq, initPackedByteNat_eq, initPackedByte_eq, initPackedFastBit_eq, initPackedFast_eq]"
new = "rw [biterFast_eq, initPackedOctStride_eq, initPackedOctProgression_eq, initPackedSWAR8_eq, initPackedByteNat_eq, initPackedByte_eq, initPackedFastBit_eq, initPackedFast_eq]"
assert old in src
src = src.replace(old, new)

Path("experiments/lkc_rule110/Submission_v26.generated.lean").write_text(src)
