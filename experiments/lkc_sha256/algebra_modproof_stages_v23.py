#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_modproof_v23.py"))
src=(OUT/"Submission_algebra_v20_modproof.lean").read_text()

markers={
  "A_round":"def Window.toList",
  "B_kbridge":"theorem fastStepAlgebra_eq_nozip",
  "C_finish":"theorem fastStepAlgebra_correct",
  "D_correct":"theorem fastStepAlgebra_fun",
  "E_fun":"theorem impl_correct",
}
for name,marker in markers.items():
    i=src.index(marker)
    text=src[:i] + "\nend Submission\n"
    p=OUT/f"ModProof_{name}.lean"
    p.write_text(text)
    print(name,len(text.encode()))
