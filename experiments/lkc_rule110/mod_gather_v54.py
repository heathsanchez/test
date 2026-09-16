#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v52.lean").read_text()

old = '''def fastPayload (x : Nat) : Nat :=
  compactFast (fastSparse x) &&& payloadMask254

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
  exact dense256_low254_eq_tail x
'''

new = '''def gatherMod8 : Nat :=
  0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff00

theorem pow512_mod8 : (2 ^ 512) % gatherMod8 = 2 ^ 8 := by decide
theorem pow1024_mod8 : (2 ^ 1024) % gatherMod8 = 2 ^ 16 := by decide
theorem pow2048_mod8 : (2 ^ 2048) % gatherMod8 = 2 ^ 32 := by decide
theorem pow4096_mod8 : (2 ^ 4096) % gatherMod8 = 2 ^ 64 := by decide
theorem pow8192_mod8 : (2 ^ 8192) % gatherMod8 = 2 ^ 128 := by decide

theorem packW_mod_collapse
    (m w k p q dp dq : Nat)
    (hp : p % m = dp)
    (hq : q % m = dq)
    (hpow : (2 ^ w) % m = 2 ^ k)
    (hout : packW k dp dq < m) :
    packW w p q % m = packW k dp dq := by
  simp only [packW, Nat.shiftLeft_eq]
  rw [Nat.add_mod, Nat.mul_mod, hp, hq, hpow]
  have hout' : dp + dq * 2 ^ k < m := by
    simpa [packW, Nat.shiftLeft_eq] using hout
  have hmul : dq * 2 ^ k < m := by omega
  rw [Nat.mod_eq_of_lt hmul]
  exact Nat.mod_eq_of_lt hout'

theorem phys8_1_mod8 (x : Nat) :
    phys8_1 x % gatherMod8 = dense8 x := by
  unfold phys8_1
  apply Nat.mod_eq_of_lt
  exact Nat.lt_of_lt_of_le (dense8_lt x) (by decide)

theorem phys8_2_mod8 (x : Nat) :
    phys8_2 x % gatherMod8 = dense16 x := by
  unfold phys8_2 dense16
  exact packW_mod_collapse gatherMod8 512 8
    (phys8_1 x) (phys8_1 (x + 8 * stepConst))
    (dense8 x) (dense8 (x + 8 * stepConst))
    (phys8_1_mod8 x)
    (phys8_1_mod8 (x + 8 * stepConst))
    pow512_mod8
    (Nat.lt_of_lt_of_le (dense16_lt x) (by decide))

theorem phys8_4_mod8 (x : Nat) :
    phys8_4 x % gatherMod8 = dense32 x := by
  unfold phys8_4 dense32
  exact packW_mod_collapse gatherMod8 1024 16
    (phys8_2 x) (phys8_2 (x + 16 * stepConst))
    (dense16 x) (dense16 (x + 16 * stepConst))
    (phys8_2_mod8 x)
    (phys8_2_mod8 (x + 16 * stepConst))
    pow1024_mod8
    (Nat.lt_of_lt_of_le (dense32_lt x) (by decide))

theorem phys8_8_mod8 (x : Nat) :
    phys8_8 x % gatherMod8 = dense64 x := by
  unfold phys8_8 dense64
  exact packW_mod_collapse gatherMod8 2048 32
    (phys8_4 x) (phys8_4 (x + 32 * stepConst))
    (dense32 x) (dense32 (x + 32 * stepConst))
    (phys8_4_mod8 x)
    (phys8_4_mod8 (x + 32 * stepConst))
    pow2048_mod8
    (Nat.lt_of_lt_of_le (dense64_lt x) (by decide))

theorem phys8_16_mod8 (x : Nat) :
    phys8_16 x % gatherMod8 = dense128 x := by
  unfold phys8_16 dense128
  exact packW_mod_collapse gatherMod8 4096 64
    (phys8_8 x) (phys8_8 (x + 64 * stepConst))
    (dense64 x) (dense64 (x + 64 * stepConst))
    (phys8_8_mod8 x)
    (phys8_8_mod8 (x + 64 * stepConst))
    pow4096_mod8
    (Nat.lt_of_lt_of_le (dense128_lt x) (by decide))

theorem phys8_32_mod8 (x : Nat) :
    phys8_32 x % gatherMod8 = dense256 x := by
  unfold phys8_32 dense256
  exact packW_mod_collapse gatherMod8 8192 128
    (phys8_16 x) (phys8_16 (x + 128 * stepConst))
    (dense128 x) (dense128 (x + 128 * stepConst))
    (phys8_16_mod8 x)
    (phys8_16_mod8 (x + 128 * stepConst))
    pow8192_mod8
    (Nat.lt_of_lt_of_le (dense256_lt x) (by decide))

def compactMod8 (q0 : Nat) : Nat :=
  let q1 := orStage compactMask1 63 q0
  let q2 := orStage compactMask2 126 q1
  let q3 := orStage compactMask3 252 q2
  q3 % gatherMod8

theorem compactMod8_bits256 (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    compactMod8 (bits256 x) = dense256 x := by
  simp only [compactMod8]
  rw [compactMask1_eq, compactMask2_eq, compactMask3_eq]
  rw [bits256_phys x h]
  rw [stage1_256 x]
  rw [stage2_128 x]
  rw [stage4_64 x]
  exact phys8_32_mod8 x

def fastPayload (x : Nat) : Nat :=
  compactMod8 (fastSparse x) &&& payloadMask254

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactMod8_bits256 x h]
  exact dense256_low254_eq_tail x
'''

if old not in base:
    raise SystemExit("fastPayload block not found")
out = base.replace(old, new, 1)

path = ROOT / "generated" / "Submission_v54.lean"
path.write_text(out)
print(f"generated {path} bytes={len(out)}")
