import Collatz.FirstCrossingRigidity
import Collatz.OrdinaryInverseOdd

namespace CollatzFinal
namespace SourceProduct

/-- The exact counterexample-relevant first-crossing object.
It has reached the unique coefficient crossing but still has no ordinary exit:
no terminal hit, no direct descent, and no merge with any smaller positive source. -/
def HardFirstCrossing (n k : Nat) : Prop :=
  FirstCoefficientCrossingAt n (k + 1) ∧
  ¬ OrdinaryExit n (iter shortcut (k + 1) n)

/-- Every first crossing on a hypothetical minimal positive bad orbit is hard. -/
theorem minimal_bad_first_crossing_is_hard
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    HardFirstCrossing n k := by
  exact ⟨hfirst, minimal_bad_has_no_ordinary_exit hmin (k + 1)⟩

/-- A hard first crossing is necessarily nondescending. -/
theorem hard_first_crossing_endpoint_ge_source
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k) :
    n ≤ iter shortcut (k + 1) n := by
  have hypos : 0 < iter shortcut (k + 1) n :=
    iter_positive shortcut shortcut_positive (k + 1) n hn
  apply Nat.le_of_not_gt
  intro hlt
  exact hhard.2 (Or.inr (Or.inl ⟨hypos, hlt⟩))

/-- Hence immediately before its forced final even step, a hard first crossing
has already reached at least twice its source. -/
theorem hard_first_crossing_previous_ge_double
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k) :
    2 * n ≤ iter shortcut k n := by
  exact (first_crossing_nondescending_iff_previous_ge_double hhard.1).1
    (hard_first_crossing_endpoint_ge_source hn hhard)

/-- No positive orbit predecessor of the hard endpoint may start below n,
at any reverse depth. This is the universal lower-merge exclusion that bounded
inverse-tree searches were approximating. -/
theorem hard_first_crossing_no_smaller_predecessor
    {n k : Nat}
    (hhard : HardFirstCrossing n k) :
    ∀ p b, 0 < p → p < n →
      iter shortcut b p ≠ iter shortcut (k + 1) n := by
  intro p b hp hlt heq
  apply hhard.2
  exact Or.inr (Or.inr ⟨p, b, hp, hlt, heq⟩)

/-- The first-crossing odd count is not a free state coordinate: it is exactly
one below the deterministic dyadic threshold. -/
theorem hard_first_crossing_q_rigid
    {n k : Nat}
    (hhard : HardFirstCrossing n k) :
    oddCount n (k + 1) + 1 = qmin (k + 1) := by
  exact first_crossing_oddCount_eq_threshold_minus_one hhard.1

/-- The final step of a hard first crossing is forced even. -/
theorem hard_first_crossing_last_step_even
    {n k : Nat}
    (hhard : HardFirstCrossing n k) :
    iter shortcut k n % 2 = 0 := by
  exact first_crossing_last_step_even hhard.1

/-- The depth-one inverse-odd lower-merge obstruction becomes a forbidden
window on every hard first-crossing endpoint of residue 2 mod 3. -/
theorem hard_first_crossing_mod3_two_growth
    {n k : Nat}
    (hhard : HardFirstCrossing n k)
    (hy : iter shortcut (k + 1) n % 3 = 2) :
    3 * n + 1 ≤ 2 * iter shortcut (k + 1) n := by
  exact no_ordinary_exit_mod3_two_growth hhard.2 hy

/-- Complete native normal form for the current finite-crossing residual. -/
theorem hard_first_crossing_normal_form
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k) :
    oddCount n (k + 1) + 1 = qmin (k + 1) ∧
    iter shortcut k n % 2 = 0 ∧
    iter shortcut (k + 1) n = iter shortcut k n / 2 ∧
    n ≤ iter shortcut (k + 1) n ∧
    2 * n ≤ iter shortcut k n ∧
    (∀ p b, 0 < p → p < n →
      iter shortcut b p ≠ iter shortcut (k + 1) n) := by
  refine ⟨hard_first_crossing_q_rigid hhard,
    hard_first_crossing_last_step_even hhard,
    first_crossing_endpoint_eq_half_previous hhard.1,
    hard_first_crossing_endpoint_ge_source hn hhard,
    hard_first_crossing_previous_ge_double hn hhard,
    hard_first_crossing_no_smaller_predecessor hhard⟩

#print axioms minimal_bad_first_crossing_is_hard
#print axioms hard_first_crossing_endpoint_ge_source
#print axioms hard_first_crossing_previous_ge_double
#print axioms hard_first_crossing_no_smaller_predecessor
#print axioms hard_first_crossing_q_rigid
#print axioms hard_first_crossing_last_step_even
#print axioms hard_first_crossing_mod3_two_growth
#print axioms hard_first_crossing_normal_form

end SourceProduct
end CollatzFinal
