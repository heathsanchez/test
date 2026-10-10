import Collatz.RetroactiveFutureQuotient

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

/-- An arbitrary finite list of original sources is represented by its
actual source identities. If all entries genuinely hit the same bad
target inside the supplied clock and have checked two-clock paths into
one finite graph component, then every entry lies in that ONE
terminal-disconnected component.

This is the proof-level membership bridge. No distinctness, density
or all-scale cardinal assumption is silently introduced. The finite
cardinality lower bound additionally requires P.Nodup, an elementary
finite-list consequence outside this theorem's stated verification
boundary. -/
theorem v169_clocked_population_in_one_unseeded_component
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (target X H : Nat)
    (P : List Nat)
    (hBad : ¬ CollatzGood target)
    (hSources : ∀ n, n ∈ P →
       0 < n ∧ n < X ∧ V169HitWithin n target H)
    (hComplete : ∀ n, n ∈ P →
       V168Path edges n target) :
    ∀ n, n ∈ P →
      0 < n ∧ n < X ∧ V168Path edges n target ∧
        ¬ V168LedgerCloses edges seeds n := by
  intro n hn
  obtain ⟨hpos, hX, _hClock⟩ := hSources n hn
  have hPath := hComplete n hn
  exact ⟨hpos, hX, hPath,
    v169_bad_path_excludes_terminal_seed
      edges seeds hBad hPath⟩

#print axioms v169_hit_is_future_meeting
#print axioms v169_bad_target_forces_bad_clocked_ancestor
#print axioms v169_bad_path_excludes_terminal_seed
#print axioms v169_clocked_population_in_one_unseeded_component

end SourceProduct
end CollatzFinal
