#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"; OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"full_v5.py"))
src=(OUT/"Submission_v5.lean").read_text()

old_impl='''def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d) 0
'''
state=r'''/-- Exact V7 reduction spine, now with a proof relation to the list semantics. -/
def permanentSparseState : Nat → Nat → Nat → Nat → Nat
  | 0, _dimension, _seed, _used => 1
  | rows + 1, dimension, seed, used =>
      let i := dimension - (rows + 1)
      permanentSparseStep dimension seed i
        (permanentSparseState rows dimension seed) used

theorem permanentSparseState_eq (dimension seed : Nat) :
    ∀ rows, rows ≤ dimension →
      permanentSparseState rows dimension seed =
        permanentSparse dimension seed
          (List.range' (dimension - rows) rows) := by
  intro rows
  induction rows with
  | zero =>
      intro h
      rfl
  | succ rows ih =>
      intro h
      rw [List.range'_succ]
      simp only [permanentSparseState, permanentSparse]
      have htail : rows ≤ dimension := by omega
      have hidx : dimension - (rows + 1) + 1 = dimension - rows := by omega
      rw [hidx, ih htail]

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparseState d d s 0
'''
if old_impl not in src:
    raise SystemExit("V5 impl block missing")
src=src.replace(old_impl,state,1)

old_proof=r'''theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
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
'''
new_proof=r'''theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  unfold impl permanentSpecN permanentSpec genPermanentMatrix
  simp only [List.length_map, List.length_range]
  let d := permanentDimension n
  let s := permanentSeed n
  have hs := permanentSparseState_eq d s d (Nat.le_refl d)
  rw [congrFun hs 0]
  simp only [Nat.sub_self]
  rw [← List.range_eq_range']
  have hall : ∀ i, i ∈ List.range d → i < d := by
    intro i hi
    simpa using hi
  have hfun := permanentSparse_eq d s (List.range d) hall
  exact congrFun hfun 0
'''
if old_proof not in src:
    raise SystemExit("V5 final proof block missing")
src=src.replace(old_proof,new_proof,1)

p=OUT/"Submission_v9_state_exact_proof.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
