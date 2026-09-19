#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"aligned_wide_v19.py"))
src=(OUT/"Submission_aligned_wide_v19.lean").read_text()

insert_marker="def ivWide : Nat :="
base_run_end=src.index(insert_marker)

def mk_runner(c:int)->str:
    pats=" :: ".join([f"k{i}" for i in range(c)]) + " :: ks"
    lines=[f"def runWideAligned{c} : List Nat → Nat → Nat → Nat",
           f"  | {pats}, s, win =>"]
    prev_s="s"; prev_w="win"
    for i in range(c):
        lines.append(f"      let s{i+1} := roundWideAligned {prev_s} {prev_w} k{i}")
        lines.append(f"      let w{i+1} := roundWindowAligned {prev_w}")
        prev_s=f"s{i+1}"; prev_w=f"w{i+1}"
    lines.append(f"      runWideAligned{c} ks {prev_s} {prev_w}")
    lines.append("  | ks, s, win => runWideAligned ks s win")
    return "\n".join(lines)+"\n\n"

prefix=src[:base_run_end]
suffix=src[base_run_end:]

for c in (4,8):
    text=prefix+mk_runner(c)+suffix
    text=text.replace(
        "let final := runWideAligned K ivWide (initialWindowWide digest)",
        f"let final := runWideAligned{c} K ivWide (initialWindowWide digest)")
    p=OUT/f"Submission_aligned_super{c}_v20.lean"
    p.write_text(text)
    print(f"generated {p} bytes={len(text.encode())}")
