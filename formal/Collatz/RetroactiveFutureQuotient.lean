import Collatz.UniversalFutureClassFrontier

namespace CollatzFinal
namespace SourceProduct

/-!
V168 — RETROACTIVE, SOURCE-ATTACHED FUTURE-CLASS CERTIFICATE REUSE.

This module proves the SOUNDNESS of certifying an arbitrary original
source from a finite graph of actual two-clock endpoint equalities.

CRUCIAL ADAPTATION: an edge can join TWO UNCERTIFIED sources.
No source ordering and no premise that either source converges is
required to admit that edge. Only an actual checked pair of clocks
and the common real endpoint is required.

When ANY representative eventually obtains a true terminal witness,
the evidence can be propagated backwards through every edge,
including edges discovered earlier between unknown sources.

The proof system below is an exact, finite, compositional compiler.
The finite ledger contains proof terms for its joins and terminals.
It does NOT assert that a finite ledger exists which closes ALL
positive integers, nor any all-scale density or convergence claim.

The separate, exact V168 C++/Python audit supplies bounded ledgers
and checks them against actual natural shortcut arithmetic. Those
finite ledgers are NOT individually imported as millions of Lean
terms into this kernel module. GLOBAL COLLATZ UNKNOWN — NO QED.
-/

/-- Every stored edge carries two genuine, independent ORIGINAL-source
    clocks and a proved endpoint equality; no residue-only shortcut
    or unverified 2-adic ghost is an admissible constructor. -/
structure V168TwoClockEdge where
  source : Nat
  other : Nat
  sourceClock : Nat
  otherClock : Nat
  sourcePositive : 0 < source
  otherPositive : 0 < other
  sameEndpoint :
    iter shortcut sourceClock source =
    iter shortcut otherClock other

/-- An entirely finite receipt for reaching the REAL terminal class. -/
structure V168TerminalSeed where
  source : Nat
  clock : Nat
  positive : 0 < source
  endpointTerminal : Terminal (iter shortcut clock source)

/-- A proof-preserving, order-independent union closure. A stored edge
    is admissible even when both source nodes lack terminal proofs. -/
inductive V168Path (edges : List V168TwoClockEdge) :
    Nat → Nat → Prop where
  | identity (n : Nat) : V168Path edges n n
  | observed (e : V168TwoClockEdge) (he : e ∈ edges) :
      V168Path edges e.source e.other
  | reverse {n m : Nat} (h : V168Path edges n m) :
      V168Path edges m n
  | compose {n m p : Nat}
      (ha : V168Path edges n m)
      (hb : V168Path edges m p) :
      V168Path edges n p

/-- The ENTIRE finite union ledger is a sound subset of true
    actual natural future-coalescence, independent of discovery order. -/
theorem v168_path_sound
    (edges : List V168TwoClockEdge) {n m : Nat}
    (h : V168Path edges n m) :
    V155FutureMeet n m := by
  induction h with
  | identity x =>
      exact v155_future_meet_refl x
  | observed e he =>
      exact ⟨e.sourceClock,e.otherClock,e.sameEndpoint⟩
  | reverse h ih =>
      exact v155_future_meet_symm ih
  | compose ha hb iha ihb =>
      exact v155_future_meet_trans iha ihb

/-- A terminal warrant can be discovered LATER, after an arbitrarily
    long chain of already verified but initially uncertified merges.
    This is the operational capability missing from V167's earlier-
    ALREADY-certified-only source-ordered worklist. -/
theorem v168_retroactive_terminal_reuse
    (edges : List V168TwoClockEdge)
    (seed : V168TerminalSeed) {n : Nat}
    (hPath : V168Path edges n seed.source) :
    CollatzGood n := by
  have hRoot : CollatzGood seed.source :=
    ⟨seed.clock,seed.endpointTerminal⟩
  have hMeetRoot : V155FutureMeet seed.source 1 :=
    (v155_future_meets_one_iff_good seed.source).mpr hRoot
  have hMeet : V155FutureMeet n 1 :=
    v155_future_meet_trans
      (v168_path_sound edges hPath) hMeetRoot
  exact (v155_future_meets_one_iff_good n).mp hMeet

/-- Finite ledger closure membership. This Prop is proof-bearing,
    not a guessed future-class label. -/
def V168LedgerCloses
    (edges : List V168TwoClockEdge)
    (terminalSeeds : List V168TerminalSeed)
    (n : Nat) : Prop :=
  ∃ seed : V168TerminalSeed,
    seed ∈ terminalSeeds ∧
    V168Path edges n seed.source

theorem v168_every_ledger_closure_is_genuine
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (n : Nat)
    (h : V168LedgerCloses edges seeds n) :
    CollatzGood n := by
  obtain ⟨seed,_hMember,hPath⟩ := h
  exact v168_retroactive_terminal_reuse edges seed hPath

/-- A COMPLETE finite ledger is already an all-source theorem
    for precisely its stated finite cutoff, with no higher source
    silently included. The finite coverage premise must be checked
    independently for the stated source population. -/
theorem v168_finite_certified_population
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    (X : Nat)
    (hAll : ∀ n : Nat, 0 < n → n < X →
      V168LedgerCloses edges seeds n) :
    ∀ n : Nat, 0<n → n<X → CollatzGood n := by
  intro n hn hlt
  exact v168_every_ledger_closure_is_genuine
    edges seeds n (hAll n hn hlt)

/-- Warranted evidence is monotone under the ADDITION of independently
    qualified actual joins. This does not justify silently deleting a
    supporting join; on revocation, re-evaluate the proof lineage. -/
theorem v168_ledger_path_monotone
    (E F : List V168TwoClockEdge)
    (hInclude : ∀ e, e ∈ E → e ∈ F)
    {n m : Nat} (h : V168Path E n m) :
    V168Path F n m := by
  induction h with
  | identity x =>
      exact .identity x
  | observed e he =>
      exact .observed e (hInclude e he)
  | reverse h ih =>
      exact .reverse ih
  | compose ha hb iha ihb =>
      exact .compose iha ihb

/-- A nonconvergent original source, if one existed, CANNOT appear
    in a warranted component that also has a terminal witness.
    A bounded timeout does not supply the nonconvergence premise. -/
theorem v168_bad_source_excludes_terminal_component
    (edges : List V168TwoClockEdge)
    (seeds : List V168TerminalSeed)
    {n : Nat} (hBad : ¬ CollatzGood n) :
    ¬ V168LedgerCloses edges seeds n := by
  intro hLedger
  exact hBad (v168_every_ledger_closure_is_genuine
    edges seeds n hLedger)

/-- A directly certified true 1<->2 seed may be reused after
    any chain of valid edges. No new terminal search is needed. -/
theorem v168_ledger_path_to_one_closes
    (edges : List V168TwoClockEdge)
    {n : Nat} (hPath : V168Path edges n 1) :
    CollatzGood n := by
  have hMeet : V155FutureMeet n 1 :=
    v168_path_sound edges hPath
  exact (v155_future_meets_one_iff_good n).mp hMeet

#print axioms v168_path_sound
#print axioms v168_retroactive_terminal_reuse
#print axioms v168_every_ledger_closure_is_genuine
#print axioms v168_finite_certified_population
#print axioms v168_ledger_path_monotone
#print axioms v168_bad_source_excludes_terminal_component
#print axioms v168_ledger_path_to_one_closes

end SourceProduct
end CollatzFinal
