#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_fullproof_v21.py"))
src=(OUT/"Submission_algebra_v21_proof.lean").read_text()

cuts={
  "V_valid":"theorem iterDigest_congr_of_invariant",
  "G_generic":"theorem iterAlgebra_correct",
  "S_special":"theorem impl_correct",
}
for name,marker in cuts.items():
    i=src.index(marker)
    text=src[:i]+"\nend Submission\n"
    p=OUT/f"V23_{name}.lean"
    p.write_text(text)
    print(name,len(text.encode()))
p=OUT/"V23_I_impl.lean"
p.write_text(src)
print("I_impl",len(src.encode()))
