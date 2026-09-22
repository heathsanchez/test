#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"threecompiled_v13.py"))
src=(OUT/"Submission_v13.lean").read_text()

insert=r'''
/-- V14 screen: closed form for the complete {1,2,3}-partition row.
This is equivalent to threeValue; proof is intentionally deferred until the
resource screen establishes value. -/
def threeClosed (m : Nat) : Nat :=
  ((m + 3) * (m + 3) + 3) / 12

def threesRowClosed (n : Nat) : List Nat :=
  (List.range (n + 1)).map threeClosed

def buildAboveThreeClosed : Nat → Nat → List Nat
  | 0, n => threesRowClosed n
  | r + 1, n => nextRowSeeded (r + 3) n (buildAboveThreeClosed r n)

def partitionThreeClosed : Nat → Nat
  | 0 => 1
  | 1 => 1
  | 2 => 2
  | n + 3 => (buildAboveThreeClosed n (n + 3)).getD (n + 3) 0
'''

anchor="def partitionThree : Nat → Nat\n"
if anchor not in src:
    raise SystemExit("V13 partitionThree anchor missing")
src=src.replace(anchor,insert+"\n"+anchor,1)

old='''def impl : Nat → Nat := partitionThree

theorem impl_correct : ∀ n, impl n = partitionSpec n := by
'''
new='''def impl : Nat → Nat := partitionThreeClosed

/-- Screen-only candidate: universal proof follows only if the closed row wins. -/
'''
if old not in src:
    raise SystemExit("V13 final proof anchor missing")
start=src.index(old)
end=src.index("\nend Submission",start)
src=src[:start]+new+src[end:]

p=OUT/"Submission_v14_threeclosed_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
