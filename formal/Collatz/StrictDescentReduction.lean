import Collatz.CoefficientDynamics

namespace CollatzFinal
namespace SourceProduct

/-- Ordinary-orbit formulation of the first remaining obstruction:
coefficient survival persists at every depth. -/
def EternalCoefficientSurvival (n : Nat) : Prop :=
  ∀ k, CoefficientSurvives n k

/-- From any witnessed coefficient crossing, strong recursion extracts a least
one without relying on a separate minimization primitive. -/
theorem first_crossing_of_crossing
    (n : Nat) :
    ∀ k, CoefficientCrossingAt n k →
      ∃ j, FirstCoefficientCrossingAt n j := by
  intro k
  induction k using Nat.strongRecOn with
  | ind k ih =>
      intro hk
      by_cases hprev : ∃ i, i < k ∧ CoefficientCrossingAt n i
      · obtain ⟨i, hi, hic⟩ := hprev
        exact ih i hi hic
      · refine ⟨k, hk, ?_⟩
        intro i hi hic
        exact hprev ⟨i, hi, hic⟩

/-- Every source either survives the coefficient test forever or has a unique
least (first) coefficient crossing. -/
theorem coefficient_survival_or_first_crossing (n : Nat) :
    EternalCoefficientSurvival n ∨
    ∃ k, FirstCoefficientCrossingAt n k := by
  classical
  by_cases h : EternalCoefficientSurvival n
  · exact Or.inl h
  · right
    have hexNot : ∃ k, ¬ CoefficientSurvives n k := by
      apply Classical.byContradiction
      intro hnone
      apply h
      intro k
      apply Classical.byContradiction
      intro hk
      exact hnone ⟨k, hk⟩
    obtain ⟨k, hk⟩ := hexNot
    have hcross : CoefficientCrossingAt n k :=
      (coefficientCrossingAt_iff_not_survives n k).2 hk
    exact first_crossing_of_crossing n k hcross

/-- If an orbit has not descended by depth k, its exact affine joint margin is
nonnegative. This is the ordinary-orbit form of the archived M obstruction. -/
theorem margin_nonnegative_of_nondescending
    {n k : Nat}
    (hnd : n ≤ iter shortcut k n) :
    (2 ^ k - 3 ^ oddCount n k) * n ≤ bias n k := by
  have ha := exact_affine n k
  have hs := Nat.mul_le_mul_left (2 ^ k) hnd
  rw [ha] at hs
  rw [Nat.sub_mul]
  omega

/-- Conversely, a negative exact joint margin is already a strict-descent
certificate for the ordinary shortcut orbit. -/
theorem strict_descent_of_negative_margin
    {n k : Nat}
    (hneg : bias n k < (2 ^ k - 3 ^ oddCount n k) * n) :
    iter shortcut k n < n := by
  apply Classical.byContradiction
  intro h
  have hnd : n ≤ iter shortcut k n := by omega
  have hm := margin_nonnegative_of_nondescending hnd
  omega

/-- A hypothetical minimal positive bad source can never descend below itself
at any depth. -/
theorem minimal_bad_nondescending_all_depths
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    ∀ k, n ≤ iter shortcut k n := by
  intro k
  apply Classical.byContradiction
  intro h
  have hlt : iter shortcut k n < n := by omega
  have hp : 0 < iter shortcut k n :=
    iter_positive shortcut shortcut_positive k n hmin.1.1
  apply positive_minimal_no_lower_merge hmin (iter shortcut k n) hp
  refine ⟨hlt, k, 0, ?_⟩
  simp [iter]

/-- Therefore every coefficient crossing of a hypothetical minimal bad source
has nonnegative exact joint margin. -/
theorem minimal_bad_crossing_margin_nonnegative
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (_hcross : CoefficientCrossingAt n k) :
    (2 ^ k - 3 ^ oddCount n k) * n ≤ bias n k := by
  exact margin_nonnegative_of_nondescending
    (minimal_bad_nondescending_all_depths hmin k)

/-- Exact two-obstruction reduction. A hypothetical minimal positive bad source
either survives the coefficient comparison forever, or its unique first
crossing is a nonnegative-M first-crossing obstruction. -/
theorem minimal_bad_two_obstruction_reduction
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    EternalCoefficientSurvival n ∨
    ∃ k, FirstCoefficientCrossingAt n k ∧
      (2 ^ k - 3 ^ oddCount n k) * n ≤ bias n k := by
  rcases coefficient_survival_or_first_crossing n with hsurv | ⟨k, hk⟩
  · exact Or.inl hsurv
  · exact Or.inr ⟨k, hk,
      minimal_bad_crossing_margin_nonnegative hmin hk.1⟩

/-- Final ordinary-orbit closeout interface.
To prove Collatz it suffices to eliminate exactly the two residual obstructions:
(1) eternal coefficient survival, and
(2) nonnegative joint margin at a first coefficient crossing. -/
theorem reaches_one_of_no_survival_and_negative_first_margin
    (hNoSurvival :
      ∀ n, 1 < n → ¬ EternalCoefficientSurvival n)
    (hNegativeFirstMargin :
      ∀ n k, 1 < n → FirstCoefficientCrossingAt n k →
        bias n k < (2 ^ k - 3 ^ oddCount n k) * n) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply reaches_one_of_strict_descent shortcut shortcut_positive
  intro n hn
  rcases coefficient_survival_or_first_crossing n with hsurv | ⟨k, hk⟩
  · exact False.elim (hNoSurvival n hn hsurv)
  · exact ⟨k, strict_descent_of_negative_margin
      (hNegativeFirstMargin n k hn hk)⟩

#print axioms first_crossing_of_crossing
#print axioms coefficient_survival_or_first_crossing
#print axioms margin_nonnegative_of_nondescending
#print axioms strict_descent_of_negative_margin
#print axioms minimal_bad_nondescending_all_depths
#print axioms minimal_bad_crossing_margin_nonnegative
#print axioms minimal_bad_two_obstruction_reduction
#print axioms reaches_one_of_no_survival_and_negative_first_margin

end SourceProduct
end CollatzFinal
