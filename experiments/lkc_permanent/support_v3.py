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
  unfold permanentRowSupport
  simp only [List.mem_filter, List.mem_range]
  constructor
  · rintro ⟨hj, hentry⟩
    refine ⟨hj, ?_⟩
    unfold permanentEntry at hentry
    simp only [hnot, if_false] at hentry
    by_cases hji : j = i
    · exact Or.inl hji
    · have hij : ¬ i = j := fun h => hji h.symm
      simp only [hij, false_or] at hentry
      by_cases hj1 : j = permanentColumnOne dimension seed i
      · exact Or.inr (Or.inl hj1)
      · simp only [hj1, false_or] at hentry
        exact Or.inr (Or.inr (by
          cases h2 : (j = permanentColumnTwo dimension seed i)
          · simp [h2] at hentry
          · exact h2))
  · rintro ⟨hj, hsupport⟩
    refine ⟨hj, ?_⟩
    unfold permanentEntry
    simp only [hnot, if_false]
    rcases hsupport with hji | hj1 | hj2
    · have hij : i = j := hji.symm
      simp [hij]
    · simp [hj1]
    · simp [hj2]

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
  have hndLeft : (permanentRowSupport dimension seed i).Nodup := by
    unfold permanentRowSupport
    exact List.Pairwise.filter _ List.nodup_range
  have hndRight :
      [i, permanentColumnOne dimension seed i,
          permanentColumnTwo dimension seed i].Nodup := by
    simp [hi1, hi2, h12]
  refine (List.perm_ext_iff_of_nodup hndLeft hndRight).2 ?_
  intro j
  rw [mem_permanentRowSupport_iff dimension seed i j hd]
  constructor
  · rintro ⟨_, h⟩
    simpa using h
  · intro h
    have hs :
        j = i ∨
        j = permanentColumnOne dimension seed i ∨
        j = permanentColumnTwo dimension seed i := by
      simpa using h
    refine ⟨?_, hs⟩
    rcases hs with hji | hj1 | hj2
    · simpa [hji] using hi
    · simpa [hj1] using h1.1
    · simpa [hj2] using h2.1

end Submission
'''
p=OUT/"Support_v3.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
