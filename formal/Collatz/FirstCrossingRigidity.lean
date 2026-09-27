import Collatz.SurvivalDeficit

namespace CollatzFinal
namespace SourceProduct

/-- The actual orbit parity bit is binary. -/
theorem orbitOddBit_lt_two (n k : Nat) :
    orbitOddBit n k < 2 := by
  unfold orbitOddBit
  split <;> omega

/-- A first coefficient crossing is rigid. Immediately before the crossing
the signed surplus is exactly zero; the deterministic threshold rises, the
actual orbit takes an even step, and the surplus lands exactly at -1. -/
theorem first_crossing_rigidity
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    signedSurplus n k = 0 ∧
    boundaryBit k = 1 ∧
    orbitOddBit n k = 0 ∧
    signedSurplus n (k + 1) = -1 := by
  have hnotCrossPrev : ¬ CoefficientCrossingAt n k :=
    hfirst.2 k (Nat.lt_succ_self k)
  have hsurvPrev : CoefficientSurvives n k := by
    apply Classical.byContradiction
    intro hnot
    exact hnotCrossPrev
      ((coefficientCrossingAt_iff_not_survives n k).2 hnot)
  have hnotSurvNow : ¬ CoefficientSurvives n (k + 1) :=
    (coefficientCrossingAt_iff_not_survives n (k + 1)).1 hfirst.1
  have hsPrev : 0 ≤ signedSurplus n k :=
    (coefficientSurvives_iff_signedSurplus_nonnegative n k).1 hsurvPrev
  have hsNowNot : ¬ 0 ≤ signedSurplus n (k + 1) := by
    intro hs
    exact hnotSurvNow
      ((coefficientSurvives_iff_signedSurplus_nonnegative n (k + 1)).2 hs)
  have hrec := signedSurplus_succ n k
  have hb := boundaryBit_lt_two k
  have ho := orbitOddBit_lt_two n k
  constructor
  · omega
  constructor
  · omega
  constructor
  · omega
  · omega

/-- The last source-orbit step at every first coefficient crossing is even. -/
theorem first_crossing_last_step_even
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    iter shortcut k n % 2 = 0 := by
  have hbit := (first_crossing_rigidity hfirst).2.2.1
  unfold orbitOddBit at hbit
  by_cases h : iter shortcut k n % 2 = 0
  · exact h
  · simp [h] at hbit

/-- At a first crossing the endpoint is literally half of the preceding
ordinary-orbit value. -/
theorem first_crossing_endpoint_eq_half_previous
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    iter shortcut (k + 1) n = iter shortcut k n / 2 := by
  rw [iter_succ_last]
  unfold shortcut
  simp [first_crossing_last_step_even hfirst]

/-- First-crossing strict descent is exactly failure to reach twice the source
immediately before the forced final even step. -/
theorem first_crossing_descends_iff_previous_lt_double
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    iter shortcut (k + 1) n < n ↔
      iter shortcut k n < 2 * n := by
  rw [first_crossing_endpoint_eq_half_previous hfirst]
  have heven := first_crossing_last_step_even hfirst
  omega

/-- Dually, a nondescending first crossing is exactly a pre-crossing value at
least twice the source. This is the ordinary-orbit form of the M>=0 branch. -/
theorem first_crossing_nondescending_iff_previous_ge_double
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    n ≤ iter shortcut (k + 1) n ↔
      2 * n ≤ iter shortcut k n := by
  rw [first_crossing_endpoint_eq_half_previous hfirst]
  have heven := first_crossing_last_step_even hfirst
  omega

/-- Universally, the odd count at first crossing is exactly one below the
native dyadic threshold qmin. This promotes the old finite q=floor(alpha*k)
phenomenon to an exact all-depth statement without real logarithms. -/
theorem first_crossing_oddCount_eq_threshold_minus_one
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    oddCount n (k + 1) + 1 = qmin (k + 1) := by
  have hs := (first_crossing_rigidity hfirst).2.2.2
  unfold signedSurplus at hs
  omega

/-- Immediately before first crossing the orbit odd count is exactly qmin. -/
theorem first_crossing_previous_oddCount_eq_qmin
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    oddCount n k = qmin k := by
  have hs := (first_crossing_rigidity hfirst).1
  unfold signedSurplus at hs
  omega

/-- Exact coefficient band at first crossing: the same odd count covered the
previous dyadic scale but fails at the doubled scale. -/
theorem first_crossing_exact_band
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    2 ^ k ≤ 3 ^ oddCount n (k + 1) ∧
    3 ^ oddCount n (k + 1) < 2 ^ (k + 1) := by
  have heven := first_crossing_last_step_even hfirst
  have hq : oddCount n (k + 1) = oddCount n k := by
    simp [oddCount, heven]
  have hnotCrossPrev : ¬ CoefficientCrossingAt n k :=
    hfirst.2 k (Nat.lt_succ_self k)
  have hprev : 2 ^ k ≤ 3 ^ oddCount n k := by
    unfold CoefficientCrossingAt at hnotCrossPrev
    omega
  constructor
  · simpa [hq] using hprev
  · exact hfirst.1

#print axioms orbitOddBit_lt_two
#print axioms first_crossing_rigidity
#print axioms first_crossing_last_step_even
#print axioms first_crossing_endpoint_eq_half_previous
#print axioms first_crossing_descends_iff_previous_lt_double
#print axioms first_crossing_nondescending_iff_previous_ge_double
#print axioms first_crossing_oddCount_eq_threshold_minus_one
#print axioms first_crossing_previous_oddCount_eq_qmin
#print axioms first_crossing_exact_band

end SourceProduct
end CollatzFinal
