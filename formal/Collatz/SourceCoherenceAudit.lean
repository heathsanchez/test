import Collatz.ReverseTargetBoundary
import Collatz.StrictDescentReduction

namespace CollatzFinal
namespace SourceProduct

/-- Necessary numerical conditions are not a replacement for the actual
source orbit, its first-crossing prefix, or its actual accumulated bias. -/
def JoinedNumericEnvelope (n y d q b : Nat) : Prop :=
  1 < n ∧ n ≤ y ∧ q < n ∧ 3 * (y - n) < q ∧
  q = oddCount n d ∧ q + 1 = qmin d ∧
  2 ^ (d - 1) ≤ 3 ^ q ∧ 3 ^ q < 2 ^ d ∧
  2 ^ d * y = 3 ^ q * n + b ∧ 3 * b ≤ q * 3 ^ q ∧
  y % 12 = 7

/-- A finite forward-invariant set containing every positive source below 7.
Closure certifies avoidance at all depths, not merely at a search cutoff. -/
def SafeBelowSeven (x : Nat) : Prop :=
  x = 1 ∨ x = 2 ∨ x = 3 ∨ x = 4 ∨ x = 5 ∨ x = 6 ∨ x = 8

theorem safeBelowSeven_small {x : Nat} (hx : 0 < x) (hsmall : x < 7) :
    SafeBelowSeven x := by
  unfold SafeBelowSeven
  omega

theorem safeBelowSeven_step {x : Nat} (hx : SafeBelowSeven x) :
    SafeBelowSeven (shortcut x) := by
  unfold SafeBelowSeven at hx
  rcases hx with rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
    unfold SafeBelowSeven <;> decide

theorem safeBelowSeven_iter {x : Nat} (hx : SafeBelowSeven x) (k : Nat) :
    SafeBelowSeven (iter shortcut k x) := by
  induction k generalizing x with
  | zero => exact hx
  | succ k ih =>
      change SafeBelowSeven (iter shortcut k (shortcut x))
      exact ih (safeBelowSeven_step hx)

theorem safeBelowSeven_ne_seven {x : Nat} (hx : SafeBelowSeven x) :
    x ≠ 7 := by
  unfold SafeBelowSeven at hx
  omega

/-- An all-depth statement, certified by finite invariant closure. -/
theorem no_smaller_source_ever_reaches_seven :
    ∀ p k, 0 < p → p < 7 → iter shortcut k p ≠ 7 := by
  intro p k hp hsmall
  exact safeBelowSeven_ne_seven
    (safeBelowSeven_iter (safeBelowSeven_small hp hsmall) k)

theorem seven_has_no_endpoint_exit : ¬ OrdinaryExit 7 7 := by
  intro h
  rcases h with ht | hd | hm
  · simp [Terminal] at ht
  · omega
  · obtain ⟨p, k, hp, hsmall, heq⟩ := hm
    exact no_smaller_source_ever_reaches_seven p k hp hsmall heq

/-- This numerical envelope includes the actual total odd count at depth 8.
The chosen bias is nevertheless not the actual source's bias. -/
theorem joined_numeric_fixture : JoinedNumericEnvelope 7 7 8 5 91 := by
  unfold JoinedNumericEnvelope
  decide

theorem seven_eight_is_not_first_crossing :
    ¬ FirstCoefficientCrossingAt 7 8 := by
  intro h
  have hc : CoefficientCrossingAt 7 7 := by
    unfold CoefficientCrossingAt
    decide
  exact h.2 7 (by decide) hc

/-- The numerical envelope and absence of all smaller predecessors are jointly
consistent. The fixture is not an actual hard first crossing. -/
theorem joined_source_coupling_separator :
    JoinedNumericEnvelope 7 7 8 5 91 ∧
    ¬ OrdinaryExit 7 7 ∧
    iter shortcut 8 7 = 8 ∧
    bias 7 8 = 347 ∧
    ¬ FirstCoefficientCrossingAt 7 8 := by
  exact ⟨joined_numeric_fixture, seven_has_no_endpoint_exit,
    by decide, by decide, seven_eight_is_not_first_crossing⟩

