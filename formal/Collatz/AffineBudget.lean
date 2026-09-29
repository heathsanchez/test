import Collatz.ReturnFixedPointDescent

namespace CollatzFinal
namespace SourceProduct

/-- Signed descent budget for an affine return law
      P * m' = A * m + B
relative to a declared live floor L.

Positive budget is exactly the fixed-point-below-floor inequality
      B < (P - A) * L
when the coefficient is contracting.  We use Int here so negative recharge
budgets remain first-class instead of being truncated by Nat subtraction. -/
def affineBudget (A B P L : Int) : Int :=
  (P - A) * L - B

/-- Exact composition law for descent budgets.

If
    P₁ y = A₁ x + B₁
and
    P₂ z = A₂ y + B₂,
then the composite law has
    P = P₁ P₂,
    A = A₂ A₁,
    B = A₂ B₁ + B₂ P₁.

The budget of the composite is therefore the weighted sum
    W₁₂ = A₂ W₁ + P₁ W₂.

This is the algebraic state that V47/V49 were discovering empirically:
individual return laws may recharge (negative budget), while a later
cumulative block can cross to positive budget and then descend by
[affine_return_strict_descent_of_live_floor]. -/
theorem affineBudget_compose
    (A₁ B₁ P₁ A₂ B₂ P₂ L : Int) :
    affineBudget (A₂ * A₁) (A₂ * B₁ + B₂ * P₁) (P₁ * P₂) L =
      A₂ * affineBudget A₁ B₁ P₁ L +
      P₁ * affineBudget A₂ B₂ P₂ L := by
  simp [affineBudget]
  ring

/-- Expanded form of the same identity, useful for certificate emitters that
store the composite affine triple directly. -/
theorem affineBudget_composite_expanded
    (A₁ B₁ P₁ A₂ B₂ P₂ L : Int) :
    ((P₁ * P₂ - A₂ * A₁) * L - (A₂ * B₁ + B₂ * P₁)) =
      A₂ * ((P₁ - A₁) * L - B₁) +
      P₁ * ((P₂ - A₂) * L - B₂) := by
  ring

/-- Positive signed budget is the integer form of the strict fixed-floor
inequality.  This keeps the executable and theorem-facing certificates aligned
without introducing a second notion of progress. -/
theorem affineBudget_pos_iff
    (A B P L : Int) :
    0 < affineBudget A B P L ↔ B < (P - A) * L := by
  simp [affineBudget]

/-- A positive composite budget cannot be synthesized from two nonpositive
component budgets when the affine composition weights are nonnegative.

Together with [affineBudget_compose], this is the key consequence-pruning
step: any cumulative fixed-floor descent certificate contains an individual
return whose fixed-floor budget is already positive.  Hence an infinite path
with every individual return budget <= 0 can never acquire positive budget
merely by batching more returns. -/
theorem affineBudget_compose_pos_implies_component_pos
    (A₁ B₁ P₁ A₂ B₂ P₂ L : Int)
    (hA₂ : 0 ≤ A₂)
    (hP₁ : 0 ≤ P₁)
    (hpos :
      0 < affineBudget (A₂ * A₁) (A₂ * B₁ + B₂ * P₁) (P₁ * P₂) L) :
    0 < affineBudget A₁ B₁ P₁ L ∨
      0 < affineBudget A₂ B₂ P₂ L := by
  rw [affineBudget_compose] at hpos
  by_cases h₁ : 0 < affineBudget A₁ B₁ P₁ L
  · exact Or.inl h₁
  · right
    by_contra h₂
    have hn₁ : affineBudget A₁ B₁ P₁ L ≤ 0 := le_of_not_gt h₁
    have hn₂ : affineBudget A₂ B₂ P₂ L ≤ 0 := le_of_not_gt h₂
    have hw₁ :
        A₂ * affineBudget A₁ B₁ P₁ L ≤ 0 :=
      mul_nonpos_of_nonneg_of_nonpos hA₂ hn₁
    have hw₂ :
        P₁ * affineBudget A₂ B₂ P₂ L ≤ 0 :=
      mul_nonpos_of_nonneg_of_nonpos hP₁ hn₂
    exact (not_lt_of_ge (add_nonpos hw₁ hw₂)) hpos


#print axioms affineBudget_compose
#print axioms affineBudget_composite_expanded
#print axioms affineBudget_pos_iff

end SourceProduct
end CollatzFinal
