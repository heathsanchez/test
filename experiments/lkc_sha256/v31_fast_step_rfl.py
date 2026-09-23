#!/usr/bin/env python3
from pathlib import Path
import runpy
ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_scalar_v31_probe.py"))
src=(OUT/"Submission_mulrotate_scalar_v31_probe.lean").read_text()
prefix=src.rsplit("\nend Submission",1)[0]+"\n\n"
proof=r'''
theorem roundsFast_nil_rfl (w : Window) (s : Digest) :
    roundsFast [] w s = s := by
  rfl

theorem roundsFast_cons_rfl (k : Nat) (ks : List Nat)
    (w : Window) (s : Digest) :
    roundsFast (k :: ks) w s =
      roundsFast ks (w.push w.nextFast) (roundFast s k w.x0) := by
  rfl

end Submission
'''
p=OUT/"V31FastStepRflProofDev.lean"
p.write_text(prefix+proof)
print(f"generated {p} bytes={len((prefix+proof).encode())}")
