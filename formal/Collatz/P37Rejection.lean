import Collatz.CoefficientCrossing

namespace CollatzFinal
namespace SourceProduct

/-- An exact rejection of a proposed first-crossing type at the parent depth.
An earlier crossing or failure to cross at the parent depth suffices. Neither
case requires a margin theorem at another type. -/
def ParentRejection (n j : Nat) : Prop :=
  (∃ i, i < j ∧ CoefficientCrossingAt n i) ∨
  ¬ CoefficientCrossingAt n j

theorem parent_rejection_excludes_first
    {n j : Nat} (hr : ParentRejection n j) :
    ¬ FirstCoefficientCrossingAt n j := by
  intro hj
  rcases hr with hearly | hnot
  · obtain ⟨i, hi, hc⟩ := hearly
    exact hj.2 i hi hc
  · exact hnot hj.1

/-- V10 off-type competitor certificates can be compressed to a test at or
before the parent's depth. If the competitor crosses later, checking that it
has not crossed at the parent is already enough. -/
theorem off_type_gives_parent_rejection
    {n j k : Nat}
    (hk : FirstCoefficientCrossingAt n k) (hne : k ≠ j) :
    ParentRejection n j := by
  by_cases hlt : k < j
  · exact Or.inl ⟨k, hlt, hk.1⟩
  · have hjk : j < k := by omega
    exact Or.inr (hk.2 j hjk)

/-- The mathematical residual requires first-crossing membership as well as
non-descent. This predicate is not asserted to have any nontrivial witness. -/
def NondescendingFirstCrossing (n j : Nat) : Prop :=
  1 < n ∧ FirstCoefficientCrossingAt n j ∧ n ≤ iter shortcut j n

/-- A witnessed off-type competitor is NOT a source-preserving transition
out of a parent residual: it excludes membership in the parent altogether.
This does not rule out a different, proved witness-changing recursion. -/
theorem off_type_excludes_parent_residual
    {n j k : Nat}
    (hk : FirstCoefficientCrossingAt n k) (hne : k ≠ j) :
    ¬ NondescendingFirstCrossing n j := by
  intro hr
  exact parent_rejection_excludes_first
    (off_type_gives_parent_rejection hk hne) hr.2.1

/-- Adding a cap or a graph rank to the same-source off-type relation cannot
make it a residual successor relation. A new semantic transformation is needed
before a rank on different types can be used for well-founded induction. -/
theorem no_same_source_off_type_progress
    {n j : Nat} (hj : FirstCoefficientCrossingAt n j) :
    ¬ (∃ k, k ≠ j ∧ FirstCoefficientCrossingAt n k) := by
  intro h
  obtain ⟨k, hne, hk⟩ := h
  exact parent_rejection_excludes_first
    (off_type_gives_parent_rejection hk hne) hj

-- The previously reported increasing-depth dependency 111 -> 129 is already
-- rejected at parent depth 111. This is a kernel computation, not native_decide.
theorem competitor_45127_rejected_at_111 :
    ¬ CoefficientCrossingAt 45127 111 := by
  unfold CoefficientCrossingAt
  decide

example : ¬ FirstCoefficientCrossingAt 45127 111 := by
  intro h
  exact competitor_45127_rejected_at_111 h.1

#print axioms parent_rejection_excludes_first
#print axioms off_type_gives_parent_rejection
#print axioms off_type_excludes_parent_residual
#print axioms no_same_source_off_type_progress
#print axioms competitor_45127_rejected_at_111

end SourceProduct
end CollatzFinal
