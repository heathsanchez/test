#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"flash_v64_probe.py"))
src=(OUT/"Submission_v64_probe.lean").read_text()

marker="end Submission\n"
if not src.endswith(marker):
    raise SystemExit("V64 probe end marker missing")
src=src[:-len(marker)]

proof=r'''
theorem biterBare_eq_biter :
    ∀ t m, m < 2 ^ 256 → biterBare t m = biter t m
  | 0, m, hm => rfl
  | t + 1, m, hm => by
      rw [biterBare, biter]
      rw [bstepBare_eq m hm]
      exact biterBare_eq_biter t (bstep m) (bstep_lt256 m)

theorem biterFlash_eq_biterFastBare
    (t m : Nat) (hm : m < 2 ^ 256) :
    biterFlash t m = biterFastBare t m := by
  unfold biterFlash biterFastBare
  by_cases h2 : t = 2
  · simp only [if_pos h2]
  · simp only [if_neg h2]
    by_cases h4 : t = 4
    · simp only [if_pos h4]
    · simp only [if_neg h4]
      by_cases h8 : t = 8
      · simp only [if_pos h8]
      · simp only [if_neg h8]
        exact biterBare_eq_biter t m hm

theorem fastInitFused_lt256 (seed : Nat) :
    WideFast.fastInitFused seed < 2 ^ 256 := by
  rw [WideFast.fastInitFused_eq]
  exact fastInit_lt256 seed

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFlash_eq_biterFastBare
    (caSteps n) (WideFast.fastInitFused (caSeed n))
    (fastInitFused_lt256 (caSeed n))]
  rw [WideFast.fastInitFused_eq]
  rw [biterFastBare_eq_biterFast (caSteps n)
    (WideFast.fastInit (caSeed n)) (fastInit_lt256 (caSeed n))]
  rw [WideFast.fastInit_v27_eq]
  exact impl_v27_correct n

end Submission
'''
src += proof
p=OUT/"Submission_v64.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
