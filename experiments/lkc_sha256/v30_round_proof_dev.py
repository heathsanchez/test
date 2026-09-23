#!/usr/bin/env python3
# rerun after t2 validity threading
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"mulrotate_v30_proof.py"))
src=(OUT/"Submission_mulrotate_v30_proof.lean").read_text()
cut=src.index("def Window.toList")
text=src[:cut]+"\nend Submission\n"
p=OUT/"V30RoundProofDev.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
