import Collatz.FixedSourceProgress

namespace CollatzFinal
namespace SourceProduct

/-- The source-order formulation of the remaining Collatz obligation.

For every source above one, its forward orbit must coalesce with the forward
orbit of some strictly smaller positive source.  Direct strict descent is the
special case where the smaller source is itself a future endpoint. -/
def CoalescenceDescent : Prop :=
  ∀ n, 1 < n →
    ∃ p, 0 < p ∧ LowerMerge shortcut n p

/-- Coalescence descent closes Collatz by well-ordering of the source integer.
No time-indexed rank or source-independent waiting bound is required. -/
theorem collatz_of_coalescence_descent
    (hcd : CoalescenceDescent) :
    ∀ n, 0 < n → CollatzGood n := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := minimal_positive_bad_gt_one hmin
    obtain ⟨p, hp, hm⟩ := hcd n hgt
    exact positive_minimal_no_lower_merge hmin p hp hm
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hnone n ⟨hn, hbad⟩

/-- User-facing reaches-one consequence of coalescence descent. -/
theorem reaches_one_of_coalescence_descent
    (hcd : CoalescenceDescent) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  intro n hn
  exact collatzGood_eventually_one
    (collatz_of_coalescence_descent hcd n hn)

/-- Conversely, Collatz itself supplies a coalescence-descent certificate:
choose the smaller source 1 and the first future hit of 1.  Thus the
coalescence formulation is an exact proof architecture, not an extra
unproved strengthening. -/
theorem coalescence_descent_of_collatz
    (hgood : ∀ n, 0 < n → CollatzGood n) :
    CoalescenceDescent := by
  intro n hgt
  have hnpos : 0 < n := by omega
  have hone := collatzGood_eventually_one (hgood n hnpos)
  obtain ⟨a, ha⟩ := hone
  refine ⟨1, by omega, ?_⟩
  refine ⟨hgt, a, 0, ?_⟩
  simpa [iter] using ha

/-- Exact equivalence between universal source-order coalescence descent and
positive Collatz termination. -/
theorem coalescence_descent_iff_collatz :
    CoalescenceDescent ↔
      (∀ n, 0 < n → CollatzGood n) := by
  constructor
  · exact collatz_of_coalescence_descent
  · exact coalescence_descent_of_collatz

#print axioms collatz_of_coalescence_descent
#print axioms reaches_one_of_coalescence_descent
#print axioms coalescence_descent_of_collatz
#print axioms coalescence_descent_iff_collatz

end SourceProduct
end CollatzFinal
