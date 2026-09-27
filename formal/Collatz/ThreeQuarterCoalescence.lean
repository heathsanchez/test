import Collatz.ConstructorTournament

namespace CollatzFinal
namespace SourceProduct

/-- Consequence-pruned large-branch target.

Unlike ThreeQuarterFuture7, this does not require the original endpoint y
itself to descend by three quarters.  It only asks for a positive source p
at most three quarters of y whose orbit coalesces with the orbit of y.

This is exactly the information LargeCrossingConstructorCoverage consumes:
on the large hard-crossing window 3*y < 4*n, such a p is automatically < n.
-/
def ThreeQuarterCoalescence7 : Prop :=
  ∀ y, 0 < y → y % 12 = 7 →
    ∃ p a b, 0 < p ∧ 4 * p ≤ 3 * y ∧
      iter shortcut a y = iter shortcut b p

/-- The weaker coalescence capability closes the full large-source hard
first-crossing domain. -/
theorem large_crossing_coverage_of_three_quarter_coalescence7
    (h34 : ThreeQuarterCoalescence7) :
    LargeCrossingConstructorCoverage := by
  intro n k hgt hhard hq hwin hmod
  let y := iter shortcut (k + 1) n
  have hypos : 0 < y := by
    dsimp [y]
    exact iter_positive shortcut shortcut_positive (k + 1) n (by omega)
  obtain ⟨p, a, b, hp, h34p, hmerge⟩ :=
    h34 y hypos (by simpa [y] using hmod)
  have hlt : p < n := by
    have hwin' : 3 * y < 4 * n := by simpa [y] using hwin
    omega
  refine ⟨a, ?_⟩
  rw [iter_add]
  change OrdinaryExit n (iter shortcut a y)
  exact Or.inr (Or.inr ⟨p, b, hp, hlt, hmerge.symm⟩)

/-- Final consequence-pruned two-capability closeout.

HighOddConstructorCoverage handles the high-odd domain.  The large branch
needs only ThreeQuarterCoalescence7, not the stronger ThreeQuarterFuture7.
-/
theorem reaches_one_of_high_odd_and_three_quarter_coalescence7
    (hHigh : HighOddConstructorCoverage)
    (h34 : ThreeQuarterCoalescence7) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_two_constructor_domains
    hHigh (large_crossing_coverage_of_three_quarter_coalescence7 h34)

#print axioms large_crossing_coverage_of_three_quarter_coalescence7
#print axioms reaches_one_of_high_odd_and_three_quarter_coalescence7

end SourceProduct
end CollatzFinal
