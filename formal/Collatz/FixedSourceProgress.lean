import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

universe u

/-- Prefix-sensitive fixed-source liveness.  This is the formal counterpart of
the time-indexed Live(n,k) used by the fixed-source progress argument: every
actual source state through depth k is still in the no-Exit residual. -/
def FixedSourcePrefixLive (n k : Nat) : Prop :=
  ∀ i, i ≤ k → Live (stateAt n i)

/-- A hypothetical minimal positive bad source is prefix-live at every depth. -/
theorem minimal_bad_prefix_live
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    ∀ k, FixedSourcePrefixLive n k := by
  intro k i _hi
  exact minimal_path_live hmin (stateAt n i) ⟨i, rfl⟩

/-- A minimal positive bad source is strictly larger than one. -/
theorem minimal_positive_bad_gt_one
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    1 < n := by
  have hn : 0 < n := hmin.1.1
  have hne : n ≠ 1 := by
    intro heq
    apply hmin.1.2
    subst n
    exact ⟨0, by simp [iter, Terminal]⟩
  omega

/-- Unbounded fixed-source progress.

Unlike the earlier bounded-block formulation, no source-independent horizon B
is assumed.  From every live prefix there only has to exist some later depth
which either leaves the live residual or strictly lowers a recursively
applicable well-founded rank. -/
def EventualFixedSourceProgress
    {W : Type u} (prec : W → W → Prop)
    (rank : Nat → Nat → W) : Prop :=
  ∀ n k, 1 < n → FixedSourcePrefixLive n k →
    ∃ b, 0 < b ∧
      (¬ FixedSourcePrefixLive n (k + b) ∨
        prec (rank n (k + b)) (rank n k))

/-- The exact logical closeout: any genuinely well-founded, recursively
applicable eventual fixed-source progress measure proves CollatzGood for every
positive source.  A uniform block bound is not required. -/
theorem collatz_of_eventual_fixed_source_progress
    {W : Type u} (prec : W → W → Prop)
    (hprec : WellFounded prec)
    (rank : Nat → Nat → W)
    (hprogress : EventualFixedSourceProgress prec rank) :
    ∀ n, 0 < n → CollatzGood n := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := minimal_positive_bad_gt_one hmin
    have himpossible : ∀ w, ∀ k, rank n k = w → False := by
      intro w
      refine hprec.induction w ?_
      intro x ih k hk
      have hlive : FixedSourcePrefixLive n k :=
        minimal_bad_prefix_live hmin k
      obtain ⟨b, _hb, hnext⟩ := hprogress n k hgt hlive
      rcases hnext with hexit | hdec
      · exact hexit (minimal_bad_prefix_live hmin (k + b))
      · have hrel : prec (rank n (k + b)) x := by
          simpa [hk] using hdec
        exact ih (rank n (k + b)) hrel (k + b) rfl
    exact himpossible (rank n 0) 0 rfl
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hnone n ⟨hn, hbad⟩

/-- User-facing reaches-one form of the same theorem. -/
theorem reaches_one_of_eventual_fixed_source_progress
    {W : Type u} (prec : W → W → Prop)
    (hprec : WellFounded prec)
    (rank : Nat → Nat → W)
    (hprogress : EventualFixedSourceProgress prec rank) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  intro n hn
  exact collatzGood_eventually_one
    (collatz_of_eventual_fixed_source_progress
      prec hprec rank hprogress n hn)

#print axioms minimal_bad_prefix_live
#print axioms minimal_positive_bad_gt_one
#print axioms collatz_of_eventual_fixed_source_progress
#print axioms reaches_one_of_eventual_fixed_source_progress

end SourceProduct
end CollatzFinal
