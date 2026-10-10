import Collatz.RetroactiveFutureQuotient
import Mathlib.Data.Finset.Card

namespace CollatzFinal
namespace SourceProduct

/-!
V169 — clocked predecessor-density to largest unseeded component.

The external positive-density, LOGARITHMIC-TIME predecessor theorem is
NOT imported here. It is a separately declared source-count hypothesis.
The compiler completeness condition for finite two-clock edges is also
explicit. This proves the exact NONCIRCULAR CONDITIONAL bridge that a
hypothetical bad target with many short-clock predecessors forces one
large terminal-disconnected verified component.

Neither that predecessor-density theorem nor a uniform all-scale
anti-giant bound is established by the present module.
Global Collatz UNKNOWN. No QED.
-/

/-- A true original-source hit within H genuine shortcut clocks. -/
def V169HitWithin (n target H : Nat) : Prop :=
  ∃ t : Nat, t ≤ H ∧ iter shortcut t n = target

/-- Actual finite-clock source hit gives a bona fide future-class edge. -/
theorem v169_hit_is_future_meeting
    (n target H : Nat) (h : V169HitWithin n target H) :
    V155FutureMeet n target := by
  obtain ⟨t, _, ht⟩ := h
  refine ⟨t, 0, ?_⟩
  simpa only [iter] using ht

/-- Genuine clocked ancestors of a truly bad target must themselves be bad.
No unknown timeout is being classified as nonconvergent. -/
theorem v169_bad_target_forces_bad_clocked_ancestor
    (n target H : Nat)
    (hBad : ¬ CollatzGood target)
    (hHit : V169HitWithin n target H) :
    ¬ CollatzGood n := by
  intro hGood
  have hMeet : V155FutureMeet target n :=
    v155_future_meet_symm
      (v169_hit_is_future_meeting n target H hHit)
  have hMeetOne : V155FutureMeet target 1 :=
    v155_future_meet_trans hMeet
      ((v155_future_meets_one_iff_good n).mpr hGood)
  exact hBad ((v155_future_meets_one_iff_good target).mp hMeetOne)

/-- Any finite sound path to a bad target cannot be terminal seeded. -/
theorem v169_bad_path_excludes_terminal_seed
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    {n target : Nat}
    (hBad : ¬ CollatzGood target)
    (hPath : V168Path edges n target) :
    ¬ V168LedgerCloses edges seeds n := by
  intro hLedger
  have hGood : CollatzGood n :=
    v168_every_ledger_closure_is_genuine edges seeds n hLedger
  have hMeet : V155FutureMeet target n :=
    v155_future_meet_symm (v168_path_sound edges hPath)
  have hMeetOne : V155FutureMeet target 1 :=
    v155_future_meet_trans hMeet
      ((v155_future_meets_one_iff_good n).mpr hGood)
  exact hBad ((v155_future_meets_one_iff_good target).mp hMeetOne)

/-- The exact observed, terminal-disconnected graph component containing
a hypothetical target. Its source cutoff is EXPLICIT and finite. -/
noncomputable def V169UnseededComponent
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (target X : Nat) : Finset Nat := by
  classical
  exact (Finset.range X).filter (fun n =>
    0 < n ∧ V168Path edges n target ∧
      ¬ V168LedgerCloses edges seeds n)

/-- A valid witnessed short-clock predecessor population P, whose
two-clock receipts are contained in the finite graph, lies entirely
in ONE unseeded component if its target is truly bad.

This is the exact finite combinatorial ingredient for a conditional
positive-density -> giant-unseeded-component argument. Neither
large P nor global shrinking of largest components is assumed as
an established Collatz fact here. -/
theorem v169_clocked_density_implies_large_unseeded_component
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (target X H K : Nat)
    (P : Finset Nat)
    (hBad : ¬ CollatzGood target)
    (hSources : ∀ n, n ∈ P →
       0 < n ∧ n < X ∧ V169HitWithin n target H)
    (hComplete : ∀ n, n ∈ P →
       V168Path edges n target)
    (hMass : K ≤ P.card) :
    K ≤ (V169UnseededComponent edges seeds target X).card := by
  classical
  have hSubset : P ⊆ V169UnseededComponent edges seeds target X := by
    intro n hn
    obtain ⟨hpos, hX, _hClock⟩ := hSources n hn
    change n ∈ (Finset.range X).filter
      (fun z => 0 < z ∧ V168Path edges z target ∧
        ¬ V168LedgerCloses edges seeds z)
    exact Finset.mem_filter.mpr
      ⟨Finset.mem_range.mpr hX,
       hpos,
       hComplete n hn,
       v169_bad_path_excludes_terminal_seed
         edges seeds hBad (hComplete n hn)⟩
  exact hMass.trans (Finset.card_le_card hSubset)

#print axioms v169_hit_is_future_meeting
#print axioms v169_bad_target_forces_bad_clocked_ancestor
#print axioms v169_bad_path_excludes_terminal_seed
#print axioms v169_clocked_density_implies_large_unseeded_component

end SourceProduct
end CollatzFinal
