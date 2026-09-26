import Collatz.CoefficientCrossing

namespace CollatzFinal
namespace SourceProduct

/-- A rejection at or before the parent depth, not a successor witness. -/
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

/-- An off-type competitor can be rejected without solving its own margin
problem. A later first crossing requires only the test at the parent depth. -/
theorem off_type_gives_parent_rejection
    {n j k : Nat}
    (hk : FirstCoefficientCrossingAt n k) (hne : k ≠ j) :
    ParentRejection n j := by
  by_cases hlt : k < j
  · exact Or.inl ⟨k, hlt, hk.1⟩
  · have hjk : j < k := by omega
    exact Or.inr (hk.2 j hjk)

def NondescendingFirstCrossing (n j : Nat) : Prop :=
  1 < n ∧ FirstCoefficientCrossingAt n j ∧ n ≤ iter shortcut j n

/-- The same-source off-type relation excludes parent membership. It is not
residual-preserving. A different witness-changing recursion is not ruled out. -/
theorem off_type_excludes_parent_residual
    {n j k : Nat}
    (hk : FirstCoefficientCrossingAt n k) (hne : k ≠ j) :
    ¬ NondescendingFirstCrossing n j := by
  intro hr
  exact parent_rejection_excludes_first
    (off_type_gives_parent_rejection hk hne) hr.2.1

theorem no_same_source_off_type_progress
    {n j : Nat} (hj : FirstCoefficientCrossingAt n j) :
    ¬ (∃ k, k ≠ j ∧ FirstCoefficientCrossingAt n k) := by
  intro h
  obtain ⟨k, hne, hk⟩ := h
  exact parent_rejection_excludes_first
    (off_type_gives_parent_rejection hk hne) hj

-- The apparent 111 -> 129 dependency already rejects the candidate at 111.
set_option maxRecDepth 10000 in
set_option maxHeartbeats 2000000 in
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
