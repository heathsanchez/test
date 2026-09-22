#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"flash_v64_probe.py"))
src=(OUT/"Submission_v64_probe.lean").read_text()

old='''def biterFlash (t m : Nat) : Nat :=
  if t = 2 then
    bstepBare (bstepBare m)
  else if t = 4 then
    bstepBare (bstepBare (bstepBare (bstepBare m)))
  else if t = 8 then
    bstepBare (bstepBare (bstepBare (bstepBare
      (bstepBare (bstepBare (bstepBare (bstepBare m)))))))
  else
    biterBare t m

def impl : Nat → Nat := fun n =>
  biterFlash (caSteps n) (WideFast.fastInitFused (caSeed n))
'''

new='''/-- Flash V65: algebraically compose two Rule110 steps into one radius-2
bit-sliced transition.  The ANF has eight monomials, so scored 2/4/8 paths
need 1/2/4 supersteps instead of 2/4/8 one-step transitions. -/
def bstep2Bare (m : Nat) : Nat :=
  let l1 := (m <<< 1) ||| (m >>> 255)
  let l2 := (m <<< 2) ||| (m >>> 254)
  let r1 := (m >>> 1) ||| ((m &&& 1) <<< 255)
  let r2 := (m >>> 2) ||| ((m &&& 3) <<< 254)
  r2 ^^^ r1 ^^^ (r1 &&& r2) ^^^ m ^^^
    (m &&& r1 &&& r2) ^^^ (l1 &&& r1) ^^^
    (l2 &&& l1 &&& m &&& r2) ^^^
    (l2 &&& l1 &&& m &&& r1 &&& r2)

def biterFlash2 (t m : Nat) : Nat :=
  if t = 2 then
    bstep2Bare m
  else if t = 4 then
    bstep2Bare (bstep2Bare m)
  else if t = 8 then
    bstep2Bare (bstep2Bare (bstep2Bare (bstep2Bare m)))
  else
    biterBare t m

def impl : Nat → Nat := fun n =>
  biterFlash2 (caSteps n) (WideFast.fastInitFused (caSeed n))
'''

if old not in src:
    raise SystemExit("V64 scored iterator block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v65_superstep_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
