#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated";OUT.mkdir(parents=True,exist_ok=True)
text=r'''import Spec

namespace Submission

def clearBitIfSet (bits i : Nat) : Nat :=
  if bits.testBit i then bits ^^^ (1 <<< i) else bits

def clearMultiples : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, bits => bits
  | fuel + 1, n, p, m, bits =>
      if n < m then bits
      else clearMultiples fuel n p (m + p) (clearBitIfSet bits m)

def sieveLoop : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, bits => bits
  | fuel + 1, n, p, bits =>
      if n < p * p then bits
      else
        let bits' :=
          if bits.testBit p then clearMultiples (n + 1) n p (p * p) bits
          else bits
        sieveLoop fuel n (p + 1) bits'

def primeBits (n : Nat) : Nat :=
  if n < 2 then 0
  else
    let bits := ((1 <<< (n + 1)) - 1) ^^^ 3
    sieveLoop (n + 1) n 2 bits

def countBits : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | fuel + 1, i, bits =>
      (if bits.testBit i then 1 else 0) + countBits fuel (i + 1) bits

def impl (n : Nat) : Nat :=
  if n < 2 then 0 else countBits (n - 1) 2 (primeBits n)

end Submission
'''
p=OUT/"Submission_v5_bitset_probe.lean";p.write_text(text);print(f"generated {p} bytes={len(text.encode())}")
