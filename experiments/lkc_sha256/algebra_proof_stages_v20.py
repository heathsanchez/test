#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"algebra_fullproof_v20.py"))
src=(OUT/"Submission_algebra_v20_proof.lean").read_text()

markers={
  "A_round":"def Window.toList",
  "B_schedule":"def streamWords",
  "C_stream":"def fastStepNoZipProof",
  "D_nozip":"theorem streamWordsK_eq_fastSchedule",
  "E_kbridge":"theorem fastStepAlgebra_eq_nozip",
  "F_eq":"theorem fastStepAlgebra_correct",
  "G_step":"theorem fastStepAlgebra_fun",
}
for name,marker in markers.items():
    i=src.index(marker)
    text=src[:i] + "\nend Submission\n"
    p=OUT/f"V20_{name}.lean"
    p.write_text(text)
    print(name,len(text.encode()))
