import Collatz.UniversalFutureClassFrontier

namespace CollatzFinal
namespace SourceProduct

/-!
V173 — REPAIR AN ARTIFICIAL ONE-ARROW BASIN INTO A GENUINE CERTIFICATE.

If a source a is already independently certified in the real shortcut,
consider the deliberately synthetic map that freezes a and otherwise
uses the real shortcut. EVERY source whose synthetic future reaches a
has a TRUE real prefix reaching a, because no earlier step could have
used the one modified arrow.

Therefore an entire synthetic competing basin is *source-attached*
certified at a cost no larger than its genuine first-hit clock plus
the REAL seed's independently verified terminal clock.

This is a universal REUSE theorem, not a proof that all sources hit a,
and not the global Collatz conjecture. It converts V171's one-arrow
adversarial example into a protected diagnostic and a sound infinite
family of transferable terminal consequences.

Global Collatz UNKNOWN — NO QED.
-/

/-- Deliberately artificial absorber at a; exact TRUE Collatz every
other source. This map is NOT the real shortcut at n=a. -/
def v173FreezeAt (a n : Nat) : Nat :=
  if n = a then a else shortcut n

theorem v173_freeze_agrees_before_seed
    (a n : Nat) (hneq : n ≠ a) :
    v173FreezeAt a n = shortcut n := by
  simp [v173FreezeAt, hneq]

/-- ANY finite frozen-a hit has a true original-source prefix hit to a.
Crucially, the returned clock never exceeds the checked artificial
clock: no extra future progress or Collatz convergence is assumed. -/
theorem v173_frozen_hit_implies_true_hit :
    ∀ t a n : Nat,
      iter (v173FreezeAt a) t n = a →
      ∃ i : Nat, i ≤ t ∧ iter shortcut i n = a := by
  intro t
  induction t with
  | zero =>
      intro a n h
      exact ⟨0, by omega, by simpa only [iter] using h⟩
  | succ t ih =>
      intro a n h
      by_cases hSeed : n = a
      · exact ⟨0, by omega, by simpa only [iter] using hSeed⟩
      · have hStep : v173FreezeAt a n = shortcut n :=
          v173_freeze_agrees_before_seed a n hSeed
        have hRest : iter (v173FreezeAt a) t (shortcut n) = a := by
          simpa only [iter, hStep] using h
        obtain ⟨i, hi, hTrue⟩ := ih a (shortcut n) hRest
        refine ⟨i+1, by omega, ?_⟩
        simpa only [iter] using hTrue

/-- Clock-quantified terminal proof reuse. The synthetic clock t and
the real certified seed clock s are both explicit; the whole original
source is shown to reach the true terminal at some u<=t+s. -/
theorem v173_frozen_basin_repair_with_clock
    (a n t s : Nat)
    (hHit : iter (v173FreezeAt a) t n = a)
    (hSeed : Terminal (iter shortcut s a)) :
    ∃ u : Nat, u ≤ t+s ∧ Terminal (iter shortcut u n) := by
  obtain ⟨i, hi, hTrue⟩ :=
    v173_frozen_hit_implies_true_hit t a n hHit
  refine ⟨i+s, by omega, ?_⟩
  rw [iter_add, hTrue]
  exact hSeed

/-- The entire frozen-source basin inherits a genuine CollatzGood
warrant once the ORIGINAL seed has its separately checked proof. -/
theorem v173_frozen_basin_of_verified_seed
    (a n : Nat) (hGood : CollatzGood a)
    (hFrozen : ∃ t : Nat, iter (v173FreezeAt a) t n = a) :
    CollatzGood n := by
  obtain ⟨t, hHit⟩ := hFrozen
  obtain ⟨s, hTerminal⟩ := hGood
  obtain ⟨u, _hBudget, hu⟩ :=
    v173_frozen_basin_repair_with_clock a n t s hHit hTerminal
  exact ⟨u, hu⟩

/-- The source5 arrow is unconditionally true: 5->8->4->2.
No assumed or inferred convergence beyond this genuine clock3 fact. -/
theorem v173_actual_five_terminal :
    CollatzGood 5 := by
  refine ⟨3, ?_⟩
  have h : iter shortcut 3 5 = 2 := by decide
  rw [h]
  simp [Terminal]

/-- Every S5-to-5 source, including arbitrarily large ones, is
really terminal-certified in TRUE Collatz. This does not assert
that EVERY natural source has an S5-to-5 path. -/
theorem v173_true_terminal_for_entire_frozen_five_basin
    (n : Nat)
    (hFrozen : ∃ t : Nat, iter (v173FreezeAt 5) t n = 5) :
    CollatzGood n :=
  v173_frozen_basin_of_verified_seed 5 n v173_actual_five_terminal hFrozen

#print axioms v173_freeze_agrees_before_seed
#print axioms v173_frozen_hit_implies_true_hit
#print axioms v173_frozen_basin_repair_with_clock
#print axioms v173_frozen_basin_of_verified_seed
#print axioms v173_actual_five_terminal
#print axioms v173_true_terminal_for_entire_frozen_five_basin

end SourceProduct
end CollatzFinal
