#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"full_v5.py"))
src=(OUT/"Submission_v5.lean").read_text()

start=src.index("def impl (n : Nat) : Nat :=")
end=src.index("\nend Submission", start)
old=src[start:end]

new=r'''/-- V7 representation probe: the row index is reconstructed from the
remaining-row counter, so execution carries only the used-column mask and a
structural Nat counter instead of allocating/traversing List.range d. -/
def permanentSparseState : Nat → Nat → Nat → Nat → Nat
  | 0, _dimension, _seed, _used => 1
  | rows + 1, dimension, seed, used =>
      let i := dimension - (rows + 1)
      permanentSparseStep dimension seed i
        (permanentSparseState rows dimension seed) used

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparseState d d s 0
'''
src=src[:start]+new+src[end:]
p=OUT/"Submission_v7_state_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
