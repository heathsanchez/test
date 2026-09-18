#!/usr/bin/env python3
from pathlib import Path

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

text=r'''import Spec

namespace Submission

def foldGenerated
    (dimension seed i : Nat) (rest : Nat → Nat) (used : Nat) :
    List Nat → Nat → Nat
  | [], total => total
  | j :: js, total =>
      let entry := permanentEntry dimension seed i j
      let total' :=
        if entry = 0 || used.testBit j then
          total
        else
          total + entry * rest (used ||| (1 <<< j))
      foldGenerated dimension seed i rest used js total'

def permanentRowsGen (dimension seed : Nat) :
    List Nat → Nat → Nat
  | [], _ => 1
  | i :: is, used =>
      foldGenerated dimension seed i
        (permanentRowsGen dimension seed is) used
        (List.range dimension) 0

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

theorem foldGenerated_eq
    (dimension seed i : Nat) (rest : Nat → Nat) (used : Nat)
    (js : List Nat) (total : Nat) :
    foldGenerated dimension seed i rest used js total =
      js.foldl (fun total j =>
        let entry := permanentEntry dimension seed i j
        if entry = 0 || used.testBit j then
          total
        else
          total + entry * rest (used ||| (1 <<< j))) total := by
  induction js generalizing total with
  | nil => rfl
  | cons j js ih =>
      simp only [foldGenerated, List.foldl]
      exact ih _

theorem genPermanentRow_getD
    (dimension seed i j : Nat) (h : j < dimension) :
    (genPermanentRow dimension seed i).getD j 0 =
      permanentEntry dimension seed i j := by
  unfold genPermanentRow
  simp only [List.getD_eq_getElem?_getD, List.getElem?_map]
  rw [List.getElem?_range h]
  simp

theorem permanentRowsGen_eq :
    ∀ dimension seed is used,
      permanentRowsGen dimension seed is used =
        permanentRows dimension
          (is.map (genPermanentRow dimension seed)) used
  | dimension, seed, [], used => rfl
  | dimension, seed, i :: is, used => by
      simp only [permanentRowsGen, List.map_cons, permanentRows]
      rw [foldGenerated_eq]
      apply foldl_congr_local
      intro total j hj
      have hjlt : j < dimension := by simpa using hj
      rw [genPermanentRow_getD dimension seed i j hjlt]
      rw [permanentRowsGen_eq dimension seed is]

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentRowsGen d s (List.range d) 0

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  unfold impl permanentSpecN permanentSpec genPermanentMatrix
  rw [permanentRowsGen_eq]
  simp

end Submission
'''
p=OUT/"Submission_v2.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
