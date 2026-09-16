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

new = '''def gatherMod4 : Nat :=
  0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff0

theorem pow256_mod4 : (2 ^ 256) % gatherMod4 = 2 ^ 4 := by decide
theorem pow512_mod4 : (2 ^ 512) % gatherMod4 = 2 ^ 8 := by decide
theorem pow1024_mod4 : (2 ^ 1024) % gatherMod4 = 2 ^ 16 := by decide
theorem pow2048_mod4 : (2 ^ 2048) % gatherMod4 = 2 ^ 32 := by decide
theorem pow4096_mod4 : (2 ^ 4096) % gatherMod4 = 2 ^ 64 := by decide
theorem pow8192_mod4 : (2 ^ 8192) % gatherMod4 = 2 ^ 128 := by decide

theorem packW_mod4_collapse
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

theorem packW_mod4_transport
    (m w k p q dp dq : Nat)
    (hp : p % m = dp)
    (hq : q % m = dq)
    (hdp : dp < m)
    (hpow : (2 ^ w) % m = 2 ^ k) :
    packW w p q % m = packW k dp dq % m := by
  simp only [packW, Nat.shiftLeft_eq]
  calc
    (p + q * 2 ^ w) % m =
        (p % m + (q * 2 ^ w) % m) % m := Nat.add_mod _ _ _
    _ = (dp + (dq * 2 ^ k) % m) % m := by
      rw [Nat.mul_mod, hp, hq, hpow]
    _ = (dp + dq * 2 ^ k) % m := by
      symm
      calc
        (dp + dq * 2 ^ k) % m =
            (dp % m + (dq * 2 ^ k) % m) % m := Nat.add_mod _ _ _
        _ = (dp + (dq * 2 ^ k) % m) % m := by
          rw [Nat.mod_eq_of_lt hdp]

theorem phys4_1_mod4 (x : Nat) :
    phys4_1 x % gatherMod4 = dense4 x := by
  unfold phys4_1
  apply Nat.mod_eq_of_lt
  exact Nat.lt_of_lt_of_le (dense4_lt x) (by decide)

theorem phys4_2_mod4 (x : Nat) :
    phys4_2 x % gatherMod4 = dense8 x := by
  unfold phys4_2 dense8
  exact packW_mod4_collapse gatherMod4 256 4
    (phys4_1 x) (phys4_1 (x + 4 * stepConst))
    (dense4 x) (dense4 (x + 4 * stepConst))
    (phys4_1_mod4 x)
    (phys4_1_mod4 (x + 4 * stepConst))
    pow256_mod4
    (Nat.lt_of_lt_of_le (dense8_lt x) (by decide))

theorem phys4_4_mod4 (x : Nat) :
    phys4_4 x % gatherMod4 = dense16 x := by
  unfold phys4_4 dense16
  exact packW_mod4_collapse gatherMod4 512 8
    (phys4_2 x) (phys4_2 (x + 8 * stepConst))
    (dense8 x) (dense8 (x + 8 * stepConst))
    (phys4_2_mod4 x)
    (phys4_2_mod4 (x + 8 * stepConst))
    pow512_mod4
    (Nat.lt_of_lt_of_le (dense16_lt x) (by decide))

theorem phys4_8_mod4 (x : Nat) :
    phys4_8 x % gatherMod4 = dense32 x := by
  unfold phys4_8 dense32
  exact packW_mod4_collapse gatherMod4 1024 16
    (phys4_4 x) (phys4_4 (x + 16 * stepConst))
    (dense16 x) (dense16 (x + 16 * stepConst))
    (phys4_4_mod4 x)
    (phys4_4_mod4 (x + 16 * stepConst))
    pow1024_mod4
    (Nat.lt_of_lt_of_le (dense32_lt x) (by decide))

theorem phys4_16_mod4 (x : Nat) :
    phys4_16 x % gatherMod4 = dense64 x := by
  unfold phys4_16 dense64
  exact packW_mod4_collapse gatherMod4 2048 32
    (phys4_8 x) (phys4_8 (x + 32 * stepConst))
    (dense32 x) (dense32 (x + 32 * stepConst))
    (phys4_8_mod4 x)
    (phys4_8_mod4 (x + 32 * stepConst))
    pow2048_mod4
    (Nat.lt_of_lt_of_le (dense64_lt x) (by decide))

theorem phys4_32_mod4 (x : Nat) :
    phys4_32 x % gatherMod4 = dense128 x := by
  unfold phys4_32 dense128
  exact packW_mod4_collapse gatherMod4 4096 64
    (phys4_16 x) (phys4_16 (x + 64 * stepConst))
    (dense64 x) (dense64 (x + 64 * stepConst))
    (phys4_16_mod4 x)
    (phys4_16_mod4 (x + 64 * stepConst))
    pow4096_mod4
    (Nat.lt_of_lt_of_le (dense128_lt x) (by decide))

theorem phys4_64_mod4 (x : Nat) :
    phys4_64 x % gatherMod4 = dense256 x % gatherMod4 := by
  unfold phys4_64 dense256
  exact packW_mod4_transport gatherMod4 8192 128
    (phys4_32 x) (phys4_32 (x + 128 * stepConst))
    (dense128 x) (dense128 (x + 128 * stepConst))
    (phys4_32_mod4 x)
    (phys4_32_mod4 (x + 128 * stepConst))
    (Nat.lt_of_lt_of_le (dense128_lt x) (by decide))
    pow8192_mod4

theorem mod4_exact_of_not_small
    (d : Nat) (hd : d < 2 ^ 256)
    (hsmall : ¬ d % gatherMod4 < 16) :
    d % gatherMod4 = d := by
  have hsum : gatherMod4 + 16 = 2 ^ 256 := by decide
  have h16m : 16 < gatherMod4 := by decide
  have hdm : d < gatherMod4 := by
    by_contra hnot
    have hge : gatherMod4 ≤ d := by omega
    have hsub : d - gatherMod4 < 16 := by omega
    have hsubm : d - gatherMod4 < gatherMod4 := by omega
    have hmod : d % gatherMod4 = d - gatherMod4 := by
      rw [Nat.mod_eq_sub_mod hge]
      exact Nat.mod_eq_of_lt hsubm
    apply hsmall
    rw [hmod]
    exact hsub
  exact Nat.mod_eq_of_lt hdm

def compactMod4Guard (q0 : Nat) : Nat :=
  let q1 := orStage compactMask1 63 q0
  let q2 := orStage compactMask2 126 q1
  let r := q2 % gatherMod4
  if r < 16 then
    let q3 := orStage compactMask3 252 q2
    let q4 := orStage compactMask4 504 q3
    let q5 := orStage compactMask5 1008 q4
    let q6 := orStage compactMask6 2016 q5
    let q7 := orStage compactMask7 4032 q6
    let q8 := orStage compactMask8 8064 q7
    q8
  else r

theorem compactMod4Guard_bits256 (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    compactMod4Guard (bits256 x) = dense256 x := by
  simp only [compactMod4Guard]
  rw [compactMask1_eq, compactMask2_eq]
  rw [bits256_phys x h]
  rw [stage1_256 x]
  rw [stage2_128 x]
  have hmod := phys4_64_mod4 x
  by_cases hs : phys4_64 x % gatherMod4 < 16
  · rw [if_pos hs]
    rw [compactMask3_eq, compactMask4_eq, compactMask5_eq,
        compactMask6_eq, compactMask7_eq, compactMask8_eq]
    rw [stage4_64 x]
    rw [stage8_32 x]
    rw [stage16_16 x]
    rw [stage32_8 x]
    rw [stage64_4 x]
    rw [stage128_2 x]
    rfl
  · rw [if_neg hs]
    have hdsmall : ¬ dense256 x % gatherMod4 < 16 := by
      intro hd
      apply hs
      rw [hmod]
      exact hd
    calc
      phys4_64 x % gatherMod4 = dense256 x % gatherMod4 := hmod
      _ = dense256 x := mod4_exact_of_not_small
        (dense256 x) (dense256_lt x) hdsmall

def fastPayload (x : Nat) : Nat :=
  compactMod4Guard (fastSparse x) &&& payloadMask254

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactMod4Guard_bits256 x h]
  exact dense256_low254_eq_tail x
'''

if old not in base:
    raise SystemExit("fastPayload block not found")
out = base.replace(old, new, 1)

path = ROOT / "generated" / "Submission_v55.lean"
path.write_text(out)
print(f"generated {path} bytes={len(out)}")
