#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"packed_core_v4.py"))
src=(OUT/"Submission_v4.lean").read_text()

def stage(name, marker):
    i=src.index(marker)
    text=src[:i] + "\nend Submission\n"
    p=OUT/f"SHA_{name}.lean"
    p.write_text(text)
    print(f"{name}: {p} bytes={len(text.encode())}")

stage("A_pack", "theorem add32_lt_base")
stage("B_validity", "def packedStep")
stage("C_iteration", "def impl")
