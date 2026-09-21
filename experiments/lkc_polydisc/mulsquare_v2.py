#!/usr/bin/env python3
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "generated"
OUT.mkdir(parents=True, exist_ok=True)
runpy.run_path(str(ROOT / "fixedsign_v1.py"))

text = r'''import Spec

namespace Submission

/-- Brown normal PRS with the exact same recurrence, specializing x^2 to x*x. -/
def normalResultantGoMul :
    Nat → Bool → List Int → List Int → Option Int
  | 0, _, _, _ => none
  | fuel + 1, initial, f, g =>
      match pseudoRemainder f g with
      | none => none
      | some raw =>
          let divided :=
            if initial then some raw
            else
              let x := f.headD 0
              exactDividePolynomial (x * x) raw
          match divided with
          | none => none
          | some coefficients =>
              match trimLeading coefficients with
              | [] => some 0
              | remainder =>
                  if remainder.length + 1 == g.length then
                    match remainder with
                    | [constant] => some constant
                    | _ => normalResultantGoMul fuel false g remainder
                  else
                    none

theorem int_pow_two (x : Int) : x ^ 2 = x * x := by
  simp [Int.pow_succ]

theorem normalResultantGoMul_eq :
    ∀ fuel initial f g,
      normalResultantGoMul fuel initial f g =
        normalResultantGo fuel initial f g
  | 0, _, _, _ => rfl
  | fuel + 1, initial, f, g => by
      simp only [normalResultantGoMul, normalResultantGo]
      rw [int_pow_two]
      split <;> simp_all [normalResultantGoMul_eq fuel] <;> rfl

def normalResultantMul (f g : List Int) : Option Int :=
  let f := trimLeading f
  let g := trimLeading g
  if f.length == g.length + 1 && !g.isEmpty then
    normalResultantGoMul (g.length + 1) true f g
  else
    none

theorem normalResultantMul_eq (f g : List Int) :
    normalResultantMul f g = normalResultant f g := by
  simp [normalResultantMul, normalResultant, normalResultantGoMul_eq]

def resultantFromPolyMul (p : List Int) : Int :=
  let derivative := derivHL p
  match normalResultantMul p derivative with
  | some resultant => resultant
  | none => bareissDet (monicReducedSylvester p derivative)

theorem resultantFromPolyMul_eq (p : List Int) :
    resultantFromPolyMul p = resultantFromPoly p := by
  change
    (match normalResultantMul p (derivHL p) with
     | some resultant => resultant
     | none => bareissDet (monicReducedSylvester p (derivHL p))) =
    (match normalResultant p (derivHL p) with
     | some resultant => resultant
     | none => bareissDet (monicReducedSylvester p (derivHL p)))
  rw [normalResultantMul_eq]

theorem coefficientsFrom_length :
    ∀ count k index state,
      (coefficientsFrom count k index state).length = count
  | 0, _, _, _ => rfl
  | count + 1, k, index, state => by
      simp [coefficientsFrom, coefficientsFrom_length count]

theorem polyOf_length (n : Nat) : (polyOf n).length = 25 := by
  simp [polyOf, coefficientsFrom_length]

theorem discSpec_eq_resultant (n : Nat) :
    discSpec n = resultantFromPoly (polyOf n) := by
  unfold discSpec discriminantFromPoly
  simp [polyOf_length]

def impl (n : Nat) : Int := resultantFromPolyMul (polyOf n)

theorem impl_correct : ∀ n, impl n = discSpec n := by
  intro n
  rw [impl, resultantFromPolyMul_eq]
  exact (discSpec_eq_resultant n).symm

end Submission
'''
path = OUT / "Submission_v2.lean"
path.write_text(text)
print(f"generated {path} bytes={len(text.encode())}")
