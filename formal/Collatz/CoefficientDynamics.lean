import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-- The two positive quantities whose comparison defines coefficient survival. -/
def coefficientNumerator (n k : Nat) : Nat := 3 ^ oddCount n k
def coefficientDenominator (k : Nat) : Nat := 2 ^ k

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

/-- Signed coefficient gap: nonnegative means no coefficient crossing yet. -/
def coefficientGap (n k : Nat) : Int :=
  (coefficientNumerator n k : Int) - (coefficientDenominator k : Int)

theorem coefficientGap_succ_even
    (n k : Nat) (h : iter shortcut k n % 2 = 0) :
    coefficientGap n (k + 1) =
      coefficientGap n k - coefficientDenominator k := by
  rw [coefficientGap, coefficientGap,
      coefficientNumerator_succ_even n k h,
      coefficientDenominator_succ]
  push_cast
  ring

theorem coefficientGap_succ_odd
    (n k : Nat) (h : iter shortcut k n % 2 ≠ 0) :
    coefficientGap n (k + 1) =
      3 * coefficientGap n k + coefficientDenominator k := by
  rw [coefficientGap, coefficientGap,
      coefficientNumerator_succ_odd n k h,
      coefficientDenominator_succ]
  push_cast
  ring

theorem coefficientCrossingAt_iff_gap_negative
    (n k : Nat) :
    CoefficientCrossingAt n k ↔ coefficientGap n k < 0 := by
  unfold CoefficientCrossingAt coefficientGap coefficientNumerator coefficientDenominator
  omega

#print axioms coefficientGap_succ_even
#print axioms coefficientGap_succ_odd
#print axioms coefficientCrossingAt_iff_gap_negative

end SourceProduct
end CollatzFinal
