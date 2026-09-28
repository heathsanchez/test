import Collatz.FirstSuperHighBoundary

namespace CollatzFinal
namespace SourceProduct

/-- Exact concatenation law for odd-step counts. -/
theorem oddCount_add (n a b : Nat) :
    oddCount n (a + b) =
      oddCount n a + oddCount (iter shortcut a n) b := by
  induction b with
  | zero =>
      simp [oddCount]
  | succ b ih =>
      have hiter :
          iter shortcut (a + b) n =
            iter shortcut b (iter shortcut a n) := by
        simpa [Nat.add_assoc] using (iter_add shortcut a b n)
      simp only [Nat.add_assoc, oddCount]
      rw [ih, hiter]
      by_cases h : iter shortcut b (iter shortcut a n) % 2 = 0
      · simp [h]
      · simp [h]
        omega

/-- The source/odd-count budget comparison that is preserved after a
coalescence.  It is the subtraction-free form of
  4*n - 3*q_n >= 4*p - 3*q_p.
-/
def WeightedBudgetDominates (n qn p qp : Nat) : Prop :=
  3 * qn + 4 * p ≤ 4 * n + 3 * qp

/-- A lower-source merge that does not spend more of the four-thirds budget
than the source drop can pay for. -/
def WeightedLowerMerge (n p a b : Nat) : Prop :=
  0 < p ∧ p < n ∧
  iter shortcut a n = iter shortcut b p ∧
  WeightedBudgetDominates n (oddCount n a) p (oddCount p b)

/-- After an exact merge, both paths see the same future parity word.  Hence a
weighted budget comparison at the merge point persists for every common
future depth. -/
theorem weighted_budget_persists_after_merge
    {n p a b : Nat}
    (hm : iter shortcut a n = iter shortcut b p)
    (hbud : WeightedBudgetDominates n (oddCount n a) p (oddCount p b)) :
    ∀ j,
      WeightedBudgetDominates n (oddCount n (a + j))
        p (oddCount p (b + j)) := by
  intro j
  rw [oddCount_add n a j, oddCount_add p b j]
  have htail :
      oddCount (iter shortcut a n) j =
        oddCount (iter shortcut b p) j := by
    rw [hm]
  unfold WeightedBudgetDominates at hbud ⊢
  rw [htail]
  omega

/-- If the smaller source has not exhausted its four-thirds odd budget at a
common future state, neither has the larger source, provided the merge paid
for the source/odd-count offset once at the merge point. -/
theorem weighted_merge_transfers_four_thirds
    {n p a b j : Nat}
    (hm : WeightedLowerMerge n p a b)
    (hp :
      3 * oddCount p (b + j) ≤ 4 * p) :
    3 * oddCount n (a + j) ≤ 4 * n := by
  rcases hm with ⟨_hp0, _hplt, heq, hbud⟩
  have hfuture :=
    weighted_budget_persists_after_merge heq hbud j
  unfold WeightedBudgetDominates at hfuture
  omega

/-- The same transfer, exposing only the common endpoint and budget premises.
This is the induction rule Crystal can compile: once a smaller source is
certified, every larger source that reaches the same state with at least the
same remaining budget inherits the cap for the whole shared suffix. -/
theorem four_thirds_cap_of_budgeted_common_future
    {n p a b j : Nat}
    (heq : iter shortcut a n = iter shortcut b p)
    (hbud :
      3 * oddCount n a + 4 * p ≤
        4 * n + 3 * oddCount p b)
    (hp :
      3 * oddCount p (b + j) ≤ 4 * p) :
    3 * oddCount n (a + j) ≤ 4 * n := by
  exact weighted_merge_transfers_four_thirds
    ⟨by omega, by omega, heq, hbud⟩ hp

#print axioms oddCount_add
#print axioms weighted_budget_persists_after_merge
#print axioms weighted_merge_transfers_four_thirds

end SourceProduct
end CollatzFinal
