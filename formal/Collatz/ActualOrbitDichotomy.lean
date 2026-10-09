import Collatz.FreshAnchorBoundary

namespace CollatzFinal
namespace SourceProduct

/-!
V139 — SOURCE-ATTACHED ACTUAL-ORBIT DICHOTOMY.

The V103 three-way episode result distinguishes an actual period,
a nonzero admitted affine return, and unbounded fresh dyadic anchors.
Those are useful implementation/event classifications, but NOT three
fundamentally distinct global behaviours of the original Nat orbit.

For ANY deterministic Nat orbit, a bounded sequence repeats. Thus:
  actual eventual period OR actual unbounded values.
For a hypothetical least *positive* Collatz counterexample:
  a genuine nonterminal positive cycle on its actual orbit OR
  arbitrarily high ACTUAL trajectory values, with no descent below
  the unchanged original source.

This closes the representation-level trichotomy into a two-way
MATHEMATICAL obstruction, not either obstruction itself.
There is no universal exclusion of positive nonterminal cycles or
unbounded no-merge positive orbits. GLOBAL COLLATZ UNKNOWN.
-/

/-- Exact eventual repetition of the original positive-Nat orbit,
    with TWO independently meaningful actual time coordinates. -/
def ActualEventuallyPeriodic (n : Nat) : Prop :=
  ∃ i k : Nat, 0 < k ∧
    iter shortcut (i + k) n = iter shortcut i n

/-- The original positive-Nat orbit exceeds EVERY natural bound.
    This is not merely high source-residue precision or fresh anchors. -/
def ActualOrbitUnbounded (n : Nat) : Prop :=
  ∀ B : Nat, ∃ k : Nat, B < iter shortcut k n

/-- Universal deterministic alternative, independently of any
    source-capped hit, earlier-source root, return grammar or rank.
    Reuses the V102 kernel-checked infinite pigeonhole lemma. -/
theorem actual_orbit_eventually_periodic_or_unbounded (n : Nat) :
    ActualEventuallyPeriodic n ∨ ActualOrbitUnbounded n := by
  by_cases hp : ActualEventuallyPeriodic n
  · exact Or.inl hp
  · right
    intro B
    apply Classical.byContradiction
    intro hno
    have hb : ∀ i, iter shortcut i n ≤ B := by
      intro i
      have hnot : ¬ B < iter shortcut i n := by
        intro hgt
        exact hno ⟨i, hgt⟩
      omega
    obtain ⟨i, j, hij, heq⟩ :=
      bounded_nat_sequence_repeats B (fun k => iter shortcut k n) hb
    have hk : 0 < j - i := by omega
    have hsum : i + (j - i) = j := by omega
    apply hp
    exact ⟨i, j - i, hk, by simpa only [hsum] using heq.symm⟩

/-- Any repeated actual endpoints define a real periodic positive-time
    orbit at the first occurrence, rather than merely an affine fixed point. -/
theorem actual_repeated_endpoint_gives_tail_period
    (n i k : Nat) (hk : 0 < k)
    (hmeet : iter shortcut (i + k) n = iter shortcut i n) :
    ∃ x : Nat, x = iter shortcut i n ∧
      iter shortcut k x = x := by
  refine ⟨iter shortcut i n, rfl, ?_⟩
  simpa only [iter_add] using hmeet

/-- A minimal POSITIVE bad source can never have an actual orbit value
    smaller than its unchanged original source. This reuses the
    existing V124 typed no-lower-merge theorem, not a fresh induction
    pretending the source is arbitrary. -/
theorem minimal_positive_bad_never_below_source
    {n : Nat} (hmin : MinimalBad PositiveBad n) (k : Nat) :
    n ≤ iter shortcut k n := by
  apply Classical.byContradiction
  intro h
  have hlt : iter shortcut k n < n := by omega
  have hp : 0 < iter shortcut k n :=
    iter_positive shortcut shortcut_positive k n hmin.1.1
  have hno : ¬ LowerMerge shortcut n (iter shortcut k n) :=
    positive_minimal_no_lower_merge hmin (iter shortcut k n) hp
  apply hno
  exact ⟨hlt, k, 0, by simp [iter]⟩

/-- A least positive bad source also has no intersection with the
    actual orbit of ANY strictly earlier positive source at ANY two
    independently chosen clocks. This is stronger than a no-capped-hit
    proxy and carries the original source identity. -/
