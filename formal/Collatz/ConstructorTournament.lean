import Collatz.AssembledConstructorCloseout

namespace CollatzFinal
namespace SourceProduct

/-- Source-independent constructor target for the rigid large-crossing endpoint class. -/
def ThreeQuarterFuture7 : Prop :=
  ∀ y, 0 < y → y % 12 = 7 →
    ∃ a, 0 < iter shortcut a y ∧ 4 * iter shortcut a y ≤ 3 * y

/-- Three-quarter future coverage closes every large-source hard crossing. -/
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

/-- Final two-capability closeout.

HighOddConstructorCoverage handles both eternal coefficient survival and the
old n<=q crossing branch. ThreeQuarterFuture7 handles the rigid q<n branch.
Together they imply positive Collatz termination. -/
theorem reaches_one_of_high_odd_and_three_quarter_future7
    (hHigh : HighOddConstructorCoverage)
    (h34 : ThreeQuarterFuture7) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_two_constructor_domains
    hHigh (large_crossing_coverage_of_three_quarter_future7 h34)

#print axioms large_crossing_coverage_of_three_quarter_future7
#print axioms reaches_one_of_high_odd_and_three_quarter_future7

end SourceProduct
end CollatzFinal
