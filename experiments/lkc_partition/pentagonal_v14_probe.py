#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

/-- Euler's generalized pentagonal recurrence, evaluated against a compact
array of already-computed partition values. This is an operational probe; the
universal bridge to partAux is proved only if the representation wins. -/
def pentagonalRow (k : Nat) : Nat → Nat → Array Int → Int → Int
  | 0, _, _, acc => acc
  | fuel + 1, j, vals, acc =>
      let g1 := j * (3 * j - 1) / 2
      if k < g1 then acc
      else
        let g2 := j * (3 * j + 1) / 2
        let term :=
          vals.getD (k - g1) 0 +
            (if g2 ≤ k then vals.getD (k - g2) 0 else 0)
        let acc' := if j % 2 = 1 then acc + term else acc - term
        pentagonalRow k fuel (j + 1) vals acc'

def partitionPentagonalBuild : Nat → Nat → Array Int → Array Int
  | 0, _, vals => vals
  | fuel + 1, k, vals =>
      if k = 0 then
        partitionPentagonalBuild fuel 1 (vals.push 1)
      else
        let pk := pentagonalRow k (k + 1) 1 vals 0
        partitionPentagonalBuild fuel (k + 1) (vals.push pk)

def impl (n : Nat) : Nat :=
  Int.toNat ((partitionPentagonalBuild (n + 1) 0 #[]).getD n 0)

end Submission
'''
p=OUT/"Submission_v14_pentagonal_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