theorem minimal_positive_bad_no_earlier_source_meeting
    {n : Nat} (hmin : MinimalBad PositiveBad n)
    (p i j : Nat) (hp : 0 < p) (hearlier : p < n) :
    iter shortcut i n ≠ iter shortcut j p := by
  intro hmeet
  exact (positive_minimal_no_lower_merge hmin p hp)
    ⟨hearlier, i, j, hmeet⟩

/-- In the bounded case, the repeated endpoint on a hypothetical
    minimal positive bad orbit is necessarily >2, and remains >= n:
    it cannot be the lawful 1<->2 terminal period. -/
theorem minimal_positive_bad_bounded_has_nonterminal_period
    {n B : Nat} (hmin : MinimalBad PositiveBad n)
    (hbounded : ∀ k : Nat, iter shortcut k n ≤ B) :
    ∃ i k : Nat, 0 < k ∧
      2 < iter shortcut i n ∧
      n ≤ iter shortcut i n ∧
      iter shortcut (i + k) n = iter shortcut i n := by
  obtain ⟨i, j, hij, heq⟩ :=
    bounded_nat_sequence_repeats B (fun k => iter shortcut k n)
      hbounded
  have hk : 0 < j - i := by omega
  have hsum : i + (j - i) = j := by omega
  have hpositive : 0 < iter shortcut i n :=
    iter_positive shortcut shortcut_positive i n hmin.1.1
  have hnonterminal : ¬ Terminal (iter shortcut i n) := by
    intro ht
    exact hmin.1.2 ⟨i, ht⟩
  have hnot1 : iter shortcut i n ≠ 1 := by
    intro h
    exact hnonterminal (Or.inl h)
  have hnot2 : iter shortcut i n ≠ 2 := by
    intro h
    exact hnonterminal (Or.inr h)
  have hgt : 2 < iter shortcut i n := by omega
  exact ⟨i, j - i, hk, hgt,
    minimal_positive_bad_never_below_source hmin i,
    by simpa only [hsum] using heq.symm⟩

/-- THE UNIVERSAL RESIDUAL IN SMALLEST CONSEQUENTIAL FORM.

Every hypothetical LEAST POSITIVE bad source must have one of two
genuine, source-attached mathematical behaviours:
  1) an actual strictly nonterminal positive cycle on its forward tail,
     at a state >= the original source; OR
  2) an orbit unbounded in ordinary natural VALUE, and every trajectory
     value is >= the unchanged original source.

A V103 nonzero admitted affine return is not a third final behaviour:
its entire deterministic Nat orbit still falls into this dichotomy.

Neither disjunct is excluded here. Collatz remains UNKNOWN.
-/
theorem least_positive_bad_nonterminal_cycle_or_unbounded_no_descent
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    (∃ i k : Nat, 0 < k ∧
      2 < iter shortcut i n ∧
      n ≤ iter shortcut i n ∧
      iter shortcut (i + k) n = iter shortcut i n) ∨
    (∀ B : Nat, ∃ k : Nat,
      B < iter shortcut k n ∧ n ≤ iter shortcut k n) := by
  rcases actual_orbit_eventually_periodic_or_unbounded n with hp | hu
  · obtain ⟨i, k, hk, heq⟩ := hp
    have hpositive : 0 < iter shortcut i n :=
      iter_positive shortcut shortcut_positive i n hmin.1.1
    have hnonterminal : ¬ Terminal (iter shortcut i n) := by
      intro ht
      exact hmin.1.2 ⟨i, ht⟩
    have hnot1 : iter shortcut i n ≠ 1 := by
      intro h
      exact hnonterminal (Or.inl h)
    have hnot2 : iter shortcut i n ≠ 2 := by
      intro h
      exact hnonterminal (Or.inr h)
    have hgt : 2 < iter shortcut i n := by omega
    exact Or.inl ⟨i, k, hk, hgt,
      minimal_positive_bad_never_below_source hmin i, heq⟩
  · right
    intro B
    obtain ⟨k, hk⟩ := hu B
    exact ⟨k, hk, minimal_positive_bad_never_below_source hmin k⟩

#print axioms actual_orbit_eventually_periodic_or_unbounded
#print axioms actual_repeated_endpoint_gives_tail_period
#print axioms minimal_positive_bad_never_below_source
#print axioms minimal_positive_bad_no_earlier_source_meeting
#print axioms minimal_positive_bad_bounded_has_nonterminal_period
#print axioms least_positive_bad_nonterminal_cycle_or_unbounded_no_descent

end SourceProduct
end CollatzFinal
