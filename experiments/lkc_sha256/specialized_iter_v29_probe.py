#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"algebra_v24_probe.py"))
src=(OUT/"Submission_algebra_v24_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]
body=r'''
/-! V29 diagnostic: specialize the outer chain recursor to the exact SHA step. -/
def iterFastAlgebra : Nat → Digest → Digest
  | 0, d => d
  | t + 1, d => iterFastAlgebra t (fastStepAlgebra d)

def implFastIter (n : Nat) : Nat :=
  encodeDigest
    (iterFastAlgebra (sha256Steps n) (seedDigest (sha256Seed n)))

end Submission
'''
p=OUT/"Submission_specialized_iter_v29_probe.lean"
p.write_text(prefix+"\n"+body)
print(f"generated {p} bytes={len(p.read_bytes())}")
