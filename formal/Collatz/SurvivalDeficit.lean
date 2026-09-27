import Collatz.CoefficientDynamics

namespace CollatzFinal
namespace SourceProduct

/-- Least required odd count, defined constructively in the native Lean core.
It either stays put or rises by one at each depth. -/
def qmin : Nat → Nat
  | 0 => 0
  | k + 1 =>
      if 2 ^ (k + 1) ≤ 3 ^ qmin k then qmin k else qmin k + 1

/-- The threshold covers the dyadic coefficient. -/
theorem qmin_spec : ∀ k : Nat, 2 ^ k ≤ 3 ^ qmin k
  | 0 => by simp [qmin]
  | k + 1 => by
      by_cases h : 2 ^ (k + 1) ≤ 3 ^ qmin k
      · simpa [qmin, h] using h
      · have ih := qmin_spec k
        have h2 : 2 * 2 ^ k ≤ 2 * 3 ^ qmin k :=
          Nat.mul_le_mul_left 2 ih
        have h3 : 2 * 3 ^ qmin k ≤ 3 * 3 ^ qmin k := by
          omega
        have hh := Nat.le_trans h2 h3
        simpa [qmin, h, Nat.pow_succ, Nat.mul_comm] using hh

/-- Every exponent below qmin fails to cover the dyadic coefficient. -/
theorem lt_qmin_fails {k q : Nat} (h : q < qmin k) :
    3 ^ q < 2 ^ k := by
  induction k generalizing q with
  | zero =>
      simp [qmin] at h
  | succ k ih =>
      by_cases hb : 2 ^ (k + 1) ≤ 3 ^ qmin k
      · have hq : q < qmin k := by
          simpa [qmin, hb] using h
        have hh := ih hq
        have hp : 2 ^ k < 2 ^ (k + 1) := by
          simp [Nat.pow_succ]
        exact Nat.lt_trans hh hp
      · have hq : q ≤ qmin k := by
          have hlt : q < qmin k + 1 := by
            simpa [qmin, hb] using h
          omega
        have hp : 3 ^ q ≤ 3 ^ qmin k :=
          Nat.pow_le_pow_right (by omega) hq
        have hb' : 3 ^ qmin k < 2 ^ (k + 1) := by
          omega
        exact Nat.lt_of_le_of_lt hp hb'

/-- Coefficient survival is exactly oddCount >= qmin. -/
theorem coefficientSurvives_iff_qmin_le
    (n k : Nat) :
    CoefficientSurvives n k ↔ qmin k ≤ oddCount n k := by
  constructor
  · intro hs
    by_cases h : qmin k ≤ oddCount n k
    · exact h
    · have hlt : oddCount n k < qmin k := by omega
      have hf := lt_qmin_fails hlt
      unfold CoefficientSurvives coefficientDenominator coefficientNumerator at hs
      omega
  · intro hq
    unfold CoefficientSurvives coefficientDenominator coefficientNumerator
    exact Nat.le_trans (qmin_spec k) (Nat.pow_le_pow_right (by omega) hq)

/-- qmin can rise by at most one per shortcut step. -/
theorem qmin_succ_le (k : Nat) :
    qmin (k + 1) ≤ qmin k + 1 := by
  by_cases h : 2 ^ (k + 1) ≤ 3 ^ qmin k <;>
    simp [qmin, h]

/-- qmin never falls. -/
theorem qmin_le_succ (k : Nat) :
    qmin k ≤ qmin (k + 1) := by
  by_cases h : 2 ^ (k + 1) ≤ 3 ^ qmin k <;>
    simp [qmin, h]

/-- The deterministic threshold bit is 0 or 1. -/
def boundaryBit (k : Nat) : Nat := qmin (k + 1) - qmin k

theorem boundaryBit_lt_two (k : Nat) :
    boundaryBit k < 2 := by
  unfold boundaryBit
  have hlo := qmin_le_succ k
  have hhi := qmin_succ_le k
  omega

/-- Exact threshold update. -/
theorem qmin_succ_eq (k : Nat) :
    qmin (k + 1) = qmin k + boundaryBit k := by
  unfold boundaryBit
  have h := qmin_le_succ k
  omega

/-- The actual orbit contributes exactly one odd-count bit per step. -/
def orbitOddBit (n k : Nat) : Nat :=
  if iter shortcut k n % 2 = 0 then 0 else 1

/-- Signed surplus removes the truncation artefact of Nat subtraction. -/
def signedSurplus (n k : Nat) : Int :=
  (oddCount n k : Int) - (qmin k : Int)

/-- Survival is exactly nonnegative signed surplus. -/
theorem coefficientSurvives_iff_signedSurplus_nonnegative
    (n k : Nat) :
    CoefficientSurvives n k ↔ 0 ≤ signedSurplus n k := by
  rw [coefficientSurvives_iff_qmin_le]
  unfold signedSurplus
  omega

/-- Exact one-step scalar recurrence. Nothing remains here except the actual
orbit parity bit versus the deterministic coefficient-boundary bit. -/
theorem signedSurplus_succ (n k : Nat) :
    signedSurplus n (k + 1) =
      signedSurplus n k + (orbitOddBit n k : Int) - (boundaryBit k : Int) := by
  unfold signedSurplus orbitOddBit
  rw [qmin_succ_eq]
  simp only [oddCount]
  split <;> simp <;> omega

#print axioms qmin_spec
#print axioms lt_qmin_fails
#print axioms coefficientSurvives_iff_qmin_le
#print axioms qmin_succ_le
#print axioms qmin_le_succ
#print axioms boundaryBit_lt_two
#print axioms qmin_succ_eq
#print axioms coefficientSurvives_iff_signedSurplus_nonnegative
#print axioms signedSurplus_succ

end SourceProduct
end CollatzFinal
