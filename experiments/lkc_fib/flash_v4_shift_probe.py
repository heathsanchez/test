#!/usr/bin/env python3
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"bitwise_v2.py"))
src=(OUT/"Submission_v2.lean").read_text()
old='''def fdBit : Nat → Nat → Nat × Nat
  | 0, _ => (0, 1)
  | _ + 1, 0 => (0, 1)
  | fuel + 1, n + 1 =>
    match fdBit fuel ((n + 1) >>> 1) with
    | (a, b) =>
      if ((n + 1) &&& 1) = 0 then
        (a * (2 * b - a), b * b + a * a)
      else
        (b * b + a * a, a * (2 * b - a) + (b * b + a * a))
'''
new='''def fdBit : Nat → Nat → Nat × Nat
  | 0, _ => (0, 1)
  | _ + 1, 0 => (0, 1)
  | fuel + 1, n + 1 =>
    match fdBit fuel ((n + 1) >>> 1) with
    | (a, b) =>
      if ((n + 1) &&& 1) = 0 then
        (a * ((b <<< 1) - a), b * b + a * a)
      else
        (b * b + a * a, a * ((b <<< 1) - a) + (b * b + a * a))
'''
if old not in src: raise SystemExit("V2 fdBit missing")
src=src.replace(old,new,1)
prefix=src.split("theorem half_eq",1)[0]
out=prefix+'''def impl (n : Nat) : Nat := (fdBit n n).1

end Submission
'''
p=OUT/"Submission_v4_shift_probe.lean";p.write_text(out)
print(f"generated {p} bytes={len(out.encode())}")
