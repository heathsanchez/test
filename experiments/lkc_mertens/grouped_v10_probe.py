#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

/-- Sum the quotient blocks i..j having the same floor(n/i). -/
def mertensGroupedRow (n : Nat) : Nat → Nat → Array Int → Int → Int
  | 0, _, _, acc => 1 - acc
  | fuel + 1, i, vals, acc =>
      if n < i then 1 - acc
      else
        let q := n / i
        let j := n / q
        let coeff : Int := Int.ofNat (j - i + 1)
        let acc' := acc + coeff * vals.getD q 0
        mertensGroupedRow n fuel (j + 1) vals acc'

/-- Build M(0), M(1), ..., M(n) once.  For k>=1,
M(k) = 1 - sum_{i=2..k} M(floor(k/i)); equal quotients are grouped. -/
def mertensGroupedBuild : Nat → Nat → Array Int → Array Int
  | 0, _, vals => vals
  | fuel + 1, k, vals =>
      if k = 0 then
        mertensGroupedBuild fuel 1 (vals.push 0)
      else
        let mk := mertensGroupedRow k (k + 1) 2 vals 0
        mertensGroupedBuild fuel (k + 1) (vals.push mk)

def impl (n : Nat) : Int :=
  (mertensGroupedBuild (n + 1) 0 #[]).getD n 0

end Submission
'''
p=OUT/"Submission_v10_grouped_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
