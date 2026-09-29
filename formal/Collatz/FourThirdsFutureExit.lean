import Collatz.FourThirdsConstructor

namespace CollatzFinal
namespace SourceProduct

/-- A weaker closeout interface than V20's immediate constructor coverage.

At the first exact four-thirds odd-count boundary, an odd state need only
eventually produce an OrdinaryExit.  The exit may be direct descent, terminal
reach, or lower-source coalescence.  This is the interface consumed by a
future/rank argument on the exact source-frozen state; it does not require the
boundary state itself to be a quarter splice. -/
def FourThirdsOddBoundaryFutureExitCoverage : Prop :=
  ∀ n k, 1 < n →
    n % 2 = 1 →
    oddCount n k = (4 * n) / 3 →
    iter shortcut k n % 2 = 1 →
    ∃ j, OrdinaryExit n (iter shortcut (k + j) n)

/-- The future-exit boundary interface is sufficient for positive Collatz.

A hypothetical minimal bad source is forced through the exact odd-count
boundary by the existing V20 diagonal/IVT argument.  The predecessor of the
odd-count increment is odd.  Any future OrdinaryExit from that boundary
contradicts minimal badness. -/
theorem reaches_one_of_four_thirds_odd_boundary_future_exit
    (hFuture : FourThirdsOddBoundaryFutureExitCoverage) :
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
    have hoddSource : n % 2 = 1 :=
      positive_minimal_bad_odd hmin
    let Q := (4 * n) / 3
    have hQlt2 : Q < 2 * n := by
      dsimp [Q]
      exact four_thirds_floor_lt_double hgt
    have hstrict :
        2 * n < oddCount n (4 * n) :=
      minimal_bad_quadruple_depth_strict_double_diagonal hmin
    have hQlt :
        Q < oddCount n (4 * n) := by
      omega
    obtain ⟨k, _hklt, hq, hqs⟩ :=
      oddCount_exact_boundary
        (n := n) (Q := Q) (K := 4 * n) hQlt
    have hxodd :
        iter shortcut k n % 2 = 1 :=
      oddCount_boundary_step_odd hq hqs
    obtain ⟨j, hexit⟩ :=
      hFuture n k hgt hoddSource
        (by simpa [Q] using hq) hxodd
    exact minimal_bad_has_no_ordinary_exit hmin (k + j) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

/-- V20 immediate constructor coverage is strictly sufficient for the weaker
future interface: direct exits fire at j=0; quarter splices schedule an
OrdinaryExit three steps later. -/
theorem four_thirds_odd_boundary_future_exit_of_constructor
    (hCov : FourThirdsOddConstructorCoverage) :
    FourThirdsOddBoundaryFutureExitCoverage := by
  intro n k hgt hodd hq hxodd
  rcases hCov n k hgt hodd hq hxodd with hexit | hsplice
  · exact ⟨0, by simpa [iter] using hexit⟩
  · refine ⟨3, ?_⟩
    rw [iter_add]
    exact ordinary_exit_after_quarter_splice hsplice.1 hsplice.2

#print axioms reaches_one_of_four_thirds_odd_boundary_future_exit
#print axioms four_thirds_odd_boundary_future_exit_of_constructor

end SourceProduct
end CollatzFinal
