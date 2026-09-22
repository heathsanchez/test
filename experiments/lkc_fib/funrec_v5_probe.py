#!/usr/bin/env python3
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
text=r'''import Spec

namespace Submission

def fdStep (recur : Nat → Nat × Nat) (n : Nat) : Nat × Nat :=
  if n = 0 then (0, 1)
  else
    match recur (n / 2) with
    | (a, b) =>
      let even := a * (2 * b - a)
      let odd := b * b + a * a
      if n % 2 = 0 then (even, odd) else (odd, even + odd)

def fdFun (fuel : Nat) : Nat → Nat × Nat :=
  Nat.rec (fun _ => (0, 1)) (fun _ recur => fdStep recur) fuel

def impl (n : Nat) : Nat := (fdFun n n).1

end Submission
'''
p=OUT/"Submission_v5_funrec_probe.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
