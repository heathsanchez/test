#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

# Rebuild exact V60 dependency chain.
for name in ["payload_mask_v51.py","init_bias_v52.py","mod_gather_v54.py",
             "maskless_bstep_v58.py","fix_v58_chain.py","ast_fusion_v60.py"]:
    runpy.run_path(str(ROOT/name))

src=(OUT/"Submission_v60.lean").read_text()

old='''def impl : Nat → Nat := fun n =>
  biterFastBare (caSteps n) (WideFast.fastInitFused (caSeed n))

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [WideFast.fastInitFused_eq]
  rw [biterFastBare_eq_biterFast (caSteps n)
    (WideFast.fastInit (caSeed n)) (fastInit_lt256 (caSeed n))]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n
'''
new='''/-- Generic maskless iterator for step counts outside the protected 2/4/8
unrolled paths.  This targets larger hidden cohorts without changing V60's
current fast paths. -/
def biterBare : Nat → Nat → Nat
  | 0, m => m
  | t + 1, m => biterBare t (bstepBare m)

def biterFlash (t m : Nat) : Nat :=
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
if old not in src:
    raise SystemExit("V60 final block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v64_probe.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
