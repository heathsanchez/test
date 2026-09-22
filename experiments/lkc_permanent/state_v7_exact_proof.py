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

# Keep V5's already-qualified theorem as the semantic bridge.
src=src.replace(old_impl, old_impl.replace("def impl ", "def implV5 "), 1)
src=src.replace("theorem impl_correct : ∀ n, impl n = permanentSpecN n := by",
                "theorem implV5_correct : ∀ n, implV5 n = permanentSpecN n := by", 1)
src=src.replace("  unfold impl permanentSpecN permanentSpec genPermanentMatrix",
                "  unfold implV5 permanentSpecN permanentSpec genPermanentMatrix", 1)

extra=r'''
/-- Exact V7 runtime: reconstruct the current row from the number of rows left.
No list of row indices exists on the measured path. -/
def permanentSparseState : Nat → Nat → Nat → Nat → Nat
  | 0, _dimension, _seed, _used => 1
  | rows + 1, dimension, seed, used =>
      let i := dimension - (rows + 1)
      permanentSparseStep dimension seed i
        (permanentSparseState rows dimension seed) used

theorem permanentSparseState_eq (dimension seed : Nat) :
    ∀ rows used, rows ≤ dimension →
      permanentSparseState rows dimension seed used =
        permanentSparse dimension seed
          (List.range' (dimension - rows) rows) used := by
  intro rows
  induction rows with
  | zero =>
      intro used h
      rfl
  | succ rows ih =>
      intro used h
      rw [List.range'_succ]
      simp only [permanentSparseState, permanentSparse]
      have hcursor :
          dimension - (rows + 1) + 1 = dimension - rows := by
        omega
      apply congrArg
        (fun next =>
          permanentSparseStep dimension seed
            (dimension - (rows + 1)) next used)
      funext u
      rw [hcursor]
      exact ih u (by omega)

def impl (n : Nat) : Nat :=
  let d := permanentDimension n
  let s := permanentSeed n
  permanentSparseState d d s 0

theorem impl_eq_implV5 (n : Nat) : impl n = implV5 n := by
  unfold impl implV5
  rw [permanentSparseState_eq
    (permanentDimension n) (permanentSeed n)
    (permanentDimension n) 0 (Nat.le_refl _)]
  simp only [Nat.sub_self]
  rw [← List.range_eq_range']

theorem impl_correct : ∀ n, impl n = permanentSpecN n := by
  intro n
  rw [impl_eq_implV5]
  exact implV5_correct n
'''
src=src.replace("\nend Submission\n", extra+"\nend Submission\n", 1)

p=OUT/"Submission_v7_exact_proof.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