theorem numeric_envelope_alone_cannot_force_exit :
    ¬ (∀ n y d q b, JoinedNumericEnvelope n y d q b → OrdinaryExit n y) := by
  intro h
  exact seven_has_no_endpoint_exit (h 7 7 8 5 91 joined_numeric_fixture)

/-- Ordinary exits persist: direct descent becomes a lower-merge witness on
subsequent steps. Thus certificate reuse must retain all exit types. -/
theorem joined_ordinary_exit_step {n y : Nat} (h : OrdinaryExit n y) :
    OrdinaryExit n (shortcut y) := by
  rcases h with ht | hd | hm
  · exact Or.inl (terminal_forward_invariant y ht)
  · exact Or.inr (Or.inr ⟨y, 1, hd.1, hd.2, by simp [iter]⟩)
  · obtain ⟨p, b, hp, hsmall, heq⟩ := hm
    refine Or.inr (Or.inr ⟨p, b + 1, hp, hsmall, ?_⟩)
    calc
      iter shortcut (b + 1) p = shortcut (iter shortcut b p) := iter_succ_last p b
      _ = shortcut y := congrArg shortcut heq

theorem joined_ordinary_exit_persists (n y j : Nat) (h : OrdinaryExit n y) :
    OrdinaryExit n (iter shortcut j y) := by
  induction j generalizing y with
  | zero => exact h
  | succ j ih =>
      change OrdinaryExit n (iter shortcut j (shortcut y))
      exact ih (shortcut y) (joined_ordinary_exit_step h)

/-- A later no-exit endpoint rules out every earlier exit on the same source
path. The converse forward-invariance claim for no-exit states is false. -/
theorem joined_no_exit_later_excludes_earlier
    {n a b : Nat}
    (hno : ¬ OrdinaryExit n (iter shortcut (a + b) n)) :
    ¬ OrdinaryExit n (iter shortcut a n) := by
  intro h
  have hf := joined_ordinary_exit_persists n (iter shortcut a n) b h
  apply hno
  simpa only [iter_add] using hf

theorem no_exit_is_not_forward_invariant :
    ¬ OrdinaryExit 7 7 ∧ OrdinaryExit 7 (iter shortcut 7 7) := by
  refine ⟨seven_has_no_endpoint_exit, ?_⟩
  exact Or.inr (Or.inl ⟨by decide, by decide⟩)

/-- Complete source-anchored composition of the two coefficient cases.
The two coverage premises remain explicit: this is not global closure.
The crossing branch may exit later, and may use a lower merge rather than
strict descent at the first crossing itself. -/
theorem reaches_one_of_anchored_branch_exits
    (hSurvivingPathExit :
      ∀ n, 1 < n → EternalCoefficientSurvival n →
        ∃ k, OrdinaryExit n (iter shortcut k n))
    (hCrossingPathExit :
      ∀ n d, 1 < n → FirstCoefficientCrossingAt n d →
        ∃ j, OrdinaryExit n (iter shortcut (d + j) n)) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply reaches_one_of_eventual_ordinary_exit_gt_one
  intro n hn
  rcases coefficient_survival_or_first_crossing n with hs | ⟨d, hd⟩
  · exact hSurvivingPathExit n hn hs
  · obtain ⟨j, hj⟩ := hCrossingPathExit n d hn hd
    exact ⟨d + j, hj⟩

#print axioms no_smaller_source_ever_reaches_seven
#print axioms joined_source_coupling_separator
#print axioms numeric_envelope_alone_cannot_force_exit
#print axioms joined_ordinary_exit_step
#print axioms joined_ordinary_exit_persists
#print axioms joined_no_exit_later_excludes_earlier
#print axioms no_exit_is_not_forward_invariant
#print axioms reaches_one_of_anchored_branch_exits

end SourceProduct
end CollatzFinal
