#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"shift_v3.py"))
src=(OUT/"Submission_v3.lean").read_text()

old='''def impl (n : Nat) : Int := resultantFromPolyMul (polyOfShift n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  rw [impl, polyOfShift_eq, resultantFromPolyMul_eq]
  exact (discSpec_eq_resultant n).symm
'''
new='''/-- Diagnostic only: keep the normal Brown PRS and delete the Bareiss
fallback. A zero result therefore marks an input that actually needs fallback. -/
def resultantNormalOnly (p : List Int) : Int :=
  let derivative := derivHL p
  match normalResultantGoMul 25 true p derivative with
  | some resultant => resultant
  | none => 0

def impl (n : Nat) : Int := resultantNormalOnly (polyOfShift n)
'''
if old not in src:
    raise SystemExit("V3 final block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v5_normal_only_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
