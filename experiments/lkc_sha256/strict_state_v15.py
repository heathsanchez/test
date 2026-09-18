#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

runpy.run_path(str(ROOT / "packed_machine_v11.py"))
src = (OUT / "Submission_machine_v11.lean").read_text()

plain_rounds = r'''def roundsPackedK : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      roundsPackedK n (ks >>> 32) (machineRound st (ks &&& w32))
'''
strict_rounds = r'''def roundsPackedK : Nat → Nat → Nat → Nat
  | 0, _, st => st
  | n + 1, ks, st =>
      let next := machineRound st (ks &&& w32)
      match next with
      | 0 => roundsPackedK n (ks >>> 32) 0
      | m + 1 => roundsPackedK n (ks >>> 32) (m + 1)
'''

plain_iter = r'''def iterPackedSha : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d => iterPackedSha n (packedShaStep d)
'''
strict_iter = r'''def iterPackedSha : Nat → Nat → Nat
  | 0, d => d
  | n + 1, d =>
      let next := packedShaStep d
      match next with
      | 0 => iterPackedSha n 0
      | m + 1 => iterPackedSha n (m + 1)
'''

variants = {
    "outer": src.replace(plain_iter, strict_iter),
    "inner": src.replace(plain_rounds, strict_rounds),
    "both": src.replace(plain_rounds, strict_rounds).replace(plain_iter, strict_iter),
}

for name, text in variants.items():
    if text == src:
        raise RuntimeError(f"strictness rewrite did not apply for {name}")
    p = OUT / f"Submission_strict_{name}_v15.lean"
    p.write_text(text)
    print(f"generated {p} bytes={len(text.encode())}")
