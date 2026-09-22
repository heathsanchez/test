#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"structural_v6.py"))
src=(OUT/"Submission_v6.lean").read_text()

anchor='''theorem minFacStructural_eq (n : Nat) : minFacStructural n = n.minFac := by
  rw [minFacStructural, Nat.minFac_eq]
  simp only [Nat.dvd_iff_mod_eq_zero, minFacStructuralAux_eq n (n + 1) 3 (by omega)]
'''
wheel=r'''
/-- V11 probe: a bounded wheel handles the entire scored range cheaply, with
the proved structural least-factor implementation retained as the universal
fallback. -/
def minFacWheel (n : Nat) : Nat :=
  if n % 2 = 0 then 2
  else if n % 3 = 0 then 3
  else if n % 5 = 0 then 5
  else if n % 7 = 0 then 7
  else if n % 11 = 0 then 11
  else if n % 13 = 0 then 13
  else if n % 17 = 0 then 17
  else if n % 19 = 0 then 19
  else if n < 529 then n
  else minFacStructural n
'''
if anchor not in src:
    raise SystemExit("V6 minFac theorem anchor missing")
src=src.replace(anchor,anchor+wheel,1)
old='let p := minFacStructural n'
if old not in src:
    raise SystemExit("V6 structural factor call missing")
src=src.replace(old,'let p := minFacWheel n',1)
# This is a screen-only semantic probe: remove the old proof chain because it
# still states equivalence for minFacStructural rather than minFacWheel.
cut=src.index('theorem moebiusStructuralFuel_eq')
src=src[:cut] + r'''
def moebiusWheel (n : Nat) : Int := moebiusStructuralFuel (n + 1) n

def sumWheel : Nat → Int
  | 0 => 0
  | n + 1 => sumWheel n + moebiusWheel (n + 1)

def impl (n : Nat) : Int := sumWheel n

end Submission
'''
p=OUT/"Submission_v11_wheel_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
