import Collatz.CoefficientDynamics

namespace CollatzFinal
namespace SourceProduct

/-- Least odd-count exponent whose ternary coefficient covers 2^k. -/
def qmin (k : Nat) : Nat :=
  Nat.find (show ∃ q : Nat, 2 ^ k ≤ 3 ^ q by
    exact ⟨k, by
      have h : 2 ^ k ≤ 3 ^ k := Nat.pow_le_pow_left (by omega) k
      simpa using h⟩)

/-- The threshold really covers the dyadic coefficient. -/
theorem qmin_spec (k : Nat) :
    2 ^ k ≤ 3 ^ qmin k := by
  exact Nat.find_spec (show ∃ q : Nat, 2 ^ k ≤ 3 ^ q by
    exact ⟨k, by
      have h : 2 ^ k ≤ 3 ^ k := Nat.pow_le_pow_left (by omega) k
      simpa using h⟩)

/-- Every exponent below qmin fails to cover 2^k. -/
theorem lt_qmin_fails {k q : Nat} (h : q < qmin k) :
    3 ^ q < 2 ^ k := by
  have hnot : ¬ 2 ^ k ≤ 3 ^ q := by
    intro hq
    have hmin := Nat.find_min' (show ∃ r : Nat, 2 ^ k ≤ 3 ^ r by
      exact ⟨k, by
        have hp : 2 ^ k ≤ 3 ^ k := Nat.pow_le_pow_left (by omega) k
        simpa using hp⟩) hq
    omega
  omega

/-- Coefficient survival is exactly oddCount >= qmin. -/
theorem coefficientSurvives_iff_qmin_le
    (n k : Nat) :
    CoefficientSurvives n k ↔ qmin k ≤ oddCount n k := by
  constructor
  · intro hs
    by_contra h
    have hlt : oddCount n k < qmin k := by omega
    have hf := lt_qmin_fails hlt
    unfold CoefficientSurvives coefficientDenominator coefficientNumerator at hs
    omega
  · intro hq
    unfold CoefficientSurvives coefficientDenominator coefficientNumerator
    exact Nat.le_trans (qmin_spec k) (Nat.pow_le_pow_right (by omega) hq)

/-- qmin can rise by at most one per shortcut step. -/
theorem qmin_succ_le (k : Nat) :
    qmin (k + 1) ≤ qmin k + 1 := by
  apply Nat.find_min'
  have hs := qmin_spec k
  simp only [Nat.pow_succ]
  have h3 : 2 * 2 ^ k ≤ 3 * 3 ^ qmin k := by
    calc
      2 * 2 ^ k ≤ 2 * 3 ^ qmin k := Nat.mul_le_mul_left 2 hs
      _ ≤ 3 * 3 ^ qmin k := by omega
  simpa [Nat.mul_comm] using h3

/-- qmin never falls as depth increases. -/
theorem qmin_le_succ (k : Nat) :
    qmin k ≤ qmin (k + 1) := by
  by_contra h
  have hlt : qmin (k + 1) < qmin k := by omega
  have hf := lt_qmin_fails hlt
  have hs := qmin_spec (k + 1)
  simp only [Nat.pow_succ] at hs
  have hpow : 3 ^ qmin (k + 1) < 2 ^ k := hf
  omega

/-- The deterministic boundary bit is always 0 or 1. -/
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

/-- On a surviving prefix, surplus above qmin is an ordinary natural number. -/
def surplus (n k : Nat) : Nat := oddCount n k - qmin k

/-- Exact one-step surplus recurrence on a surviving successor. -/
theorem surplus_succ
    (n k : Nat)
    (hs : CoefficientSurvives n (k + 1)) :
    surplus n (k + 1) =
      surplus n k +
        (if iter shortcut k n % 2 = 0 then 0 else 1) -
        boundaryBit k := by
  have hnext : qmin (k + 1) ≤ oddCount n (k + 1) :=
    (coefficientSurvives_iff_qmin_le n (k + 1)).1 hs
  have hq := qmin_succ_eq k
  unfold surplus
  simp only [oddCount]
  split <;> omega

#print axioms qmin_spec
#print axioms lt_qmin_fails
#print axioms coefficientSurvives_iff_qmin_le
#print axioms qmin_succ_le
#print axioms qmin_le_succ
#print axioms boundaryBit_lt_two
#print axioms qmin_succ_eq
#print axioms surplus_succ

end SourceProduct
end CollatzFinal
