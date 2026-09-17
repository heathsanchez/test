#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v54.lean").read_text()
mod16 = hex((1 << 1024) - (1 << 16))

old = '''def fastPayload (x : Nat) : Nat :=
  compactMod8 (fastSparse x) &&& payloadMask254

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactMod8_bits256 x h]
  exact dense256_low254_eq_tail x
'''

new = f'''def gatherMod16 : Nat := {mod16}

theorem pow1024_mod16 : (2 ^ 1024) % gatherMod16 = 2 ^ 16 := by decide
theorem pow2048_mod16 : (2 ^ 2048) % gatherMod16 = 2 ^ 32 := by decide
theorem pow4096_mod16 : (2 ^ 4096) % gatherMod16 = 2 ^ 64 := by decide
theorem pow8192_mod16 : (2 ^ 8192) % gatherMod16 = 2 ^ 128 := by decide

theorem phys16_1_mod16 (x : Nat) :
    phys16_1 x % gatherMod16 = dense16 x := by
  unfold phys16_1
  apply Nat.mod_eq_of_lt
  exact Nat.lt_of_lt_of_le (dense16_lt x) (by decide)

theorem phys16_2_mod16 (x : Nat) :
    phys16_2 x % gatherMod16 = dense32 x := by
  unfold phys16_2 dense32
  exact packW_mod_collapse gatherMod16 1024 16
    (phys16_1 x) (phys16_1 (x + 16 * stepConst))
    (dense16 x) (dense16 (x + 16 * stepConst))
    (phys16_1_mod16 x)
    (phys16_1_mod16 (x + 16 * stepConst))
    pow1024_mod16
    (Nat.lt_of_lt_of_le (dense32_lt x) (by decide))

theorem phys16_4_mod16 (x : Nat) :
    phys16_4 x % gatherMod16 = dense64 x := by
  unfold phys16_4 dense64
  exact packW_mod_collapse gatherMod16 2048 32
    (phys16_2 x) (phys16_2 (x + 32 * stepConst))
    (dense32 x) (dense32 (x + 32 * stepConst))
    (phys16_2_mod16 x)
    (phys16_2_mod16 (x + 32 * stepConst))
    pow2048_mod16
    (Nat.lt_of_lt_of_le (dense64_lt x) (by decide))

theorem phys16_8_mod16 (x : Nat) :
    phys16_8 x % gatherMod16 = dense128 x := by
  unfold phys16_8 dense128
  exact packW_mod_collapse gatherMod16 4096 64
    (phys16_4 x) (phys16_4 (x + 64 * stepConst))
    (dense64 x) (dense64 (x + 64 * stepConst))
    (phys16_4_mod16 x)
    (phys16_4_mod16 (x + 64 * stepConst))
    pow4096_mod16
    (Nat.lt_of_lt_of_le (dense128_lt x) (by decide))

theorem phys16_16_mod16 (x : Nat) :
    phys16_16 x % gatherMod16 = dense256 x := by
  unfold phys16_16 dense256
  exact packW_mod_collapse gatherMod16 8192 128
    (phys16_8 x) (phys16_8 (x + 128 * stepConst))
    (dense128 x) (dense128 (x + 128 * stepConst))
    (phys16_8_mod16 x)
    (phys16_8_mod16 (x + 128 * stepConst))
    pow8192_mod16
    (Nat.lt_of_lt_of_le (dense256_lt x) (by decide))

def compactMod16 (q0 : Nat) : Nat :=
  let q1 := orStage compactMask1 63 q0
  let q2 := orStage compactMask2 126 q1
  let q3 := orStage compactMask3 252 q2
  let q4 := orStage compactMask4 504 q3
  q4 % gatherMod16

theorem compactMod16_bits256 (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    compactMod16 (bits256 x) = dense256 x := by
  simp only [compactMod16]
  rw [compactMask1_eq, compactMask2_eq, compactMask3_eq, compactMask4_eq]
  rw [bits256_phys x h]
  rw [stage1_256 x]
  rw [stage2_128 x]
  rw [stage4_64 x]
  rw [stage8_32 x]
  exact phys16_16_mod16 x

def fastPayload (x : Nat) : Nat :=
  compactMod16 (fastSparse x) &&& payloadMask254

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactMod16_bits256 x h]
  exact dense256_low254_eq_tail x
'''

if old not in base:
    raise SystemExit("v54 fastPayload block not found")
out = base.replace(old, new, 1)
path = ROOT / "generated" / "Submission_v59.lean"
path.write_text(out)
print(f"generated {path} bytes={len(out)}")
