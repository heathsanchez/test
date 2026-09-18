#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"base32_machine_v12.py"))
src=(OUT/"Submission_machine_v12.lean").read_text()

plain_rounds=r'''def roundsPackedKBase : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      roundsPackedKBase n (ks / base32) (machineRoundB st (ks % base32))
'''
strict_rounds=r'''def roundsPackedKBase : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      let next := machineRoundB st (ks % base32)
      match next with
      | 0 => roundsPackedKBase n (ks / base32) 0
      | m + 1 => roundsPackedKBase n (ks / base32) (m + 1)
'''

plain_iter=r'''def iterPackedShaB : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedShaB n (packedShaStepB d)
'''
strict_iter=r'''def iterPackedShaB : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d =>
      let next := packedShaStepB d
      match next with
      | 0 => iterPackedShaB n 0
      | m + 1 => iterPackedShaB n (m + 1)
'''

text=src.replace(plain_rounds,strict_rounds).replace(plain_iter,strict_iter)
if text==src or strict_rounds not in text or strict_iter not in text:
    raise RuntimeError("strict base32 rewrite did not apply")
p=OUT/"Submission_base32_strict_v16.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
