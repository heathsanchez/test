import Collatz.TimedOrdinaryHitGiantBridge

namespace CollatzFinal
namespace SourceProduct

/-!
V170 — UNIVERSALLY COMPLETE SOURCE-CLOCK RELATION WITHOUT A
SEPARATE LEDGER-COMPLETENESS ASSUMPTION.

V169 established the ordinary-to-shortcut clock conversion and
bad-target macroscopic component bridge under THREE premises:
timed-target positive density; finite-ledger completeness; sparse
non-giant component mass.

This module ELIMINATES the second premise, not by asserting that
a heuristic algorithm is complete, but by defining the CANONICAL
full finite graph directly from all actual, source-indexed two-clock
endpoint equalities at clocks i,j <= H on genuine positive
original source vertices n,m<X.

Every time-bounded predecessor of b<X lies in b's component by
the one-edge constructor. Completeness is unconditional.

The remaining QED implication still has TWO explicit independent
mathematical inputs:
  (1) external timed positive-density for each target b≡2 mod3;
  (2) a Collatz-specific height- and clock-aware no-macroscopic-
      unseeded-component estimate for the full canonical graph.

No asymptotic no-giant estimate is proved here and no external
theorem is silently imported. Global Collatz UNKNOWN, no QED.
-/

/-- The canonical time-H, height-X graph contains EVERY observed
    actual two-clock equality between genuine positive sources
    inside [1,X). Its inductive closure is independent of how
    a finite graph algorithm enumerates edges. -/
inductive V170FullClockPath (X H : Nat) : Nat → Nat → Prop where
  | identity (n : Nat) : V170FullClockPath X H n n
  | meeting {n m i j : Nat}
      (hn : 0<n) (hm : 0<m) (hnX : n<X) (hmX : m<X)
      (hi : i<=H) (hj : j<=H)
      (hEndpoint : iter shortcut i n = iter shortcut j m) :
      V170FullClockPath X H n m
  | reverse {n m : Nat} (h : V170FullClockPath X H n m) :
      V170FullClockPath X H m n
  | compose {n m p : Nat}
      (h1 : V170FullClockPath X H n m)
      (h2 : V170FullClockPath X H m p) :
      V170FullClockPath X H n p

/-- Even after arbitrarily many graph unions, the relation is
    ALWAYS a genuine future-coalescence relation. -/
theorem v170_full_graph_path_sound
    (X H : Nat) {n m : Nat}
    (h : V170FullClockPath X H n m) :
    V155FutureMeet n m := by
  induction h with
  | identity n =>
      exact v155_future_meet_refl n
  | meeting hn hm hnX hmX hi hj hEndpoint =>
      exact ⟨_,_,hEndpoint⟩
  | reverse h ih =>
      exact v155_future_meet_symm ih
  | compose h1 h2 ih1 ih2 =>
      exact v155_future_meet_trans ih1 ih2

/-- Source- and clock-completeness is built in:
    whenever an actual positive original source reaches a
    positive original target b<X within H shortcut clocks,
    its DIRECT graph edge to b exists automatically.

    No completeness assumption on an external executable ledger. -/
theorem v170_timed_hit_has_full_graph_edge
    (X H n b : Nat)
    (hn : 0<n) (hnX : n<X)
    (hb : 0<b) (hbX : b<X)
    (hh : V169ShortcutTimedHit b H n) :
    V170FullClockPath X H n b := by
  obtain ⟨i,hi,hEndpoint⟩ := hh
  exact V170FullClockPath.meeting
    hn hb hnX hbX hi (by omega)
    (by simpa [iter] using hEndpoint)

/-- A finite cutoff component is SEEDED only if an independently
    actual terminal hit occurs within H at some positive original
    source in its full graph component. This is a source-based
    finite-clock notion, not an oracle for eventual convergence. -/
def V170HasTerminalSeed
    (X H n : Nat) : Prop :=
  ∃ p : Nat, 0<p ∧ p<X ∧
    V170FullClockPath X H n p ∧
    ∃ j : Nat, j<=H ∧ Terminal (iter shortcut j p)

/-- A terminal-seeded graph class is soundly convergent
    regardless of the number/order of graph unions. -/
theorem v170_terminal_seeded_class_is_good
    (X H n : Nat)
    (hs : V170HasTerminalSeed X H n) :
    CollatzGood n := by
  obtain ⟨p,hp,_hpX,hpath,j,_hj,hTerm⟩ := hs
  have hGoodP : CollatzGood p := ⟨j,hTerm⟩
  have hMeetP : V155FutureMeet p 1 :=
    (v155_future_meets_one_iff_good p).mpr hGoodP
  have hMeet : V155FutureMeet n 1 :=
    v155_future_meet_trans
      (v170_full_graph_path_sound X H hpath) hMeetP
  exact (v155_future_meets_one_iff_good n).mp hMeet

/-- A genuinely BAD target (if one existed) cannot acquire a
    terminal seed through any valid actual graph path. -/
theorem v170_bad_target_component_has_no_seed
    (X H n b : Nat)
    (hBad : ¬ CollatzGood b)
    (hPath : V170FullClockPath X H n b) :
    ¬ V170HasTerminalSeed X H n := by
  intro hSeed
  have hGoodN :=
    v170_terminal_seeded_class_is_good X H n hSeed
  have hNB := v170_full_graph_path_sound X H hPath
  have hBN := v155_future_meet_symm hNB
  have hNOne : V155FutureMeet n 1 :=
    (v155_future_meets_one_iff_good n).mpr hGoodN
  have hBOne := v155_future_meet_trans hBN hNOne
  exact hBad ((v155_future_meets_one_iff_good b).mp hBOne)

