#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)

runpy.run_path(str(ROOT / "support_v3.py"))
support = (OUT / "Support_v3.lean").read_text()
support_body = support.replace("import Spec\n\nnamespace Submission\n\n", "", 1)
support_body = support_body.rsplit("\nend Submission", 1)[0]

core = r'''import Spec

namespace Submission

set_option linter.unusedSimpArgs false

/--
One sparse row transition.  The continuation is explicit, so the expensive
recursive proof is factored into:
  1. a non-recursive one-step equivalence, and
  2. a tiny generic structural lift over the remaining rows.
-/
def permanentChoices (dimension seed i : Nat) : List Nat :=
  [i, permanentColumnOne dimension seed i,
      permanentColumnTwo dimension seed i]

def permanentSparseStep
    (dimension seed i : Nat) (next : Nat → Nat) (used : Nat) : Nat :=
  let choices :=
    if dimension < 3 then List.range dimension
    else permanentChoices dimension seed i
  choices.foldl (fun total j =>
    if used.testBit j then total
    else total + next (used ||| (1 <<< j))) 0

def permanentSparse : Nat → Nat → List Nat → Nat → Nat
  | _dimension, _seed, [], _ => 1
  | dimension, seed, i :: is, used =>
      permanentSparseStep dimension seed i
        (permanentSparse dimension seed is) used

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d) 0

'''

proof = r'''
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
  permanentChoices dimension seed i

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
    simp [rowSupport, permanentChoices, h1.2, Ne.symm h1.2,
      h2.2.1, Ne.symm h2.2.1, h2.2.2, Ne.symm h2.2.2]
  apply (List.perm_ext_iff_of_nodup hleft hright).2
  intro j
  constructor
  · intro hj
    have hp := (List.mem_filter.mp hj).2
    have he : permanentEntry dimension seed i j = 1 := by
      simpa only [supportPred, beq_iff_eq] using hp
    rcases (permanentEntry_support_iff dimension seed i j hd).mp he with hij | hj1 | hj2
    · simp [rowSupport, permanentChoices, hij]
    · simp [rowSupport, permanentChoices, hj1]
    · simp [rowSupport, permanentChoices, hj2]
  · intro hj
    have hj' : j = i ∨
        j = permanentColumnOne dimension seed i ∨
        j = permanentColumnTwo dimension seed i := by
      simpa [rowSupport, permanentChoices] using hj
    have hs : i = j ∨
        j = permanentColumnOne dimension seed i ∨
        j = permanentColumnTwo dimension seed i := by
      rcases hj' with hji | hj1 | hj2
      · exact Or.inl hji.symm
      · exact Or.inr (Or.inl hj1)
      · exact Or.inr (Or.inr hj2)
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

/--
Certified transition abstraction: for an arbitrary continuation `next`, one
dense trusted row transition equals the sparse three-choice transition.
There is no recursion in this theorem.
-/
theorem denseRowStep_eq_sparseRowStep
    (dimension seed i used : Nat) (next : Nat → Nat)
    (hi : i < dimension) :
    (List.range dimension).foldl (fun total j =>
      let entry := (genPermanentRow dimension seed i).getD j 0
      if entry = 0 || used.testBit j then
        total
      else
        total + entry * next (used ||| (1 <<< j))) 0 =
      permanentSparseStep dimension seed i next used := by
  unfold permanentSparseStep
  by_cases hdlt : dimension < 3
  · rw [if_pos hdlt]
    apply foldl_congr_local
    intro total j hj
    have hjlt : j < dimension := by simpa using hj
    rw [genPermanentRow_getD dimension seed i j hjlt]
    unfold permanentEntry
    simp [hdlt]
  · have hd : 3 ≤ dimension := by omega
    rw [if_neg hdlt]
    let p : Nat → Bool := fun j => supportPred dimension seed i j
    let f : Nat → Nat → Nat := fun total j =>
      if used.testBit j then total
      else total + next (used ||| (1 <<< j))
    calc
      (List.range dimension).foldl (fun total j =>
          let entry := (genPermanentRow dimension seed i).getD j 0
          if entry = 0 || used.testBit j then
            total
          else
            total + entry * next (used ||| (1 <<< j))) 0
          =
          (List.range dimension).foldl
            (fun total j => if p j then f total j else total) 0 := by
              apply foldl_congr_local
              intro total j hj
              have hjlt : j < dimension := by simpa using hj
              rw [genPermanentRow_getD dimension seed i j hjlt]
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
      _ = _ := by
            rfl

/--
The recursive lift is now tiny: the induction transports an equality of
continuations, then applies the already-certified one-row transition theorem.
-/
theorem permanentSparse_eq (dimension seed : Nat) :
    ∀ is, (∀ i, i ∈ is → i < dimension) →
      permanentSparse dimension seed is =
        permanentRows dimension
          (is.map (genPermanentRow dimension seed)) := by
  intro is
  induction is with
  | nil =>
      intro hall
      rfl
  | cons i is ih =>
      intro hall
      have hi : i < dimension := hall i (by simp)
      have htail : ∀ x, x ∈ is → x < dimension := by
        intro x hx
        exact hall x (by simp [hx])
      have ihfun :
          permanentSparse dimension seed is =
            permanentRows dimension
              (is.map (genPermanentRow dimension seed)) :=
        ih htail
      funext used
      simp only [permanentSparse, List.map_cons, permanentRows]
      rw [← ihfun]
      exact (denseRowStep_eq_sparseRowStep
        dimension seed i used
        (permanentSparse dimension seed is) hi).symm

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  unfold impl permanentSpecN permanentSpec genPermanentMatrix
  simp only [List.length_map, List.length_range]
  have hall :
      ∀ i, i ∈ List.range (permanentDimension n) →
        i < permanentDimension n := by
    intro i hi
    simpa using hi
  have hfun := permanentSparse_eq
    (permanentDimension n) (permanentSeed n)
    (List.range (permanentDimension n)) hall
  exact congrFun hfun 0

end Submission
'''

text = core + support_body + "\n" + proof
p = OUT / "Submission_v5.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
