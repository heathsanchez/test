import Collatz.FirstSuperHighBoundary

namespace CollatzFinal
namespace SourceProduct

/-- Exact finite invariant containing every positive shortcut orbit started
strictly below 27.  It is used only to certify the semantic counterexample to
the old current-endpoint four-thirds premise. -/
def SafeBelowTwentySeven (x : Nat) : Prop :=
  x = 1 ∨ x = 2 ∨ x = 3 ∨ x = 4 ∨ x = 5 ∨ x = 6 ∨ x = 7 ∨ x = 8 ∨
  x = 9 ∨ x = 10 ∨ x = 11 ∨ x = 12 ∨ x = 13 ∨ x = 14 ∨ x = 15 ∨
  x = 16 ∨ x = 17 ∨ x = 18 ∨ x = 19 ∨ x = 20 ∨ x = 21 ∨ x = 22 ∨
  x = 23 ∨ x = 24 ∨ x = 25 ∨ x = 26 ∨ x = 29 ∨ x = 32 ∨ x = 35 ∨
  x = 38 ∨ x = 40 ∨ x = 44 ∨ x = 53 ∨ x = 80

theorem safeBelowTwentySeven_small
    {x : Nat} (hx : 0 < x) (hsmall : x < 27) :
    SafeBelowTwentySeven x := by
  unfold SafeBelowTwentySeven
  omega

theorem safeBelowTwentySeven_step
    {x : Nat} (hx : SafeBelowTwentySeven x) :
    SafeBelowTwentySeven (shortcut x) := by
  unfold SafeBelowTwentySeven at hx
  rcases hx with
    rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
    rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
    rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
    rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl |
    rfl | rfl <;>
    unfold SafeBelowTwentySeven shortcut <;> decide

theorem safeBelowTwentySeven_iter
    {x : Nat} (hx : SafeBelowTwentySeven x) (k : Nat) :
    SafeBelowTwentySeven (iter shortcut k x) := by
  induction k generalizing x with
  | zero =>
      simpa [iter] using hx
  | succ k ih =>
      change SafeBelowTwentySeven (iter shortcut k (shortcut x))
      exact ih (safeBelowTwentySeven_step hx)

theorem no_smaller_source_ever_reaches_ninety_two :
    ∀ p k, 0 < p → p < 27 → iter shortcut k p ≠ 92 := by
  intro p k hp hsmall
  have hs :=
    safeBelowTwentySeven_iter
      (safeBelowTwentySeven_small hp hsmall) k
  unfold SafeBelowTwentySeven at hs
  omega

/-- At the endpoint 92, source 27 has no current OrdinaryExit.
This distinguishes a scheduled quarter-splice consequence from an exit that
already holds at the current endpoint. -/
theorem twenty_seven_ninety_two_no_ordinary_exit :
    ¬ OrdinaryExit 27 92 := by
  intro h
  rcases h with ht | hd | hm
  · simp [Terminal] at ht
  · omega
  · obtain ⟨p, b, hp, hsmall, heq⟩ := hm
    exact no_smaller_source_ever_reaches_ninety_two
      p b hp hsmall heq

/-- The old current-endpoint FourThirdsNoExitOddCap is false.
The 27 orbit reaches x=92 at depth 57 with q=37:
3*37 > 4*27, while no OrdinaryExit holds at x=92.
The earlier x=61 quarter-splice only schedules the lower merge at depth 59. -/
set_option maxRecDepth 10000 in
theorem four_thirds_no_exit_odd_cap_false :
    ¬ FourThirdsNoExitOddCap := by
  intro hCap
  have hiter : iter shortcut 57 27 = 92 := by decide
  have hno : ¬ OrdinaryExit 27 (iter shortcut 57 27) := by
    rw [hiter]
    exact twenty_seven_ninety_two_no_ordinary_exit
  have h := hCap 27 57 (by decide) hno
  have hq : oddCount 27 57 = 37 := by decide
  rw [hq] at h
  omega

/-- The prefix condition actually tested by Crystal V14:
up through depth k the orbit has neither descended below its source nor exposed
a source-relative quarter splice. -/
def DirectQuarterProtectedPrefix (n k : Nat) : Prop :=
  ∀ i, i ≤ k →
    n ≤ iter shortcut i n ∧
    ¬ (iter shortcut i n % 8 = 5 ∧ iter shortcut i n ≤ 4 * n)

/-- Correct four-thirds candidate matching the executable V14 semantics. -/
def FourThirdsProtectedPrefixCap : Prop :=
  ∀ n k, 1 < n →
    DirectQuarterProtectedPrefix n k →
    3 * oddCount n k ≤ 4 * n

/-- A hypothetical minimal bad source satisfies the protected-prefix condition
at every depth: direct descent is impossible, and any quarter-splice event
would schedule an OrdinaryExit three steps later. -/
theorem minimal_bad_direct_quarter_protected_prefix
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n) :
    DirectQuarterProtectedPrefix n k := by
  intro i hi
  constructor
  · exact minimal_bad_nondescending_all_depths hmin i
  · intro hsplice
    have hexit :
        OrdinaryExit n (iter shortcut (i + 3) n) := by
      rw [iter_add]
      exact ordinary_exit_after_quarter_splice hsplice.1 hsplice.2
    exact minimal_bad_has_no_ordinary_exit hmin (i + 3) hexit

/-- The corrected protected-prefix four-thirds cap is a single-premise
closeout.  Unlike FourThirdsNoExitOddCap, its semantics exactly match the
Crystal falsifier. -/
theorem reaches_one_of_four_thirds_protected_prefix_cap
    (hCap : FourThirdsProtectedPrefixCap) :
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
    have hprot :
        DirectQuarterProtectedPrefix n (4 * n) :=
      minimal_bad_direct_quarter_protected_prefix hmin
    have hcap :
        3 * oddCount n (4 * n) ≤ 4 * n :=
      hCap n (4 * n) hgt hprot
    have hstrict :
        2 * n < oddCount n (4 * n) :=
      minimal_bad_quadruple_depth_strict_double_diagonal hmin
    omega
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms four_thirds_no_exit_odd_cap_false
#print axioms minimal_bad_direct_quarter_protected_prefix
#print axioms reaches_one_of_four_thirds_protected_prefix_cap

end SourceProduct
end CollatzFinal
