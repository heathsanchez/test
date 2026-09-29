import Collatz.AffineBudget

namespace CollatzFinal
namespace SourceProduct

/-- Signed defect of an affine return law
      P * m' = A * m + B
at a current owner coordinate m. -/
def returnDefect (A B P m : Int) : Int :=
  (P - A) * m - B

/-- Cross-centre injection numerator for two affine return laws.

Writing C_i = P_i - A_i, this is
      J_12 = C_1 * B_2 - C_2 * B_1.
It is the denominator-free coordinate-change separator between the two
rational fixed points B_i / C_i. -/
def returnInjection
    (A₁ B₁ P₁ A₂ B₂ P₂ : Int) : Int :=
  (P₁ - A₁) * B₂ - (P₂ - A₂) * B₁

/-- Exact defect transport under a switch to a second affine return law.

If the second return sends m to m',
      P₂ * m' = A₂ * m + B₂,
then the defect measured relative to the first return centre obeys
      P₂ * Δ₁(m') = A₂ * Δ₁(m) + J₁₂.

This is the integer identity behind the V31/V34/A8 recharge and centre-switch
calculi.  No valuation or positivity assumptions are needed. -/
theorem returnDefect_transport
    (A₁ B₁ P₁ A₂ B₂ P₂ m m' : Int)
    (hstep : P₂ * m' = A₂ * m + B₂) :
    P₂ * returnDefect A₁ B₁ P₁ m' =
      A₂ * returnDefect A₁ B₁ P₁ m +
        returnInjection A₁ B₁ P₁ A₂ B₂ P₂ := by
  simp only [returnDefect, returnInjection]
  calc
    P₂ * ((P₁ - A₁) * m' - B₁)
        = (P₁ - A₁) * (P₂ * m') - P₂ * B₁ := by
            simp only [Int.mul_sub]
            have hcross :
                P₂ * ((P₁ - A₁) * m') =
                  (P₁ - A₁) * (P₂ * m') := by
              rw [← Int.mul_assoc, Int.mul_comm P₂ (P₁ - A₁), Int.mul_assoc]
            rw [hcross]
    _ = (P₁ - A₁) * (A₂ * m + B₂) - P₂ * B₁ := by
          rw [hstep]
    _ = A₂ * ((P₁ - A₁) * m - B₁) +
          ((P₁ - A₁) * B₂ - (P₂ - A₂) * B₁) := by
          simp only [Int.mul_add, Int.mul_sub, Int.sub_mul, Int.mul_assoc]
          have hcross :
              (P₁ - A₁) * (A₂ * m) =
                A₂ * ((P₁ - A₁) * m) := by
            rw [← Int.mul_assoc, Int.mul_comm (P₁ - A₁) A₂, Int.mul_assoc]
          rw [hcross]
          omega

/-- A return law transports its own defect multiplicatively:
      P * Δ(m') = A * Δ(m).
This is the zero-injection specialization of [returnDefect_transport]. -/
theorem returnDefect_self_scale
    (A B P m m' : Int)
    (hstep : P * m' = A * m + B) :
    P * returnDefect A B P m' =
      A * returnDefect A B P m := by
  have h := returnDefect_transport
    A B P A B P m m' hstep
  simpa [returnInjection] using h

/-- The injection of a return law with itself is zero. -/
theorem returnInjection_self
    (A B P : Int) :
    returnInjection A B P A B P = 0 := by
  simp [returnInjection]

#print axioms returnDefect_transport
#print axioms returnDefect_self_scale
#print axioms returnInjection_self

end SourceProduct
end CollatzFinal
