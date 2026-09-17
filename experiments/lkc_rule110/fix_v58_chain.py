#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "generated" / "Submission_v58.lean"
s = path.read_text()
old = '''theorem biterFastBare_eq_biterFast (t m : Nat) (hm : m < 2 ^ 256) :
    biterFastBare t m = biterFast t m := by
  unfold biterFastBare biterFast
  by_cases h2 : t = 2
  · simp [h2, bstepBare_eq, bstep_lt256, hm]
  · by_cases h4 : t = 4
    · simp [h2, h4, bstepBare_eq, bstep_lt256, hm]
    · by_cases h8 : t = 8
      · simp [h2, h4, h8, bstepBare_eq, bstep_lt256, hm]
      · simp [h2, h4, h8]
'''
new = '''theorem biterFastBare_eq_biterFast (t m : Nat) (hm : m < 2 ^ 256) :
    biterFastBare t m = biterFast t m := by
  unfold biterFastBare biterFast
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
'''
if old not in s:
    raise SystemExit("v58 chain theorem block not found")
path.write_text(s.replace(old, new, 1))
print(f"patched {path} bytes={path.stat().st_size}")
