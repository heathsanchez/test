#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"support_v3.py"))
support=(OUT/"Support_v3.lean").read_text()
support_body=support
support_body=support_body.replace("import Spec\n\nnamespace Submission\n\n","",1)
support_body=support_body.rsplit("\nend Submission",1)[0]

core=r'''import Spec

namespace Submission

set_option linter.unusedSimpArgs false

def permanentSparse : Nat → Nat → List Nat → Nat → Nat
  | _dimension, _seed, [], _ => 1
  | dimension, seed, i :: is, used =>
      if dimension < 3 then
        (List.range dimension).foldl (fun total j =>
          if used.testBit j then total
          else total + permanentSparse dimension seed is (used ||| (1 <<< j))) 0
      else
        let c1 := permanentColumnOne dimension seed i
        let c2 := permanentColumnTwo dimension seed i
        (if used.testBit i then 0 else permanentSparse dimension seed is (used ||| (1 <<< i))) +
        (if used.testBit c1 then 0 else permanentSparse dimension seed is (used ||| (1 <<< c1))) +
        (if used.testBit c2 then 0 else permanentSparse dimension seed is (used ||| (1 <<< c2)))

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d) 0

'''

proof=r'''
theorem genPermanentRow_getD
    (dimension seed i j : Nat) (hj : j < dimension) :
    (genPermanentRow dimension seed i).getD j 0 =
      permanentEntry dimension seed i j := by
  unfold genPermanentRow
  simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
  rw [List.getElem?_range hj]
  simp

theorem foldl_congr_local
    (xs : List Nat) (f g : Nat → Nat → Nat)
    (h : ∀ acc x, x ∈ xs → f acc x = g acc x) :
    ∀ init, xs.foldl f init = xs.foldl g init := by
  induction xs with
  | nil =>
      intro init
      rfl
  | cons a as ih =>
      intro init
      simp only [List.foldl]
      rw [h init a (by simp)]
      apply ih
      intro acc x hx
      apply h acc x
      simp [hx]

def rowSupport (dimension seed i : Nat) : List Nat :=
  [i, permanentColumnOne dimension seed i,
      permanentColumnTwo dimension seed i]

def supportPred (dimension seed i j : Nat) : Bool :=
  permanentEntry dimension seed i j == 1

theorem support_filter_perm
    (dimension seed i : Nat)
    (hd : 3 ≤ dimension) (hi : i < dimension) :
    List.Perm
      ((List.range dimension).filter (supportPred dimension seed i))
      (rowSupport dimension seed i) := by
  have h1 := permanentColumnOne_props dimension seed i hd hi
  have h2 := permanentColumnTwo_props dimension seed i hd hi
  have hleft :
      ((List.range dimension).filter (supportPred dimension seed i)).Nodup :=
    List.nodup_range.filter _
  have hright : (rowSupport dimension seed i).Nodup := by
    simp only [rowSupport, List.nodup_cons, List.mem_cons, List.mem_singleton,
      List.nodup_singleton, not_or]
    exact ⟨⟨Ne.symm h1.2, Ne.symm h2.2.1⟩, Ne.symm h2.2.2⟩
  apply (List.perm_ext_iff_of_nodup hleft hright).2
  intro j
  constructor
  · intro hj
    have hp := (List.mem_filter.mp hj).2
    have he : permanentEntry dimension seed i j = 1 := by
      simpa only [supportPred, beq_iff_eq] using hp
    rcases (permanentEntry_support_iff dimension seed i j hd).mp he with hij | hj1 | hj2
    · simp [rowSupport, hij]
    · simp [rowSupport, hj1]
    · simp [rowSupport, hj2]
  · intro hj
    have hs : i = j ∨
        j = permanentColumnOne dimension seed i ∨
        j = permanentColumnTwo dimension seed i := by
      simpa [rowSupport] using hj
    have he : permanentEntry dimension seed i j = 1 :=
      (permanentEntry_support_iff dimension seed i j hd).2 hs
    apply List.mem_filter.mpr
    constructor
    · rcases hs with hij | hj1 | hj2
      · subst hij
        simpa using hi
      · simpa [hj1] using h1.1
      · simpa [hj2] using h2.1
    · simpa only [supportPred, beq_iff_eq] using he

theorem permanentSparse_eq (dimension seed : Nat) :
    ∀ is used, (∀ i, i ∈ is → i < dimension) →
      permanentSparse dimension seed is used =
        permanentRows dimension
          (is.map (genPermanentRow dimension seed)) used := by
  intro is
  induction is with
  | nil =>
      intro used hall
      rfl
  | cons i is ih =>
      intro used hall
      have hi : i < dimension := hall i (by simp)
      have htail : ∀ x, x ∈ is → x < dimension := by
        intro x hx
        exact hall x (by simp [hx])
      have ihAll : ∀ u,
          permanentSparse dimension seed is u =
            permanentRows dimension
              (is.map (genPermanentRow dimension seed)) u := by
        intro u
        exact ih u htail
      simp only [permanentSparse, List.map_cons, permanentRows]
      by_cases hdlt : dimension < 3
      · rw [if_pos hdlt]
        apply foldl_congr_local
        intro total j hj
        have hjlt : j < dimension := by simpa using hj
        rw [genPermanentRow_getD dimension seed i j hjlt]
        rw [ihAll (used ||| (1 <<< j))]
        unfold permanentEntry
        simp [hdlt]
      · have hd : 3 ≤ dimension := by omega
        rw [if_neg hdlt]
        symm
        let p : Nat → Bool := fun j => supportPred dimension seed i j
        let f : Nat → Nat → Nat := fun total j =>
          if used.testBit j then total
          else total + permanentSparse dimension seed is (used ||| (1 <<< j))
        calc
          _ = (List.range dimension).foldl
              (fun total j => if p j then f total j else total) 0 := by
                apply foldl_congr_local
                intro total j hj
                have hjlt : j < dimension := by simpa using hj
                rw [genPermanentRow_getD dimension seed i j hjlt]
                rw [← ihAll (used ||| (1 <<< j))]
                dsimp [p, f, supportPred]
                by_cases h1 : i = j
                · simp [permanentEntry, hdlt, h1]
                · by_cases h2 : j = permanentColumnOne dimension seed i
                  · simp [permanentEntry, hdlt, h1, h2]
                  · by_cases h3 : j = permanentColumnTwo dimension seed i
                    · simp [permanentEntry, hdlt, h1, h2, h3]
                    · simp [permanentEntry, hdlt, h1, h2, h3]
          _ = ((List.range dimension).filter p).foldl f 0 := by
                symm
                exact List.foldl_filter
          _ = (rowSupport dimension seed i).foldl f 0 := by
                apply (support_filter_perm dimension seed i hd hi).foldl_eq'
                · intro x hx y hy z
                  dsimp [f]
                  by_cases hxu : used.testBit x
                  · simp [hxu]
                  · by_cases hyu : used.testBit y
                    · simp [hxu, hyu]
                    · simp [hxu, hyu, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]
                · exact 0
          _ = _ := by
                simp only [rowSupport, f, List.foldl]
                by_cases h0 : used.testBit i
                · by_cases h1 : used.testBit (permanentColumnOne dimension seed i)
                  · by_cases h2 : used.testBit (permanentColumnTwo dimension seed i)
                    · simp [h0, h1, h2]
                    · simp [h0, h1, h2]
                  · by_cases h2 : used.testBit (permanentColumnTwo dimension seed i)
                    · simp [h0, h1, h2]
                    · simp [h0, h1, h2, Nat.add_assoc]
                · by_cases h1 : used.testBit (permanentColumnOne dimension seed i)
                  · by_cases h2 : used.testBit (permanentColumnTwo dimension seed i)
                    · simp [h0, h1, h2]
                    · simp [h0, h1, h2, Nat.add_assoc]
                  · by_cases h2 : used.testBit (permanentColumnTwo dimension seed i)
                    · simp [h0, h1, h2, Nat.add_assoc]
                    · simp [h0, h1, h2, Nat.add_assoc]

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  unfold impl permanentSpecN permanentSpec genPermanentMatrix
  rw [permanentSparse_eq
      (permanentDimension n) (permanentSeed n)
      (List.range (permanentDimension n)) 0]
  · simp [genPermanentMatrix]
  · intro i hi
    simpa using hi

end Submission
'''

text=core+support_body+"\n"+proof
p=OUT/"Submission_v4.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
