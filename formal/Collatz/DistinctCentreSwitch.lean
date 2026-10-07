import Collatz.SameCentreMacro

namespace CollatzFinal
namespace SourceProduct

/-- A power-of-two return denominator minus an odd multiplier is odd. -/
theorem return_denominator_coefficient_odd
    {A : Int} {D : Nat}
    (hD : 0 < D)
    (hA : A % 2 = 1) :
    ((2 : Int) ^ D - A) % 2 = 1 := by
  cases D with
  | zero =>
      omega
  | succ k =>
      have hp := pow_two_succ_even k
      omega

/-- Odd multiplication preserves dyadic order in both directions. -/
theorem dyadic_order_cancel_odd
    {x A : Int} {v : Nat}
    (hAx : DyadicOrder (A * x) v)
    (hA : A % 2 = 1) :
    DyadicOrder x v := by
  have hxne : x ≠ 0 := by
    intro hx
    subst x
    have hne := dyadic_order_nonzero hAx
    simp at hne
  obtain ⟨w, hw⟩ := dyadic_order_exists hxne
  have hAw : DyadicOrder (A * x) w := dyadic_mul_odd hw hA
  have he : w = v := dyadic_order_unique hAw hAx
  simpa [he] using hw

/-- Denominator-free identity relating two affine-centre defects at one owner.
Writing Cᵢ=Pᵢ-Aᵢ and Δᵢ=Cᵢ*m-Bᵢ:
  C₂ Δ₁ = C₁ Δ₂ + J₁₂.
-/
theorem returnDefect_pair_injection
    (A₁ B₁ P₁ A₂ B₂ P₂ m : Int) :
    (P₂ - A₂) * returnDefect A₁ B₁ P₁ m =
      (P₁ - A₁) * returnDefect A₂ B₂ P₂ m +
        returnInjection A₁ B₁ P₁ A₂ B₂ P₂ := by
  simp only [returnDefect, returnInjection, Int.mul_sub]
  have hcross :
      (P₂ - A₂) * ((P₁ - A₁) * m) =
        (P₁ - A₁) * ((P₂ - A₂) * m) := by
    rw [← Int.mul_assoc,
      Int.mul_comm (P₂ - A₂) (P₁ - A₁),
      Int.mul_assoc]
  rw [hcross]
  omega

/-- Nonzero exact admission to one deterministic return cylinder.
The own-centre defect is known through at least the law's forced D+1 bits. -/
def ReturnCylinderAdmissible
    (A B : Int) (D : Nat) (m : Int) : Prop :=
  ∃ w,
    D + 1 ≤ w ∧
    DyadicOrder
      (returnDefect A B ((2 : Int) ^ D) m) w

/-- A separated new return cylinder forces the old-centre defect order to be
exactly the centre-separation order.

This is the universal algebra behind V58's "next centre is closer" observation.
The only premises are:
* both return multipliers are odd and depths are positive;
* the new owner is admitted by its own cylinder through D₂+1 bits;
* the centre-separation injection has order h below that forced precision.

No corpus/rank assumption appears. -/
theorem separated_admissible_switch_old_order
    {A₁ B₁ A₂ B₂ m : Int}
    {D₁ D₂ h : Nat}
    (hD₁ : 0 < D₁)
    (hD₂ : 0 < D₂)
    (hA₁ : A₁ % 2 = 1)
    (hA₂ : A₂ % 2 = 1)
    (hadm : ReturnCylinderAdmissible A₂ B₂ D₂ m)
    (hJ :
      DyadicOrder
        (returnInjection
          A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h)
    (hsep : h < D₂ + 1) :
    DyadicOrder
      (returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) h := by
  obtain ⟨w, hwD, hw⟩ := hadm
  have hhw : h < w := by omega
  have hC₁ :
      (((2 : Int) ^ D₁) - A₁) % 2 = 1 :=
    return_denominator_coefficient_odd hD₁ hA₁
  have hC₂ :
      (((2 : Int) ^ D₂) - A₂) % 2 = 1 :=
    return_denominator_coefficient_odd hD₂ hA₂
  have hnewMul :
      DyadicOrder
        ((((2 : Int) ^ D₁) - A₁) *
          returnDefect A₂ B₂ ((2 : Int) ^ D₂) m) w :=
    dyadic_mul_odd hw hC₁
  have hsum :
      DyadicOrder
        ((((2 : Int) ^ D₁) - A₁) *
            returnDefect A₂ B₂ ((2 : Int) ^ D₂) m +
          returnInjection
            A₁ B₁ ((2 : Int) ^ D₁)
            A₂ B₂ ((2 : Int) ^ D₂)) h := by
    have hz := dyadic_sum_low hJ hnewMul hhw
    simpa [Int.add_comm] using hz
  have hprod :
      DyadicOrder
        ((((2 : Int) ^ D₂) - A₂) *
          returnDefect A₁ B₁ ((2 : Int) ^ D₁) m) h := by
    rw [returnDefect_pair_injection]
    exact hsum
  exact dyadic_order_cancel_odd hprod hC₂

/-- Therefore the new centre has strictly greater pulled-source precision than
the old centre at the same prefix depth. -/
theorem separated_admissible_switch_precision_gain
    {A₁ B₁ A₂ B₂ m : Int}
    {H D₁ D₂ h : Nat}
    (hD₁ : 0 < D₁)
    (hD₂ : 0 < D₂)
    (hA₁ : A₁ % 2 = 1)
    (hA₂ : A₂ % 2 = 1)
    (hadm : ReturnCylinderAdmissible A₂ B₂ D₂ m)
    (hJ :
      DyadicOrder
        (returnInjection
          A₁ B₁ ((2 : Int) ^ D₁)
          A₂ B₂ ((2 : Int) ^ D₂)) h)
    (hsep : h < D₂ + 1) :
    ∃ w,
      DyadicOrder
        (returnDefect A₂ B₂ ((2 : Int) ^ D₂) m) w ∧
      pulledPrecision H h < pulledPrecision H w := by
  obtain ⟨w, hwD, hw⟩ := hadm
  refine ⟨w, hw, ?_⟩
  have hhw : h < w := by omega
  unfold pulledPrecision
  omega

#print axioms return_denominator_coefficient_odd
#print axioms dyadic_order_cancel_odd
#print axioms returnDefect_pair_injection
#print axioms separated_admissible_switch_old_order
#print axioms separated_admissible_switch_precision_gain

end SourceProduct
end CollatzFinal
