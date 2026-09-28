import Collatz.QuarterSplice
import Collatz.UniversalDiagonal

namespace CollatzFinal
namespace SourceProduct

/-- The only remaining quarter-splice obligation after the universal diagonal
theorem: act only on a source that is still no-exit at the deterministic
checkpoint 2*n and has already entered q >= n. -/
def DoubleDepthPostDiagonalQuarterSpliceCoverage : Prop :=
  ∀ n, 1 < n → n % 2 = 1 →
    n ≤ oddCount n (2 * n) →
    ¬ OrdinaryExit n (iter shortcut (2 * n) n) →
    ∃ r, let x := iter shortcut ((2 * n) + r) n
      x % 8 = 5 ∧ x ≤ 4 * n

/-- The V9 diagonal theorem makes the restricted checkpoint coverage sufficient
for full positive Collatz. -/
theorem reaches_one_of_double_depth_postdiagonal_quarter_splice
    (hQ : DoubleDepthPostDiagonalQuarterSpliceCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := by
      have hn : 0 < n := hmin.1.1
      have hne : n ≠ 1 := by
        intro heq
        apply hmin.1.2
        subst n
        exact ⟨0, by simp [iter, Terminal]⟩
      omega
    have hodd : n % 2 = 1 := positive_minimal_bad_odd hmin
    have hdiag : n ≤ oddCount n (2 * n) :=
      minimal_bad_enters_post_diagonal_by_double hmin
    have hno : ¬ OrdinaryExit n (iter shortcut (2 * n) n) :=
      minimal_bad_has_no_ordinary_exit hmin (2 * n)
    obtain ⟨r, hxmod, hxband⟩ := hQ n hgt hodd hdiag hno
    have hexit :
        OrdinaryExit n (iter shortcut (((2 * n) + r) + 3) n) := by
      rw [iter_add]
      exact ordinary_exit_after_quarter_splice hxmod hxband
    exact minimal_bad_has_no_ordinary_exit hmin (((2 * n) + r) + 3) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms reaches_one_of_double_depth_postdiagonal_quarter_splice

end SourceProduct
end CollatzFinal
