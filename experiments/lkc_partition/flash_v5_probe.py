#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def initialRowLinear (n : Nat) : List Nat :=
  1 :: List.replicate n 0

/-- Standard coin-change row recurrence:
    curr[m] = prev[m] + curr[m-part].
The reverse prefix makes the lagged curr entry available without resumming all
multiplicities j for every cell. -/
def nextRowLinearAux (part : Nat) : List Nat → List Nat → List Nat
  | [], outRev => outRev.reverse
  | x :: xs, outRev =>
      let lag := outRev.getD (part - 1) 0
      let y := x + lag
      nextRowLinearAux part xs (y :: outRev)

def nextRowLinear (part : Nat) (prev : List Nat) : List Nat :=
  nextRowLinearAux part prev []

def buildRowsLinear : Nat → Nat → List Nat
  | 0, n => initialRowLinear n
  | k + 1, n => nextRowLinear (k + 1) (buildRowsLinear k n)

def partitionLinear (n : Nat) : Nat :=
  (buildRowsLinear n n).getD n 0

def impl (n : Nat) : Nat := partitionLinear n

end Submission
'''
p=OUT/"Submission_v5_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
