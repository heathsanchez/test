import Collatz.RetroactiveFutureQuotient

set_option maxRecDepth 16384

namespace CollatzFinal
namespace SourceProduct

/-!
V172 — SOURCE-HEIGHT UNLOCK BY TWO GENUINE FUTURE JOINS.

This module is an exact, finite certificate for one difficult source
that is NOT terminal-certified by a direct clock cap H=176. It uses
two larger ORIGINAL source IDs that become available between cutoffs
2^22 and 2^24, reuses a terminal-certified third source, and
reconstructs the 335-clock actual terminal consequence without
spending 335 clocks in any one component of the certificate.

This is a local verified capability, NOT an all-scale Collatz theorem.
Global Collatz UNKNOWN — NO QED.
-/

/-- First genuine two-clock source meet: both clocks are <=176.
The intermediate source 5,640,039 exceeds the old 2^22 cutoff. -/
def v172HeightBridgeOne : V168TwoClockEdge where
  source := 4053039
  other := 5640039
  sourceClock := 141
  otherClock := 2
  sourcePositive := by omega
  otherPositive := by omega
  sameEndpoint := by decide

/-- Second genuine two-clock source meet: the new source 5,575,759
has a separate, independently verified terminal clock. -/
def v172HeightBridgeTwo : V168TwoClockEdge where
  source := 5640039
  other := 5575759
  sourceClock := 65
  otherClock := 0
  sourcePositive := by omega
  otherPositive := by omega
  sameEndpoint := by decide

/-- Actual terminal seed available by clock 131, within H=176. -/
def v172HeightTerminalSeed : V168TerminalSeed where
  source := 5575759
  clock := 131
  positive := by omega
  endpointTerminal := by
    have h : iter shortcut 131 5575759 = 2 := by decide
    rw [h]
    simp [Terminal]

/-- Proof-carrying finite ledger records both original sources, both
independent clocks, and the authentic terminal seed. -/
theorem v172_height_unlocked_finite_ledger :
    V168LedgerCloses
      [v172HeightBridgeOne, v172HeightBridgeTwo]
      [v172HeightTerminalSeed] 4053039 := by
  refine ⟨v172HeightTerminalSeed, by simp, ?_⟩
  have hOne : v172HeightBridgeOne ∈
      [v172HeightBridgeOne, v172HeightBridgeTwo] := by simp
  have hTwo : v172HeightBridgeTwo ∈
      [v172HeightBridgeOne, v172HeightBridgeTwo] := by simp
  have hA := V168Path.observed v172HeightBridgeOne hOne
  have hB := V168Path.observed v172HeightBridgeTwo hTwo
  exact V168Path.compose hA hB

/-- A complete, genuine terminal warrant assembled from separately
proved source/clock witnesses; no guessed convergence premise. -/
theorem v172_height_unlocked_terminal_certificate :
    CollatzGood 4053039 := by
  exact v168_every_ledger_closure_is_genuine
    [v172HeightBridgeOne, v172HeightBridgeTwo]
    [v172HeightTerminalSeed]
    4053039
    v172_height_unlocked_finite_ledger

/-- The compiled three-part certificate never requires a source clock
exceeding the original finite cutoff H=176. -/
theorem v172_all_component_clocks_below_176 :
    v172HeightBridgeOne.sourceClock ≤ 176 ∧
    v172HeightBridgeOne.otherClock ≤ 176 ∧
    v172HeightBridgeTwo.sourceClock ≤ 176 ∧
    v172HeightBridgeTwo.otherClock ≤ 176 ∧
    v172HeightTerminalSeed.clock ≤ 176 := by
  decide

/-- Genuine ORIGINAL source-height separation: both bridge owners
are admitted at cutoff 2^24 but excluded at cutoff 2^22. -/
theorem v172_new_height_is_essential_to_this_ledger :
    4053039 < 2^22 ∧
    2^22 ≤ 5640039 ∧ 5640039 < 2^24 ∧
    2^22 ≤ 5575759 ∧ 5575759 < 2^24 := by
  decide

/-- Protected ONE-ARROW non-Collatz control: only source5's next
state is changed. The two-height joins above remain real for this
modified map, but its would-be terminal seed falls into fixed5.
This prevents promoting arbitrary coalescence to convergence. -/
def v172OneArrowControl (n : Nat) : Nat :=
  if n = 5 then 5 else shortcut n

theorem v172_one_arrow_only_changes_five (n : Nat)
    (hn : n ≠ 5) :
    v172OneArrowControl n = shortcut n := by
  simp [v172OneArrowControl, hn]

theorem v172_one_arrow_five_is_fixed :
    v172OneArrowControl 5 = 5 := by decide

theorem v172_one_arrow_retains_first_join :
    iter v172OneArrowControl 141 4053039 =
    iter v172OneArrowControl 2 5640039 := by decide

theorem v172_one_arrow_retains_second_join :
    iter v172OneArrowControl 65 5640039 =
    iter v172OneArrowControl 0 5575759 := by decide

theorem v172_one_arrow_terminal_anchor_fails :
    iter v172OneArrowControl 131 5575759 = 5 := by decide

theorem v172_one_arrow_rejects_terminal_promotion :
    ¬ Terminal (iter v172OneArrowControl 131 5575759) := by
  rw [v172_one_arrow_terminal_anchor_fails]
  simp [Terminal]

#print axioms v172_one_arrow_retains_first_join
#print axioms v172_one_arrow_retains_second_join
#print axioms v172_one_arrow_terminal_anchor_fails
#print axioms v172_one_arrow_rejects_terminal_promotion

#print axioms v172_height_unlocked_finite_ledger
#print axioms v172_height_unlocked_terminal_certificate
#print axioms v172_all_component_clocks_below_176
#print axioms v172_new_height_is_essential_to_this_ledger

end SourceProduct
end CollatzFinal
