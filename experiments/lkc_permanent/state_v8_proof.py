#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"full_v5.py"))
src=(OUT/"Submission_v5.lean").read_text()

old_impl='''def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparse d s (List.range d) 0
'''
if old_impl not in src:
    raise SystemExit("V5 impl block missing")

# Preserve the proved V5 evaluator under a private comparison name.
src=src.replace(old_impl, old_impl.replace("def impl ", "def implV5 "), 1)
src=src.replace("theorem impl_correct : ∀ n, impl n = permanentSpecN n := by",
                "theorem implV5_correct : ∀ n, implV5 n = permanentSpecN n := by", 1)
src=src.replace("  unfold impl permanentSpecN permanentSpec genPermanentMatrix",
                "  unfold implV5 permanentSpecN permanentSpec genPermanentMatrix", 1)

state=r'''
/-- Proof-friendly form of the V7 representation. The row cursor is carried
structurally, so runtime never allocates or traverses List.range d. -/
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

theorem impl_eq_implV5 (n : Nat) : impl n = implV5 n := by
  unfold impl implV5
  have hs := permanentSparseState_eq
    (permanentDimension n) (permanentSeed n)
    (permanentDimension n) 0 (by omega)
  rw [congrFun hs 0]
  rw [← List.range_eq_range']

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  rw [impl_eq_implV5]
  exact implV5_correct n
'''
src=src.replace("\nend Submission\n", state+"\nend Submission\n", 1)

p=OUT/"Submission_v8_state_proof.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
