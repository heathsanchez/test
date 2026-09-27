import Collatz.CoefficientCrossing

namespace CollatzFinal
namespace SourceProduct

/-- The two positive quantities whose comparison is coefficient survival. -/
def coefficientNumerator (n k : Nat) : Nat := 3 ^ oddCount n k
def coefficientDenominator (k : Nat) : Nat := 2 ^ k

def CoefficientSurvives (n k : Nat) : Prop :=
  coefficientDenominator k ≤ coefficientNumerator n k

theorem coefficientNumerator_succ_even
    (n k : Nat) (h : iter shortcut k n % 2 = 0) :
    coefficientNumerator n (k + 1) = coefficientNumerator n k := by
  simp [coefficientNumerator, oddCount, h]

theorem coefficientNumerator_succ_odd
    (n k : Nat) (h : iter shortcut k n % 2 ≠ 0) :
    coefficientNumerator n (k + 1) = 3 * coefficientNumerator n k := by
  simp [coefficientNumerator, oddCount, h, Nat.pow_succ, Nat.mul_comm]

theorem coefficientDenominator_succ (k : Nat) :
    coefficientDenominator (k + 1) = 2 * coefficientDenominator k := by
  simp [coefficientDenominator, Nat.pow_succ, Nat.mul_comm]

/-- On an even orbit step, survival asks whether the unchanged numerator still
    covers the doubled dyadic denominator. -/
theorem coefficientSurvives_succ_even
    (n k : Nat) (h : iter shortcut k n % 2 = 0) :
    CoefficientSurvives n (k + 1) ↔
      2 * coefficientDenominator k ≤ coefficientNumerator n k := by
  simp [CoefficientSurvives, coefficientNumerator_succ_even n k h,
    coefficientDenominator_succ]

/-- On an odd orbit step, numerator and denominator are multiplied by 3 and 2. -/
theorem coefficientSurvives_succ_odd
    (n k : Nat) (h : iter shortcut k n % 2 ≠ 0) :
    CoefficientSurvives n (k + 1) ↔
      2 * coefficientDenominator k ≤ 3 * coefficientNumerator n k := by
  simp [CoefficientSurvives, coefficientNumerator_succ_odd n k h,
    coefficientDenominator_succ]

theorem coefficientCrossingAt_iff_not_survives
    (n k : Nat) :
    CoefficientCrossingAt n k ↔ ¬ CoefficientSurvives n k := by
  unfold CoefficientCrossingAt CoefficientSurvives
  simp [coefficientNumerator, coefficientDenominator]
  omega

#print axioms coefficientNumerator_succ_even
#print axioms coefficientNumerator_succ_odd
#print axioms coefficientSurvives_succ_even
#print axioms coefficientSurvives_succ_odd
#print axioms coefficientCrossingAt_iff_not_survives

end SourceProduct
end CollatzFinal
