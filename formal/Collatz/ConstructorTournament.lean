import Collatz.AssembledConstructorCloseout

namespace CollatzFinal
namespace SourceProduct

/-- Source-independent constructor target isolated by the large-crossing tournament.

Every positive endpoint in the exact large-hard scalar class eventually reaches
a positive value at most three quarters of itself.  This is deliberately stated
as a constructor capability, not as a rank. -/
def ThreeQuarterFuture7 : Prop :=
  ∀ y, 0 < y → y % 12 = 7 →
    ∃ a, 0 < iter shortcut a y ∧ 4 * iter shortcut a y ≤ 3 * y

/-- The three-quarter future capability closes the entire large-source
hard-first-crossing constructor domain.

Indeed Lean already supplies 3*y < 4*n on that domain.  Thus any future
p <= 3*y/4 satisfies p<n and is a direct OrdinaryExit, even if the first
coefficient crossing itself did not descend. -/
theorem large_crossing_coverage_of_three_quarter_future7
    (h34 : ThreeQuarterFuture7) :
    LargeCrossingConstructorCoverage := by
  intro n k hgt hhard hq hwin hmod
  let y := iter shortcut (k + 1) n
  have hypos : 0 < y := by
    dsimp [y]
    exact iter_positive shortcut shortcut_positive (k + 1) n (by omega)
  obtain ⟨a, hp, h34p⟩ := h34 y hypos (by simpa [y] using hmod)
  have hlt : iter shortcut a y < n := by
    have hwin' : 3 * y < 4 * n := by simpa [y] using hwin
    omega
  refine ⟨a, ?_⟩
  rw [iter_add]
  change OrdinaryExit n (iter shortcut a y)
  exact Or.inr (Or.inl ⟨hp, hlt⟩)

/-- Tournament-reduced closeout: after the large branch is discharged by the
source-independent three-quarter constructor, only the eternal-survival and
origin-crossing constructor domains remain. -/
theorem reaches_one_of_two_domains_and_three_quarter_future7
    (hEternal : EternalConstructorCoverage)
    (hOrigin : OriginCrossingConstructorCoverage)
    (h34 : ThreeQuarterFuture7) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_assembled_constructor_coverage
    hEternal hOrigin
    (large_crossing_coverage_of_three_quarter_future7 h34)

#print axioms large_crossing_coverage_of_three_quarter_future7
#print axioms reaches_one_of_two_domains_and_three_quarter_future7

end SourceProduct
end CollatzFinal
