#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"flash_v64_probe.py"))
p=OUT/"Submission_v64_probe.lean"
src=p.read_text()

marker="\nend Submission\n"
if marker not in src:
    raise SystemExit("Submission terminator missing")

proof=r'''
theorem biterBare_eq_biter :
    ∀ t m, m < 2 ^ 256 -> biterBare t m = biter t m
  | 0, m, hm => rfl
  | t + 1, m, hm => by
      simp only [biterBare, biter]
      rw [bstepBare_eq m hm]
      exact biterBare_eq_biter t (bstep m) (bstep_lt256 m)

theorem biterFlash_eq_biterFast (t m : Nat) (hm : m < 2 ^ 256) :
    biterFlash t m = biterFast t m := by
  unfold biterFlash biterFast
  by_cases h2 : t = 2
  · simp only [if_pos h2]
    rw [bstepBare_eq m hm]
    exact bstepBare_eq _ (bstep_lt256 _)
  · simp only [if_neg h2]
    by_cases h4 : t = 4
    · simp only [if_pos h4]
      rw [bstepBare_eq m hm]
      rw [bstepBare_eq _ (bstep_lt256 _)]
      rw [bstepBare_eq _ (bstep_lt256 _)]
      exact bstepBare_eq _ (bstep_lt256 _)
    · simp only [if_neg h4]
      by_cases h8 : t = 8
      · simp only [if_pos h8]
        rw [bstepBare_eq m hm]
        rw [bstepBare_eq _ (bstep_lt256 _)]
        rw [bstepBare_eq _ (bstep_lt256 _)]
        rw [bstepBare_eq _ (bstep_lt256 _)]
        rw [bstepBare_eq _ (bstep_lt256 _)]
        rw [bstepBare_eq _ (bstep_lt256 _)]
        rw [bstepBare_eq _ (bstep_lt256 _)]
        exact bstepBare_eq _ (bstep_lt256 _)
      · simp only [if_neg h8]
        exact biterBare_eq_biter t m hm

theorem impl_correct : ∀ n, impl n = caSpecN n := by
  intro n
  unfold impl
  rw [biterFlash_eq_biterFast
    (caSteps n) (WideFast.fastInitFused (caSeed n))]
  · rw [WideFast.fastInitFused_eq]
    rw [WideFast.fastInit_v27_eq]
    exact impl_v27_correct n
  · rw [WideFast.fastInitFused_eq]
    exact fastInit_lt256 (caSeed n)
'''
out=src.replace(marker,"\n"+proof+marker,1)
q=OUT/"Submission_v64_proof.lean"
q.write_text(out)
print(f"generated {q} bytes={len(out.encode())}")
