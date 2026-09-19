#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"generated"
OUT.mkdir(parents=True,exist_ok=True)
runpy.run_path(str(ROOT/"shift_v3.py"))
src=(OUT/"Submission_v3.lean").read_text()

old='''def impl (n : Nat) : Int := resultantFromPolyMul (polyOfShift n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  rw [impl, polyOfShift_eq, resultantFromPolyMul_eq]
  exact (discSpec_eq_resultant n).symm

end Submission
'''
new=r'''/-- Generated inputs are monic degree 24, so the generic initial
trim/shape gate can be discharged once in the proof instead of during every
scored evaluation. -/
def resultantFromPolyFixed24 (p : List Int) : Int :=
  let derivative := derivHL p
  match normalResultantGoMul 25 true p derivative with
  | some resultant => resultant
  | none => bareissDet (monicReducedSylvester p derivative)

theorem coefficientsFromShift_length :
    ∀ count k index state,
      (coefficientsFromShift count k index state).length = count
  | 0, _, _, _ => rfl
  | count + 1, k, index, state => by
      simp [coefficientsFromShift, coefficientsFromShift_length count]

theorem polyOfShift_length (n : Nat) : (polyOfShift n).length = 25 := by
  simp [polyOfShift, coefficientsFromShift_length]

theorem trimLeading_polyOfShift (n : Nat) :
    trimLeading (polyOfShift n) = polyOfShift n := by
  simp [polyOfShift, trimLeading]

theorem derivHL_polyOfShift_length (n : Nat) :
    (derivHL (polyOfShift n)).length = 24 := by
  simp [derivHL, polyOfShift_length]

theorem trimLeading_derivHL_polyOfShift (n : Nat) :
    trimLeading (derivHL (polyOfShift n)) = derivHL (polyOfShift n) := by
  unfold derivHL
  rw [polyOfShift_length]
  simp [polyOfShift, trimLeading]

theorem resultantFromPolyFixed24_eq (n : Nat) :
    resultantFromPolyFixed24 (polyOfShift n) =
      resultantFromPolyMul (polyOfShift n) := by
  unfold resultantFromPolyFixed24 resultantFromPolyMul normalResultantMul
  rw [trimLeading_polyOfShift, trimLeading_derivHL_polyOfShift]
  have hd : (derivHL (polyOfShift n)).length = 24 :=
    derivHL_polyOfShift_length n
  have hp : (polyOfShift n).length = 25 := polyOfShift_length n
  simp [hd, hp]

def impl (n : Nat) : Int := resultantFromPolyFixed24 (polyOfShift n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  rw [impl, resultantFromPolyFixed24_eq, polyOfShift_eq,
      resultantFromPolyMul_eq]
  exact (discSpec_eq_resultant n).symm

end Submission
'''
if old not in src:
    raise SystemExit("V3 final block missing")
src=src.replace(old,new,1)
p=OUT/"Submission_v4.lean"
p.write_text(src)
print(f"generated {p} bytes={len(src.encode())}")
