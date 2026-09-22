#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def clearMask (bits mask : Nat) : Nat :=
  bits ^^^ (bits &&& mask)

/-- Bits at start, start+p, ..., through the largest such position ≤ n.
For p>0 this is 2^start * (1 + 2^p + ... + 2^(q*p)). -/
def progressionMask (n p start : Nat) : Nat :=
  if p = 0 || n < start then 0
  else
    let count := (n - start) / p + 1
    let geom := ((1 <<< (p * count)) - 1) / ((1 <<< p) - 1)
    geom <<< start

def sieveLoopBulk : Nat → Nat → Nat → Nat → Nat
  | 0, _, _, bits => bits
  | fuel + 1, n, p, bits =>
      if n < p * p then bits
      else
        let bits' :=
          if bits.testBit p then
            clearMask bits (progressionMask n p (p * p))
          else bits
        sieveLoopBulk fuel n (p + 1) bits'

def primeBitsBulk (n : Nat) : Nat :=
  if n < 2 then 0
  else
    let bits := ((1 <<< (n + 1)) - 1) ^^^ 3
    sieveLoopBulk (n + 1) n 2 bits

def countBits : Nat → Nat → Nat → Nat
  | 0, _, _ => 0
  | fuel + 1, i, bits =>
      (if bits.testBit i then 1 else 0) + countBits fuel (i + 1) bits

def impl (n : Nat) : Nat :=
  if n < 2 then 0 else countBits (n - 1) 2 (primeBitsBulk n)

end Submission
'''
p=OUT/"Submission_v6_bulkmask_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
