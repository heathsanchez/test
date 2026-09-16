#!/usr/bin/env python3
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
subprocess.run(["python3", str(ROOT / "payload_mask_v51.py")], check=True)
base = (ROOT / "generated" / "Submission_v51.lean").read_text()

MOD = (1 << 1024) - (1 << 16)
MOD_HEX = hex(MOD)

anchor = '''theorem compactMask8_eq : compactMask8 = stageMask128_2 := by decide
'''
if anchor not in base:
    raise SystemExit("compact mask anchor not found")

block = f'''

-- V52: after four ordinary gather stages, the 256 output bits live as
-- sixteen 16-bit blocks spaced 1024 bits apart.  Since
--   2^1024 = 2^16 (mod 2^1024 - 2^16),
-- one remainder operation concatenates all sixteen blocks at once.
def gatherMod16 : Nat := {MOD_HEX}

theorem gatherMod16_eq : gatherMod16 = 2 ^ 1024 - 2 ^ 16 := by decide

theorem pow1024_mod_gather16 :
    2 ^ 1024 % gatherMod16 = 2 ^ 16 := by decide

theorem pow2048_mod_gather16 :
    2 ^ 2048 % gatherMod16 = 2 ^ 32 := by decide

theorem pow4096_mod_gather16 :
    2 ^ 4096 % gatherMod16 = 2 ^ 64 := by decide

theorem pow8192_mod_gather16 :
    2 ^ 8192 % gatherMod16 = 2 ^ 128 := by decide

theorem packW_mod_gather16
    (w k a b da db : Nat)
    (ha : a % gatherMod16 = da)
    (hb : b % gatherMod16 = db)
    (hp : 2 ^ w % gatherMod16 = 2 ^ k)
    (hsum : da + db * 2 ^ k < gatherMod16) :
    packW w a b % gatherMod16 = da + db * 2 ^ k := by
  unfold packW
  simp only [Nat.shiftLeft_eq]
  rw [Nat.add_mod, Nat.mul_mod, ha, hb, hp]
  have hprod : db * 2 ^ k < gatherMod16 := by omega
  rw [Nat.mod_eq_of_lt hprod]
  exact Nat.mod_eq_of_lt hsum

theorem phys16_1_mod_gather16 (x : Nat) :
    phys16_1 x % gatherMod16 = dense16 x := by
  unfold phys16_1
  apply Nat.mod_eq_of_lt
  have hd := dense16_lt x
  have hm : 2 ^ 16 < gatherMod16 := by decide
  omega

theorem phys16_2_mod_gather16 (x : Nat) :
    phys16_2 x % gatherMod16 = dense32 x := by
  unfold phys16_2
  have hsum :
      dense16 x + dense16 (x + 16 * stepConst) * 2 ^ 16 < gatherMod16 := by
    have hd := dense32_lt x
    have hm : 2 ^ 32 < gatherMod16 := by decide
    have heq :
        dense16 x + dense16 (x + 16 * stepConst) * 2 ^ 16 = dense32 x := by
      simp [dense32, packW, Nat.shiftLeft_eq, Nat.mul_comm]
    rw [heq]
    exact Nat.lt_trans hd hm
  have h := packW_mod_gather16 1024 16
      (phys16_1 x) (phys16_1 (x + 16 * stepConst))
      (dense16 x) (dense16 (x + 16 * stepConst))
      (phys16_1_mod_gather16 x)
      (phys16_1_mod_gather16 (x + 16 * stepConst))
      pow1024_mod_gather16 hsum
  simpa [dense32, packW, Nat.shiftLeft_eq, Nat.mul_comm] using h

theorem phys16_4_mod_gather16 (x : Nat) :
    phys16_4 x % gatherMod16 = dense64 x := by
  unfold phys16_4
  have hsum :
      dense32 x + dense32 (x + 32 * stepConst) * 2 ^ 32 < gatherMod16 := by
    have hd := dense64_lt x
    have hm : 2 ^ 64 < gatherMod16 := by decide
    have heq :
        dense32 x + dense32 (x + 32 * stepConst) * 2 ^ 32 = dense64 x := by
      simp [dense64, packW, Nat.shiftLeft_eq, Nat.mul_comm]
    rw [heq]
    exact Nat.lt_trans hd hm
  have h := packW_mod_gather16 2048 32
      (phys16_2 x) (phys16_2 (x + 32 * stepConst))
      (dense32 x) (dense32 (x + 32 * stepConst))
      (phys16_2_mod_gather16 x)
      (phys16_2_mod_gather16 (x + 32 * stepConst))
      pow2048_mod_gather16 hsum
  simpa [dense64, packW, Nat.shiftLeft_eq, Nat.mul_comm] using h

theorem phys16_8_mod_gather16 (x : Nat) :
    phys16_8 x % gatherMod16 = dense128 x := by
  unfold phys16_8
  have hsum :
      dense64 x + dense64 (x + 64 * stepConst) * 2 ^ 64 < gatherMod16 := by
    have hd := dense128_lt x
    have hm : 2 ^ 128 < gatherMod16 := by decide
    have heq :
        dense64 x + dense64 (x + 64 * stepConst) * 2 ^ 64 = dense128 x := by
      simp [dense128, packW, Nat.shiftLeft_eq, Nat.mul_comm]
    rw [heq]
    exact Nat.lt_trans hd hm
  have h := packW_mod_gather16 4096 64
      (phys16_4 x) (phys16_4 (x + 64 * stepConst))
      (dense64 x) (dense64 (x + 64 * stepConst))
      (phys16_4_mod_gather16 x)
      (phys16_4_mod_gather16 (x + 64 * stepConst))
      pow4096_mod_gather16 hsum
  simpa [dense128, packW, Nat.shiftLeft_eq, Nat.mul_comm] using h

theorem phys16_16_mod_gather16 (x : Nat) :
    phys16_16 x % gatherMod16 = dense256 x := by
  unfold phys16_16
  have hsum :
      dense128 x + dense128 (x + 128 * stepConst) * 2 ^ 128 < gatherMod16 := by
    have hd := dense256_lt x
    have hm : 2 ^ 256 < gatherMod16 := by decide
    have heq :
        dense128 x + dense128 (x + 128 * stepConst) * 2 ^ 128 = dense256 x := by
      simp [dense256, packW, Nat.shiftLeft_eq, Nat.mul_comm]
    rw [heq]
    exact Nat.lt_trans hd hm
  have h := packW_mod_gather16 8192 128
      (phys16_8 x) (phys16_8 (x + 128 * stepConst))
      (dense128 x) (dense128 (x + 128 * stepConst))
      (phys16_8_mod_gather16 x)
      (phys16_8_mod_gather16 (x + 128 * stepConst))
      pow8192_mod_gather16 hsum
  simpa [dense256, packW, Nat.shiftLeft_eq, Nat.mul_comm] using h

def compactMod16 (q0 : Nat) : Nat :=
  let q1 := orStage compactMask1 63 q0
  let q2 := orStage compactMask2 126 q1
  let q3 := orStage compactMask3 252 q2
  let q4 := orStage compactMask4 504 q3
  q4 % gatherMod16

theorem compactMod16_bits256 (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    compactMod16 (bits256 x) = dense256 x := by
  rw [bits256_phys x h]
  simp only [compactMod16]
  rw [compactMask1_eq, compactMask2_eq, compactMask3_eq, compactMask4_eq]
  rw [stage1_256 x]
  rw [stage2_128 x]
  rw [stage4_64 x]
  rw [stage8_32 x]
  exact phys16_16_mod_gather16 x
'''

out = base.replace(anchor, anchor + block, 1)

old_def = '''def fastPayload (x : Nat) : Nat :=
  compactFast (fastSparse x) &&& payloadMask254
'''
new_def = '''def fastPayload (x : Nat) : Nat :=
  compactMod16 (fastSparse x) &&& payloadMask254
'''
if old_def not in out:
    raise SystemExit("V51 fastPayload definition not found")
out = out.replace(old_def, new_def, 1)

old_proof = '''  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
  exact dense256_low254_eq_tail x
'''
new_proof = '''  rw [payloadMask254_eq]
  rw [fastSparse_eq, compactMod16_bits256 x h]
  exact dense256_low254_eq_tail x
'''
if old_proof not in out:
    raise SystemExit("V51 fastPayload proof pattern not found")
out = out.replace(old_proof, new_proof, 1)

p = ROOT / "generated" / "Submission_v52.lean"
p.parent.mkdir(parents=True, exist_ok=True)
p.write_text(out)
print(f"generated {p} bytes={len(out)} mod_bits={MOD.bit_length()}")
