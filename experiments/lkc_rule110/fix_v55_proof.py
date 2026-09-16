#!/usr/bin/env python3
from pathlib import Path

path = Path(__file__).resolve().parent / "generated" / "Submission_v55.lean"
s = path.read_text()
old = '''theorem mod4_exact_of_not_small
    (d : Nat) (hd : d < 2 ^ 256)
    (hsmall : ¬ d % gatherMod4 < 16) :
    d % gatherMod4 = d := by
  have hsum : gatherMod4 + 16 = 2 ^ 256 := by decide
  have h16m : 16 < gatherMod4 := by decide
  have hdm : d < gatherMod4 := by
    by_contra hnot
    have hge : gatherMod4 ≤ d := by omega
    have hsub : d - gatherMod4 < 16 := by omega
    have hsubm : d - gatherMod4 < gatherMod4 := by omega
    have hmod : d % gatherMod4 = d - gatherMod4 := by
      rw [Nat.mod_eq_sub_mod hge]
      exact Nat.mod_eq_of_lt hsubm
    apply hsmall
    rw [hmod]
    exact hsub
  exact Nat.mod_eq_of_lt hdm
'''
new = '''theorem mod4_exact_of_not_small
    (d : Nat) (hd : d < 2 ^ 256)
    (hsmall : ¬ d % gatherMod4 < 16) :
    d % gatherMod4 = d := by
  have hsum : gatherMod4 + 16 = 2 ^ 256 := by decide
  have h16m : 16 < gatherMod4 := by decide
  by_cases hdm : d < gatherMod4
  · exact Nat.mod_eq_of_lt hdm
  · have hge : gatherMod4 ≤ d := by omega
    have hsub : d - gatherMod4 < 16 := by omega
    have hsubm : d - gatherMod4 < gatherMod4 := by omega
    have hmod : d % gatherMod4 = d - gatherMod4 := by
      rw [Nat.mod_eq_sub_mod hge]
      exact Nat.mod_eq_of_lt hsubm
    have hs : d % gatherMod4 < 16 := by
      rw [hmod]
      exact hsub
    exact (hsmall hs).elim
'''
if old not in s:
    raise SystemExit("v55 theorem block not found")
path.write_text(s.replace(old, new, 1))
print(f"patched {path} bytes={path.stat().st_size}")
