#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"full_v5.py"))
src=(OUT/"Submission_v5.lean").read_text()

old='''def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d) 0
'''
new='''def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d).reverse 0
'''
if old not in src:
    raise SystemExit("V5 impl block missing")
src=src.replace(old,new,1)

# Probe only: row-permutation correctness will be proved if the runtime separator wins.
i=src.index("theorem impl_correct")
src=src[:i]+"end Submission\n"

p=OUT/"Submission_v6_reverse_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
