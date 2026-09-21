#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)

runpy.run_path(str(ROOT/"mulsquare_v2.py"))
v2=(OUT/"Submission_v2.lean").read_text()
prefix=v2.split("def impl (n : Nat) : Int :=",1)[0]

extra=r'''
/-- Exact coefficient-word constructor using shift rather than multiply-by-power. -/
def collectCoeffWordShift : Nat → Nat → Nat → Nat × Nat
  | 0, _, state => (0, state)
  | words + 1, shift, state =>
      let state' := lcgNext state
      let (tail, finalState) := collectCoeffWordShift words (shift + 64) state'
      ((state' <<< shift) + tail, finalState)

theorem collectCoeffWordShift_eq :
    ∀ words shift state,
      collectCoeffWordShift words shift state =
        collectCoeffWord words shift state
  | 0, shift, state => rfl
  | words + 1, shift, state => by
      simp only [collectCoeffWordShift, collectCoeffWord]
      rw [collectCoeffWordShift_eq words (shift + 64) (lcgNext state)]
      rw [Nat.shiftLeft_eq]

def coefficientsFromShift : Nat → Nat → Nat → Nat → List Int
  | 0, _, _, _ => []
  | count + 1, k, index, state =>
      let width := coefficientWidth k index
      let words := (width + 63) / 64
      let (word, state') := collectCoeffWordShift words 0 state
      centeredNonzeroCoeff width words word ::
        coefficientsFromShift count k (index + 1) state'

theorem coefficientsFromShift_eq :
    ∀ count k index state,
      coefficientsFromShift count k index state =
        coefficientsFrom count k index state
  | 0, k, index, state => rfl
  | count + 1, k, index, state => by
      simp only [coefficientsFromShift, coefficientsFrom]
      rw [collectCoeffWordShift_eq]
      rw [coefficientsFromShift_eq count]

def polyOfShift (n : Nat) : List Int :=
  let k := kbitsOf n
  1 :: coefficientsFromShift 24 k 1 (lcgSeed n)

theorem polyOfShift_eq (n : Nat) : polyOfShift n = polyOf n := by
  simp [polyOfShift, polyOf, coefficientsFromShift_eq]

def impl (n : Nat) : Int := resultantFromPolyMul (polyOfShift n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  rw [impl, polyOfShift_eq, resultantFromPolyMul_eq]
  exact (discSpec_eq_resultant n).symm

end Submission
'''

text=prefix+extra
p=OUT/"Submission_v3.lean"
p.write_text(text)
print(f"generated {p} bytes={len(text.encode())}")