/-- Membership in ONE actual source-clock future component
    which has no independently witnessed terminal seed. -/
def V170UnseededComponent
    (X H b n : Nat) : Prop :=
  0<n ∧ n<X ∧
  V170FullClockPath X H n b ∧
  ¬ V170HasTerminalSeed X H n

/-- Exact count of positive original sources in the time-H,
    height-X canonical unseeded component of b. The abstract
    finite-graph relation is specified mathematically here;
    the executable graph may enumerate it separately. -/
noncomputable def v170UnseededComponentCount
    (X H b : Nat) : Nat := by
  classical
  exact v150Count (V170UnseededComponent X H b) X

/-- Crucial NEW UNCONDITIONAL structural elimination:
    a genuine hypothetical bad b≡2 mod3 absorbs ALL of its
    time-bounded ordinary predecessors in ONE UNSEEDED actual
    component, WITHOUT any external graph-completeness axiom.

    The bad-target premise is hypothetical; no existence of
    a bad target is asserted. -/
theorem v170_bad_target_timed_predecessors_into_one_class
    (X H b n : Nat)
    (hb : 0<b) (hbX : b<X) (hbMod : b%3=2)
    (hBad : ¬ CollatzGood b)
    (hn : 0<n) (hnX : n<X)
    (hOrdinaryHit : V169OrdinaryTimedHit b H n) :
    V170UnseededComponent X H b n := by
  have hTimed :
      V169ShortcutTimedHit b H n :=
    v169_timed_ordinary_hit_to_actual_shortcut
      b H n hbMod hOrdinaryHit
  have hPath :=
    v170_timed_hit_has_full_graph_edge
      X H n b hn hnX hb hbX hTimed
  exact ⟨hn,hnX,hPath,
    v170_bad_target_component_has_no_seed
      X H n b hBad hPath⟩

/-- Entire finite true ordinary timed predecessor population
    fits in ONE unseeded canonical graph class. -/
theorem v170_bad_target_timed_count_lower_bound
    (X H b : Nat)
    (hb : 0<b) (hbX : b<X) (hbMod : b%3=2)
    (hBad : ¬ CollatzGood b) :
    v169OrdinaryTimedCount b H X <=
      v170UnseededComponentCount X H b := by
  classical
  change
    v150Count
      (fun n => 0<n ∧ V169OrdinaryTimedHit b H n) X <=
    v150Count (V170UnseededComponent X H b) X
  apply v150_count_monotone_below
  intro n hnX h
  exact v170_bad_target_timed_predecessors_into_one_class
    X H b n hb hbX hbMod hBad h.1 hnX h.2

/-- The exact now-SOLE new arithmetic obstruction:
    for all prescribed q,X0, on at least one sufficiently
    large dyadic cutoff, NO residue-2 target can have a
    terminal-UNSEEDED canonical H(k) class with size >=2^k/q.

    This is a proposed mathematical inequality, NOT proved.
    A finite-window experiment cannot discharge its quantifiers.
-/
def V170SparseNoGiantOnResidueTwo
    (H : Nat → Nat) : Prop :=
  ∀ q X0 : Nat, 0<q →
    ∃ k : Nat, X0 <= 2^k ∧
      ∀ b : Nat, b%3=2 → b<2^k →
        q*v170UnseededComponentCount (2^k) (H k) b < 2^k

/-- Fully constructively eliminates V169's third-party
    finite-graph completeness premise by using the complete
    mathematical source-clock graph. The global conclusion is
    STILL CONDITIONAL on exactly two separately stated claims:
    targetwise timed predecessor positive density, and
    arithmetic no-giant elimination for true +1 dynamics.

    Neither is smuggled in from the bounded V168/V169 audits.
-/
theorem v170_collatz_of_timed_density_and_sparse_no_giant
    (H : Nat → Nat)
    (hTimed : V169TimedTargetDensity H)
    (hNoGiant : V170SparseNoGiantOnResidueTwo H) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  have hNoMin : ∀ m : Nat, ¬ MinimalBad PositiveBad m := by
    intro m hMin
    obtain ⟨hBadB,hModB⟩ :=
      v150_minimal_bad_has_nonthree_bad_successor hMin
    let b := shortcut m
    obtain ⟨q,X0,hq,hLower⟩ :=
      hTimed b hModB
    obtain ⟨k,hX,hUpper⟩ :=
      hNoGiant q (X0+b+1) hq
    have hbX : b<2^k := by omega
    have hX0 : X0<=2^k := by omega
    have hCount :=
      v170_bad_target_timed_count_lower_bound
        (2^k) (H k) b hBadB.1 hbX hModB hBadB.2
    have hWeighted := Nat.mul_le_mul_left q hCount
    have hLo := hLower k hX0
    have hHi := hUpper b hModB hbX
    omega
  have hNoBad := no_bad_of_no_minimal PositiveBad hNoMin
  intro n hn
  apply Classical.byContradiction
  intro hBad
  exact hNoBad n ⟨hn,hBad⟩

/-- The 8k source-dependent clock matching the external
    ordinary logarithmic-time assertion c=11 with
    11 log2<8, independently of a source-specific bound. -/
def v170EightKClock (k : Nat) : Nat := 8*k

#print axioms v170_full_graph_path_sound
#print axioms v170_timed_hit_has_full_graph_edge
#print axioms v170_terminal_seeded_class_is_good
#print axioms v170_bad_target_component_has_no_seed
#print axioms v170_bad_target_timed_predecessors_into_one_class
#print axioms v170_bad_target_timed_count_lower_bound
#print axioms v170_collatz_of_timed_density_and_sparse_no_giant

end SourceProduct
end CollatzFinal
