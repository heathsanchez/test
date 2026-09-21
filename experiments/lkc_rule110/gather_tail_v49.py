#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = (ROOT / "Submission_v47.lean").read_text()

old = '''def fastPayload (x : Nat) : Nat :=
  compactFast (fastSparse x) &&& (2 ^ 254 - 1)

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
  exact dense256_low254_eq_tail x
'''

new = '''def compactFast254 (q0 : Nat) : Nat :=
  let q1 := orStage compactMask1 63 q0
  let q2 := orStage compactMask2 126 q1
  let q3 := orStage compactMask3 252 q2
  let q4 := orStage compactMask4 504 q3
  let q5 := orStage compactMask5 1008 q4
  let q6 := orStage compactMask6 2016 q5
  let q7 := orStage compactMask7 4032 q6
  let q8 := orStage (2 ^ 254 - 1) 8064 q7
  q8

theorem compactFast254_eq (q : Nat) :
    compactFast254 q = compactFast q &&& (2 ^ 254 - 1) := by
  simp only [compactFast254, compactFast]
  unfold orStage
  rw [Nat.and_assoc]
  have hm : compactMask8 &&& (2 ^ 254 - 1) = (2 ^ 254 - 1) := by
    unfold compactMask8
    decide
  rw [hm]

def fastPayload (x : Nat) : Nat :=
  compactFast254 (fastSparse x)

theorem fastPayload_eq (x : Nat)
    (h : x + 255 * stepConst < 2 ^ 64) :
    fastPayload x = packByteTailNat x 31 := by
  unfold fastPayload
  rw [compactFast254_eq]
  rw [fastSparse_eq, compactFast_eq, compactTree_bits256 x h]
  exact dense256_low254_eq_tail x
'''

if old not in BASE:
    raise SystemExit("fastPayload source pattern not found")
out = BASE.replace(old, new, 1)
out_path = ROOT / "generated" / "Submission_v49.lean"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(out)
print(f"generated {out_path} bytes={len(out)}")
