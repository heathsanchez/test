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

/-- Final one-premise Crystal interface.  No explicit q-coordinate is supplied:
no-exit at the checkpoint itself forces non-descent, and V9 then derives q>=n. -/
def DoubleDepthNoExitQuarterSpliceCoverage : Prop :=
  ∀ n, 1 < n → n % 2 = 1 →
    ¬ OrdinaryExit n (iter shortcut (2 * n) n) →
    ∃ r, let x := iter shortcut ((2 * n) + r) n
      x % 8 = 5 ∧ x ≤ 4 * n

theorem double_depth_no_exit_is_post_diagonal
    {n : Nat}
    (hn : 0 < n)
    (hno : ¬ OrdinaryExit n (iter shortcut (2 * n) n)) :
    n ≤ oddCount n (2 * n) := by
  have hypos : 0 < iter shortcut (2 * n) n :=
    iter_positive shortcut shortcut_positive (2 * n) n hn
  have hnd : n ≤ iter shortcut (2 * n) n := by
    apply Nat.le_of_not_gt
    intro hlt
    exact hno (Or.inr (Or.inl ⟨hypos, hlt⟩))
  exact nondescending_double_depth_enters_post_diagonal hn hnd

theorem postdiagonal_coverage_of_double_depth_no_exit
    (hQ : DoubleDepthNoExitQuarterSpliceCoverage) :
    DoubleDepthPostDiagonalQuarterSpliceCoverage := by
  intro n hgt hodd _hdiag hno
  exact hQ n hgt hodd hno

/-- This is the smallest current universal closeout statement: if every odd
source still no-exit at 2*n eventually reaches a quarter splice relative to the
same source, then Collatz follows. -/
theorem reaches_one_of_double_depth_no_exit_quarter_splice
    (hQ : DoubleDepthNoExitQuarterSpliceCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  exact reaches_one_of_double_depth_postdiagonal_quarter_splice
    (postdiagonal_coverage_of_double_depth_no_exit hQ)

#print axioms double_depth_no_exit_is_post_diagonal
#print axioms reaches_one_of_double_depth_no_exit_quarter_splice

#print axioms reaches_one_of_double_depth_postdiagonal_quarter_splice

end SourceProduct
end CollatzFinal
