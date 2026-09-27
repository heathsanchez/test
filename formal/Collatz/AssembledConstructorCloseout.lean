import Collatz.SourceCoherenceAudit
import Collatz.HardCrossingSplit
import Collatz.FinalExcursion

namespace CollatzFinal
namespace SourceProduct

/-- Exact constructor-domain decomposition of a first crossing on a hypothetical
minimal positive bad source.

Nothing is abstracted away:
* the crossing is hard (no exit at the crossing);
* either the source lies in the origin branch n <= q;
* or q < n, in which case the endpoint is in the rigid large-source window
  3*y < 4*n and residue class y = 7 mod 24.

This is the domain split that a lower-source constructor compiler must cover. -/
theorem minimal_bad_first_crossing_constructor_domains
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    let q := oddCount n (k + 1)
    let y := iter shortcut (k + 1) n
    HardFirstCrossing n k ∧
      (n ≤ q ∨
        (q < n ∧ 3 * y < 4 * n ∧ y % 24 = 7)) := by
  let q := oddCount n (k + 1)
  let y := iter shortcut (k + 1) n
  have hhard : HardFirstCrossing n k :=
    minimal_bad_first_crossing_is_hard hmin hfirst
  refine ⟨hhard, ?_⟩
  rcases minimal_bad_first_crossing_origin_or_large_signature
    hmin hfirst with horigin | hlarge
  · exact Or.inl horigin
  · rcases hlarge with ⟨hq, hmod⟩
    have hwin : 3 * y < 4 * n := by
      dsimp [y]
      exact first_crossing_three_y_lt_four_n hmin.1.1 hfirst hq
    exact Or.inr ⟨hq, hwin, by simpa [y] using hmod⟩

/-- Constructor coverage needed only on the eternal-survival branch. -/
def EternalConstructorCoverage : Prop :=
  ∀ n, 1 < n → EternalCoefficientSurvival n →
    ∃ k, OrdinaryExit n (iter shortcut k n)

/-- Constructor coverage needed only on hard first crossings in the origin
branch.  Coverage may fire at any later depth and may be direct descent,
terminal reach, or any lower-source coalescence. -/
def OriginCrossingConstructorCoverage : Prop :=
  ∀ n k, 1 < n → HardFirstCrossing n k →
    n ≤ oddCount n (k + 1) →
    ∃ j, OrdinaryExit n (iter shortcut ((k + 1) + j) n)

/-- Constructor coverage needed only on the rigid large-source hard-crossing
branch.  The residue/window assumptions are consequences of minimal badness,
not extra conjectures. -/
def LargeCrossingConstructorCoverage : Prop :=
  ∀ n k, 1 < n → HardFirstCrossing n k →
    oddCount n (k + 1) < n →
    3 * iter shortcut (k + 1) n < 4 * n →
    iter shortcut (k + 1) n % 24 = 7 →
    ∃ j, OrdinaryExit n (iter shortcut ((k + 1) + j) n)

/-- Full assembly theorem.

The old proof search has been reduced to three goal-relative constructor
coverage interfaces.  If Crystal supplies an exact OrdinaryExit constructor on
each of these domains, the existing source-order/minimal-bad kernel closes
Collatz immediately.  No time-indexed rank, uniform block bound, or universal
first-crossing descent theorem is required. -/
theorem reaches_one_of_assembled_constructor_coverage
    (hEternal : EternalConstructorCoverage)
    (hOrigin : OriginCrossingConstructorCoverage)
    (hLarge : LargeCrossingConstructorCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := minimal_positive_bad_gt_one hmin
    rcases coefficient_survival_or_first_crossing n with hsurv | ⟨d, hfirst⟩
    · obtain ⟨k, hexit⟩ := hEternal n hgt hsurv
      exact minimal_bad_has_no_ordinary_exit hmin k hexit
    · cases d with
      | zero =>
          have hc : CoefficientCrossingAt n 0 := hfirst.1
          unfold CoefficientCrossingAt at hc
          simp at hc
      | succ k =>
          have hhard : HardFirstCrossing n k :=
            minimal_bad_first_crossing_is_hard hmin hfirst
          rcases minimal_bad_first_crossing_constructor_domains
            hmin hfirst with ⟨_, horigin | hlarge⟩
          · obtain ⟨j, hexit⟩ :=
              hOrigin n k hgt hhard horigin
            exact minimal_bad_has_no_ordinary_exit hmin ((k + 1) + j) hexit
          · rcases hlarge with ⟨hq, hwin, hmod⟩
            obtain ⟨j, hexit⟩ :=
              hLarge n k hgt hhard hq hwin hmod
            exact minimal_bad_has_no_ordinary_exit hmin ((k + 1) + j) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms minimal_bad_first_crossing_constructor_domains
#print axioms reaches_one_of_assembled_constructor_coverage

end SourceProduct
end CollatzFinal
