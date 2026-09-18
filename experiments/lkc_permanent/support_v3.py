#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

theorem permanentSkipOne_props
    (dimension excluded k : Nat)
    (hexcluded : excluded < dimension)
    (hk : k < dimension - 1) :
    permanentSkipOne excluded k < dimension ∧
      permanentSkipOne excluded k ≠ excluded := by
  unfold permanentSkipOne
  by_cases h : k < excluded
  · simp [h]
    omega
  · simp [h]
    omega

theorem permanentSkipTwo_props
    (dimension a b k : Nat)
    (ha : a < dimension)
    (hb : b < dimension)
    (hab : a ≠ b)
    (hk : k < dimension - 2) :
    permanentSkipTwo a b k < dimension ∧
      permanentSkipTwo a b k ≠ a ∧
      permanentSkipTwo a b k ≠ b := by
  by_cases hle : a ≤ b
  · have hlt : a < b := by omega
    have hmin : min a b = a := Nat.min_eq_left hle
    have hmax : max a b = b := Nat.max_eq_right hle
    by_cases hka : k < a
    · have hkb : k < b := by omega
      simp [permanentSkipTwo, hmin, hmax, hka, hkb]
      omega
    · by_cases hkb : k + 1 < b
      · simp [permanentSkipTwo, hmin, hmax, hka, hkb]
        omega
      · simp [permanentSkipTwo, hmin, hmax, hka, hkb]
        omega
  · have hba : b ≤ a := Nat.le_of_not_ge hle
    have hlt : b < a := by omega
    have hmin : min a b = b := Nat.min_eq_right hba
    have hmax : max a b = a := Nat.max_eq_left hba
    by_cases hkb : k < b
    · have hka : k < a := by omega
      simp [permanentSkipTwo, hmin, hmax, hkb, hka]
      omega
    · by_cases hka : k + 1 < a
      · simp [permanentSkipTwo, hmin, hmax, hkb, hka]
        omega
      · simp [permanentSkipTwo, hmin, hmax, hkb, hka]
        omega

theorem permanentColumnOne_props
    (dimension seed i : Nat)
    (hd : 3 ≤ dimension)
    (hi : i < dimension) :
    permanentColumnOne dimension seed i < dimension ∧
      permanentColumnOne dimension seed i ≠ i := by
  unfold permanentColumnOne
  apply permanentSkipOne_props dimension i
  · exact hi
  · exact Nat.mod_lt _ (by omega)

theorem permanentColumnTwo_props
    (dimension seed i : Nat)
    (hd : 3 ≤ dimension)
    (hi : i < dimension) :
    permanentColumnTwo dimension seed i < dimension ∧
      permanentColumnTwo dimension seed i ≠ i ∧
      permanentColumnTwo dimension seed i ≠ permanentColumnOne dimension seed i := by
  have h1 := permanentColumnOne_props dimension seed i hd hi
  unfold permanentColumnTwo
  apply permanentSkipTwo_props dimension i (permanentColumnOne dimension seed i)
  · exact hi
  · exact h1.1
  · exact Ne.symm h1.2
  · exact Nat.mod_lt _ (by omega)

theorem permanentEntry_support_iff
    (dimension seed i j : Nat)
    (hd : 3 ≤ dimension) :
    permanentEntry dimension seed i j = 1 ↔
      i = j ∨
      j = permanentColumnOne dimension seed i ∨
      j = permanentColumnTwo dimension seed i := by
  have hnot : ¬ dimension < 3 := by omega
  unfold permanentEntry
  rw [if_neg hnot]
  by_cases h1 : i = j
  · simp [h1]
  · by_cases h2 : j = permanentColumnOne dimension seed i
    · simp [h1, h2]
    · by_cases h3 : j = permanentColumnTwo dimension seed i
      · simp [h1, h2, h3]
      · simp [h1, h2, h3]

theorem permanentEntry_zero_iff
    (dimension seed i j : Nat)
    (hd : 3 ≤ dimension) :
    permanentEntry dimension seed i j = 0 ↔
      i ≠ j ∧
      j ≠ permanentColumnOne dimension seed i ∧
      j ≠ permanentColumnTwo dimension seed i := by
  have hnot : ¬ dimension < 3 := by omega
  unfold permanentEntry
  rw [if_neg hnot]
  by_cases h1 : i = j
  · simp [h1]
  · by_cases h2 : j = permanentColumnOne dimension seed i
    · simp [h1, h2]
    · by_cases h3 : j = permanentColumnTwo dimension seed i
      · simp [h1, h2, h3]
      · simp [h1, h2, h3]

end Submission
'''
p=OUT/"Support_v3.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
