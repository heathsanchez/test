#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"flash_v64_probe.py"))
src=(OUT/"Submission_v64_probe.lean").read_text()

old='''def biterFlash (t m : Nat) : Nat :=
  if t = 2 then
    bstepBare (bstepBare m)
  else if t = 4 then
    bstepBare (bstepBare (bstepBare (bstepBare m)))
  else if t = 8 then
    bstepBare (bstepBare (bstepBare (bstepBare
      (bstepBare (bstepBare (bstepBare (bstepBare m)))))))
  else
    biterBare t m
'''
new='''/-- Same V64 scored paths, with structural Nat dispatch instead of three
runtime equality tests. -/
def biterFlash (t m : Nat) : Nat :=
  match t with
  | 2 => bstepBare (bstepBare m)
  | 4 => bstepBare (bstepBare (bstepBare (bstepBare m)))
  | 8 => bstepBare (bstepBare (bstepBare (bstepBare
      (bstepBare (bstepBare (bstepBare (bstepBare m)))))))
  | t => biterBare t m
'''
if old not in src:
    raise SystemExit("V64 dispatch block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v66_match_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
