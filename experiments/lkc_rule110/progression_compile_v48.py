#!/usr/bin/env python3
from pathlib import Path
import argparse
import re

ROOT = Path(__file__).resolve().parent
BASE = (ROOT / "Submission_v47.lean").read_text()
STEP = 0x9e3779b9

# laneIndex256 = sum i * 2^(64*i), i=0..255.
BIAS = sum((i * STEP) << (64 * i) for i in range(256))
BIAS_HEX = hex(BIAS)


def bias_block(use_replicate: bool) -> str:
    repl = ""
    rhs = "x * laneOnes256"
    if use_replicate:
        repl = r'''
def replicate256 (x : Nat) : Nat :=
  let x2 := x + (x <<< 64)
  let x4 := x2 + (x2 <<< 128)
  let x8 := x4 + (x4 <<< 256)
  let x16 := x8 + (x8 <<< 512)
  let x32 := x16 + (x16 <<< 1024)
  let x64 := x32 + (x32 <<< 2048)
  let x128 := x64 + (x64 <<< 4096)
  x128 + (x128 <<< 8192)

theorem replicate256_eq (x : Nat) :
    replicate256 x = x * laneOnes256 := by
  unfold replicate256 laneOnes256
  simp only [Nat.shiftLeft_eq]
  omega
'''
        rhs = "replicate256 x"
    return f'''def progressionBias256 : Nat := {BIAS_HEX}

theorem progressionBias256_eq :
    progressionBias256 = stepConst * laneIndex256 := by
  decide
{repl}
def wideProgression (x : Nat) : Nat :=
  {rhs} + progressionBias256
'''


def transform(variant: str) -> str:
    out = BASE
    old = r'''def wideProgression (x : Nat) : Nat :=
  x * laneOnes256 + stepConst * laneIndex256
'''
    if old not in out:
        raise SystemExit("wideProgression source pattern not found")
    out = out.replace(old, bias_block(variant == "replicate"), 1)

    old_proof = r'''theorem wideProgression_eq_state256 (x : Nat) :
    wideProgression x = state256 x := by
  unfold wideProgression laneOnes256 laneIndex256
'''
    new_proof = r'''theorem wideProgression_eq_state256 (x : Nat) :
    wideProgression x = state256 x := by
  unfold wideProgression
  rw [progressionBias256_eq]
'''
    if variant == "replicate":
        new_proof += "  rw [replicate256_eq]\n"
    new_proof += "  unfold laneOnes256 laneIndex256\n"
    if old_proof not in out:
        raise SystemExit("wideProgression proof pattern not found")
    out = out.replace(old_proof, new_proof, 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", choices=("bias", "replicate"))
    ap.add_argument("output", type=Path)
    args = ap.parse_args()
    out = transform(args.variant)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(out)
    print(f"generated {args.variant}: {args.output} bytes={len(out)} bias_bits={BIAS.bit_length()}")


if __name__ == "__main__":
    main()
