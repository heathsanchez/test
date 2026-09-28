import Collatz.OwnerFourThirdsBoundary

namespace CollatzFinal
namespace SourceProduct

/-- The exact strengthened local invariant suggested by the V17 Crystal frontier.

Only protected odd states pay the extra three units of source budget.  This is
stronger than the protected four-thirds cap exactly where it matters: an odd
state is forbidden when the remaining budget is 0, 1, or 2.

This is an explicit premise, not asserted as proved by finite Crystal data. -/
def ProtectedOddBudgetGap : Prop :=
  ∀ n k, 1 < n →
    DirectQuarterProtectedPrefix n k →
    iter shortcut k n % 2 = 1 →
    3 * oddCount n k + 3 ≤ 4 * n

/-- The +3 protected odd-budget gap forces the exact four-thirds boundary to
be even.  At q=floor(4n/3), Euclidean division gives
4n < 3(q+1) = 3q+3, contradicting the gap if the endpoint were odd. -/
theorem four_thirds_boundary_even_of_protected_odd_budget_gap
    (hGap : ProtectedOddBudgetGap) :
    FourThirdsProtectedBoundaryEven := by
  intro n k hgt hprot hq
  have hmodlt :
      iter shortcut k n % 2 < 2 :=
    Nat.mod_lt _ (by decide)
  by_cases heven : iter shortcut k n % 2 = 0
  · exact heven
  · have hodd : iter shortcut k n % 2 = 1 := by omega
    have hgap := hGap n k hgt hprot hodd
    have hfloor := four_thirds_floor_boundary n
    rw [hq] at hgap
    omega

/-- Therefore the V17 odd-budget invariant alone closes positive Collatz. -/
theorem reaches_one_of_protected_odd_budget_gap
    (hGap : ProtectedOddBudgetGap) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_four_thirds_protected_boundary_even
    (four_thirds_boundary_even_of_protected_odd_budget_gap hGap)

#print axioms four_thirds_boundary_even_of_protected_odd_budget_gap
#print axioms reaches_one_of_protected_odd_budget_gap

end SourceProduct
end CollatzFinal
