import Collatz.ReturnFixedPointDescent

namespace CollatzFinal
namespace SourceProduct

/-- A repayment certificate compares the end of the composition to its
starting owner. Local descent of the second segment alone is insufficient. -/
theorem composed_affine_return_repayment
    {A₁ B₁ P₁ A₂ B₂ P₂ m m₁ m₂ : Nat}
    (h₁ : P₁ * m₁ = A₁ * m + B₁)
    (h₂ : P₂ * m₂ = A₂ * m₁ + B₂)
    (hcontract : A₂ * A₁ < P₂ * P₁)
    (hguard : A₂ * B₁ + B₂ * P₁ <
      (P₂ * P₁ - A₂ * A₁) * m) :
    m₂ < m := by
  have heq : (P₂ * P₁) * m₂ =
      (A₂ * A₁) * m + (A₂ * B₁ + B₂ * P₁) := by
    calc
      (P₂ * P₁) * m₂ = P₁ * (P₂ * m₂) := by ac_rfl
      _ = P₁ * (A₂ * m₁ + B₂) := by rw [h₂]
      _ = A₂ * (P₁ * m₁) + B₂ * P₁ := by simp only [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm, Nat.add_assoc]
      _ = A₂ * (A₁ * m + B₁) + B₂ * P₁ := by rw [h₁]
      _ = (A₂ * A₁) * m + (A₂ * B₁ + B₂ * P₁) := by ring
  exact affine_return_strict_descent_of_live_floor
    hcontract (Nat.le_refl m) hguard heq

/-- The same certificate can be applied uniformly above a proved floor.
Availability of a matching admitted composition remains a separate premise. -/
theorem composed_affine_return_repayment_of_floor
    {A₁ B₁ P₁ A₂ B₂ P₂ L m m₁ m₂ : Nat}
    (h₁ : P₁ * m₁ = A₁ * m + B₁)
    (h₂ : P₂ * m₂ = A₂ * m₁ + B₂)
    (hcontract : A₂ * A₁ < P₂ * P₁)
    (hfloor : L ≤ m)
    (hguard : A₂ * B₁ + B₂ * P₁ <
      (P₂ * P₁ - A₂ * A₁) * L) :
    m₂ < m := by
  apply composed_affine_return_repayment h₁ h₂ hcontract
  exact Nat.lt_of_lt_of_le hguard
    (Nat.mul_le_mul_left (P₂ * P₁ - A₂ * A₁) hfloor)

#print axioms composed_affine_return_repayment
#print axioms composed_affine_return_repayment_of_floor

/-- A known return residue can certify the whole matching owner cylinder. -/
theorem affine_return_repayment_of_residue
    {A B P modulus rho m m' : Nat}
    (hcontract : A < P)
    (hguard : B < (P - A) * rho)
    (hresidue : m % modulus = rho)
    (heq : P * m' = A * m + B) :
    m' < m := by
  have hfloor : rho ≤ m := by
    rw [← hresidue]
    exact Nat.mod_le m modulus
  exact affine_return_strict_descent_of_live_floor
    hcontract hfloor hguard heq

/-- Concrete 128→168 owner macro from the independently checked overshoot
trace: this law repays at every positive starting owner satisfying its equation.
This theorem does not assert that every source eventually admits this law. -/
theorem overshoot_witness_macro_repayment
    {m m' : Nat}
    (hpositive : 0 < m)
    (heq : 1099511627776 * m' = 282429536481 * m + 592347247211) :
    m' < m := by
  exact affine_return_strict_descent_of_live_floor (L := 1)
    (by decide) (by omega) (by decide) heq

#print axioms affine_return_repayment_of_residue
#print axioms overshoot_witness_macro_repayment

end SourceProduct
end CollatzFinal
