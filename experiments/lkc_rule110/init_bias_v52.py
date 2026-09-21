#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
base = (ROOT / "generated" / "Submission_v51.lean").read_text()

old = '''def fastInit (seed : Nat) : Nat :=
  let x := seed + 3 * stepConst
  1 + 4 * fastPayload x
'''
new = '''def initBias3 : Nat := 0x1daa66d2b

theorem initBias3_eq : initBias3 = 3 * stepConst := by decide

def fastInit (seed : Nat) : Nat :=
  let x := seed + initBias3
  1 + 4 * fastPayload x
'''
if old not in base:
    raise SystemExit("fastInit pattern not found")
out = base.replace(old, new, 1)

old_proof = '''  dsimp [fastInit, initPackedByteNat]
  rw [fastPayload_eq (caSeed n + 3 * stepConst) hb]
'''
new_proof = '''  dsimp [fastInit, initPackedByteNat]
  rw [initBias3_eq]
  rw [fastPayload_eq (caSeed n + 3 * stepConst) hb]
'''
if old_proof not in out:
    raise SystemExit("fastInit proof pattern not found")
out = out.replace(old_proof, new_proof, 1)

path = ROOT / "generated" / "Submission_v52.lean"
path.write_text(out)
print(f"generated {path} bytes={len(out)}")
