#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"full_v5.py"))
src=(OUT/"Submission_v5.lean").read_text()

start=src.index("def impl (n : Nat) : Nat :=")
end=src.index("\nend Submission", start)

block=r'''/-- Proof-friendly form of the V7 row-state representation.  The row index is
carried explicitly; no List.range is traversed at runtime. -/
def permanentSparseState : Nat → Nat → Nat → Nat → Nat → Nat
  | 0, _dimension, _seed, _i, _used => 1
  | rows + 1, dimension, seed, i, used =>
      permanentSparseStep dimension seed i
        (permanentSparseState rows dimension seed (i + 1)) used

theorem permanentSparseState_eq (dimension seed : Nat) :
    ∀ rows i, i + rows ≤ dimension →
      permanentSparseState rows dimension seed i =
        permanentSparse dimension seed (List.range' i rows) := by
  intro rows
  induction rows with
  | zero =>
      intro i h
      rfl
  | succ rows ih =>
      intro i h
      rw [List.range'_succ]
      simp only [permanentSparseState, permanentSparse]
      have ht : i + 1 + rows ≤ dimension := by omega
      rw [ih (i + 1) ht]

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparseState d d s 0 0

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  unfold impl permanentSpecN permanentSpec genPermanentMatrix
  simp only [List.length_map, List.length_range]
  let d := permanentDimension n
  let s := permanentSeed n
  have hs := permanentSparseState_eq d s d 0 (by omega)
  have hr : List.range d = List.range' 0 d := List.range_eq_range'
  rw [congrFun hs 0]
  rw [← hr]
  have hall :
      ∀ i, i ∈ List.range d → i < d := by
    intro i hi
    simpa using hi
  have hfun := permanentSparse_eq d s (List.range d) hall
  exact congrFun hfun 0
'''

src=src[:start]+block+src[end:]
p=OUT/"Submission_v8_state_proof.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
