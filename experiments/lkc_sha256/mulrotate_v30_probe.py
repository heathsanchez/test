#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"algebra_v24_probe.py"))
src=(OUT/"Submission_algebra_v24_probe.lean").read_text()

old='''def smallSigma0Fast (x : Nat) : Nat :=
  rotrRaw x 7 ^^^ rotrRaw x 18 ^^^ (x >>> 3)

def smallSigma1Fast (x : Nat) : Nat :=
  rotrRaw x 17 ^^^ rotrRaw x 19 ^^^ (x >>> 10)

def bigSigma0Fast (x : Nat) : Nat :=
  rotrRaw x 2 ^^^ rotrRaw x 13 ^^^ rotrRaw x 22

def bigSigma1Fast (x : Nat) : Nat :=
  rotrRaw x 6 ^^^ rotrRaw x 11 ^^^ rotrRaw x 25
'''
new='''/-- Duplicate a bounded 32-bit word at offsets 0 and 32 in one Nat multiplication.
Low 32 bits of (dup32 x >>> n) are ROTR n x. -/
def dup32 (x : Nat) : Nat := x * 4294967297

def smallSigma0Fast (x : Nat) : Nat :=
  let z := dup32 x
  (z >>> 7) ^^^ (z >>> 18) ^^^ (x >>> 3)

def smallSigma1Fast (x : Nat) : Nat :=
  let z := dup32 x
  (z >>> 17) ^^^ (z >>> 19) ^^^ (x >>> 10)

def bigSigma0Fast (x : Nat) : Nat :=
  let z := dup32 x
  (z >>> 2) ^^^ (z >>> 13) ^^^ (z >>> 22)

def bigSigma1Fast (x : Nat) : Nat :=
  let z := dup32 x
  (z >>> 6) ^^^ (z >>> 11) ^^^ (z >>> 25)
'''
if old not in src: raise SystemExit("sigma block missing")
src=src.replace(old,new,1)
src=src.replace('def impl (n : Nat) : Nat :=','def implMulRotate (n : Nat) : Nat :=',1)
# diagnostic source does not need a universal proof
p=OUT/"Submission_mulrotate_v30_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
