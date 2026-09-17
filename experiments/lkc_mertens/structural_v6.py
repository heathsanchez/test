#!/usr/bin/env python3
"""Remove well-founded recursion from the measured least-factor path.
Candidate versions are separate single-file submissions, not answer tables.
"""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'generated'
runpy.run_path(str(ROOT / 'representation_v2.py'))
v5 = (OUT / 'Submission_v5.lean').read_text()
prefix = v5.split('def impl (n : Nat)')[0]

MINIMUM = r'''
/-- The same odd-divisor search as Mathlib, with explicit structural fuel. -/
def minFacStructuralAux (n : Nat) : Nat → Nat → Nat
  | 0, _ => n
  | fuel + 1, k =>
      if n < k * k then n
      else if n % k = 0 then k
      else minFacStructuralAux n fuel (k + 2)

/-- The fuel bound only justifies totality; execution still stops at sqrt(n). -/
theorem minFacStructuralAux_eq (n fuel : Nat) : ∀ k, n < k + fuel →
    minFacStructuralAux n fuel k = Nat.minFacAux n k := by
  induction fuel with
  | zero =>
      intro k hk
      have hnk : n < k := by omega
      have hpos : 0 < k := by omega
      have hsq : n < k * k :=
        Nat.lt_of_lt_of_le hnk (Nat.le_mul_of_pos_right k hpos)
      rw [minFacStructuralAux, Nat.minFacAux, if_pos hsq]
  | succ fuel ih =>
      intro k hk
      rw [minFacStructuralAux, Nat.minFacAux]
      by_cases hsq : n < k * k
      · simp only [if_pos hsq]
      · simp only [if_neg hsq]
        by_cases hm : n % k = 0
        · have hd : k ∣ n := Nat.dvd_of_mod_eq_zero hm
          simp only [if_pos hm, if_pos hd]
        · have hd : ¬ k ∣ n := fun h => hm (Nat.mod_eq_zero_of_dvd h)
          simp only [if_neg hm, if_neg hd]
          exact ih (k + 2) (by omega)

def minFacStructural (n : Nat) : Nat :=
  if n % 2 = 0 then 2 else minFacStructuralAux n (n + 1) 3

theorem minFacStructural_eq (n : Nat) : minFacStructural n = n.minFac := by
  rw [minFacStructural, Nat.minFac_eq]
  simp only [Nat.dvd_iff_mod_eq_zero, minFacStructuralAux_eq n (n + 1) 3 (by omega)]
'''

old_body = prefix.split('def moebiusFusedFuel :', 1)[1].split('theorem moebius_factor_step', 1)[0]
new_body = 'def moebiusStructuralFuel :' + old_body.replace('moebiusFusedFuel', 'moebiusStructuralFuel').replace('let p := n.minFac', 'let p := minFacStructural n')
assert 'let p := minFacStructural n' in new_body

EQUIVALENCE = r'''
theorem moebiusStructuralFuel_eq (fuel n : Nat) :
    moebiusStructuralFuel fuel n = moebiusFusedFuel fuel n := by
  induction fuel generalizing n with
  | zero => rfl
  | succ fuel ih =>
      simp only [moebiusStructuralFuel, moebiusFusedFuel, minFacStructural_eq, ih]

def moebiusStructural (n : Nat) : Int := moebiusStructuralFuel (n + 1) n

theorem moebiusStructural_eq (n : Nat) :
    moebiusStructural n = ArithmeticFunction.moebius n := by
  rw [moebiusStructural, moebiusStructuralFuel_eq]
  exact moebiusFusedFuel_eq (n + 1) n (by omega)
'''

DIRECT = r'''
/-- First-order summation with no generic function argument or accumulator. -/
def mertensDirect : Nat → Int
  | 0 => 0
  | n + 1 => mertensDirect n + moebiusStructural (n + 1)

theorem mertensDirect_eq (n : Nat) : mertensDirect n = mertensSpec n := by
  induction n with
  | zero => simp [mertensDirect, mertensSpec]
  | succ n ih =>
      rw [mertensDirect, ih, moebiusStructural_eq]
      simp only [mertensSpec, Finset.sum_range_succ]
'''

common = prefix + MINIMUM + new_body + EQUIVALENCE
v6 = common + r'''
def impl (n : Nat) : Int := sumDown moebiusStructural n 0

theorem impl_correct : ∀ n, impl n = mertensSpec n := by
  intro n
  exact sumDown_correct moebiusStructural moebiusStructural_eq n

end Submission
'''
v7 = common + DIRECT + r'''
def impl (n : Nat) : Int := mertensDirect n

theorem impl_correct : ∀ n, impl n = mertensSpec n := mertensDirect_eq

end Submission
'''
for name, text in [('v6', v6), ('v7', v7)]:
    assert len(text.encode()) <= 1048576
    assert all(word not in text for word in ['sorry', 'admit', 'native_decide', 'unsafe ', 'partial '])
    path = OUT / f'Submission_{name}.lean'
    path.write_text(text)
    print(f'{name}: {path} ({len(text.encode())} bytes)')
