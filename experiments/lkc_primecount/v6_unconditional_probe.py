#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def clearBitIfSet (bits i : Nat) : Nat :=
  if bits.testBit i then bits ^^^ (1 <<< i) else bits

def clearMultiples : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _, _, _, bits => bits
  | fuel + 1, n, p, m, bits =>
      if n < m then bits
      else clearMultiples fuel n p (m + p) (clearBitIfSet bits m)

/-- Interaction-unit runtime: keep the packed representation, but remove the
semantic dependency on the current bit of p. Every p up to sqrt(n) performs its
p^2 progression clearing.  This is deliberately proof-friendly. -/
def sieveLoopAll : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, bits => bits
  | fuel + 1, n, p, bits =>
      if n < p * p then bits
      else
        sieveLoopAll fuel n (p + 1)
          (clearMultiples (n + 1) n p (p * p) bits)

def primeBitsAll (n : Nat) : Nat :=
  if n < 2 then 0
  else sieveLoopAll (n + 1) n 2 (((1 <<< (n + 1)) - 1) ^^^ 3)

def countBits : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | fuel + 1, i, bits =>
      (if bits.testBit i then 1 else 0) + countBits fuel (i + 1) bits

def impl (n : Nat) : Nat :=
  if n < 2 then 0 else countBits (n - 1) 2 (primeBitsAll n)

end Submission
'''
p=OUT/"Submission_v6_unconditional_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
