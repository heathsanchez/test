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
  unfold permanentSkipTwo
  by_cases hle : a ≤ b
  · have hlt : a < b := by omega
    rw [Nat.min_eq_left hle, Nat.max_eq_right hle]
    by_cases hka : k < a
    · have hkb : k < b := by omega
      simp [hka, hkb]
      omega
    · by_cases hkb : k + 1 < b
      · simp [hka, hkb]
        omega
      · simp [hka, hkb]
        omega
  · have hba : b ≤ a := Nat.le_of_not_ge hle
    have hlt : b < a := by omega
    rw [Nat.min_eq_right hba, Nat.max_eq_left hba]
    by_cases hkb : k < b
    · have hka : k < a := by omega
      simp [hkb, hka]
      omega
    · by_cases hka : k + 1 < a
      · simp [hkb, hka]
        omega
      · simp [hkb, hka]
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

def permanentRowSupport (dimension seed i : Nat) : List Nat :=
  (List.range dimension).filter
    (fun j => permanentEntry dimension seed i j != 0)

theorem mem_permanentRowSupport_iff
    (dimension seed i j : Nat)
    (hd : 3 ≤ dimension) :
    j ∈ permanentRowSupport dimension seed i ↔
      j < dimension ∧
        (j = i ∨
         j = permanentColumnOne dimension seed i ∨
         j = permanentColumnTwo dimension seed i) := by
  have hnot : ¬ dimension < 3 := by omega
  simp [permanentRowSupport, permanentEntry, hnot, eq_comm]

theorem permanentRowSupport_perm
    (dimension seed i : Nat)
    (hd : 3 ≤ dimension)
    (hi : i < dimension) :
    List.Perm (permanentRowSupport dimension seed i)
      [i, permanentColumnOne dimension seed i,
          permanentColumnTwo dimension seed i] := by
  have h1 := permanentColumnOne_props dimension seed i hd hi
  have h2 := permanentColumnTwo_props dimension seed i hd hi
  have hi1 : i ≠ permanentColumnOne dimension seed i := Ne.symm h1.2
  have hi2 : i ≠ permanentColumnTwo dimension seed i := Ne.symm h2.2.1
  have h12 :
      permanentColumnOne dimension seed i ≠
        permanentColumnTwo dimension seed i := Ne.symm h2.2.2
  apply (List.perm_ext_iff_of_nodup ?_ ?_).2
  · exact List.Pairwise.filter _ List.nodup_range
  · simp [hi1, hi2, h12]
  · intro j
    rw [mem_permanentRowSupport_iff dimension seed i j hd]
    simp [hi, h1.1, h2.1]

end Submission
'''
p=OUT/"Support_v3.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
