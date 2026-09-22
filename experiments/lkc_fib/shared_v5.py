#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"bitwise_v2.py"))
src=(OUT/"Submission_v2.lean").read_text().replace("fdBit","fdShared")

old='''def fdShared : Nat → Nat → Nat × Nat
  | 0, _ => (0, 1)
  | _ + 1, 0 => (0, 1)
  | fuel + 1, n + 1 =>
    match fdShared fuel ((n + 1) >>> 1) with
    | (a, b) =>
      if ((n + 1) &&& 1) = 0 then
        (a * (2 * b - a), b * b + a * a)
      else
        (b * b + a * a, a * (2 * b - a) + (b * b + a * a))
'''
new='''/-- V5: share both fast-doubling products before the parity branch.
The old odd branch constructed b*b+a*a twice in the reduction spine. -/
def fdShared : Nat → Nat → Nat × Nat
  | 0, _ => (0, 1)
  | _ + 1, 0 => (0, 1)
  | fuel + 1, n + 1 =>
    match fdShared fuel ((n + 1) >>> 1) with
    | (a, b) =>
      let c := a * (2 * b - a)
      let d := b * b + a * a
      if ((n + 1) &&& 1) = 0 then (c, d) else (d, c + d)
'''
if old not in src:
    raise SystemExit("renamed V2 doubling block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v5_shared.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
