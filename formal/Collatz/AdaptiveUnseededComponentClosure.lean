import Collatz.DominantClockSourceGraph
import Collatz.RetroactiveFutureQuotient

namespace CollatzFinal
namespace SourceProduct

/-!
V173 — ONE QUALIFIED ACTUAL EDGE CLOSES AN ENTIRE PREVIOUSLY
UNSEEDED FUTURE COMPONENT, RETROACTIVELY.

The V172 source-clock graph may have a finite number c of
genuine unseeded original-source components. We need not run
every source again: take one ACTUAL representative from each
component and continue its real shortcut trajectory until a
meeting edge with an already terminal-seeded component occurs.

V168 proves every arbitrary finite chain of exact source/clock
meetings is sound, even if both sources were initially UNKNOWN.
The new lemma proves the ONE-EDGE admission rule for every
source in an entire preexisting component, with all dependencies
and the target's terminal proof explicit.

This is a generic CERTIFICATE COMPILER for verified true
Collatz meetings, not a theorem that the required edges
eventually exist for every component at all source scales.

A finite union-graph argument gives a conditional lower bound:
if c pre-existing unseeded components all become seeded using
only binary component-joining edges (no new direct terminal
seeds), at least c effective joins are needed, because each
effective edge reduces unseeded component count by at most one.
The full graph-count lower bound is ordinary combinatorics
and is NOT separately kernel formalized in this file.

The bounded V173 Python+C++ audit supplies specific exact
source-and-clock edge witnesses at k=24 and k=25; they are
not million-line Lean source-specific certificates.

GLOBAL COLLATZ UNKNOWN. NO QED.
-/

/-- The new edge has EXACT real original-source and original-owner
    meeting clocks. No finite residue equivalence can replace it. -/
def v173RealEdge
    (n p i j : Nat)
    (hn : 0<n) (hp : 0<p)
    (hEqual : iter shortcut i n = iter shortcut j p) :
    V168TwoClockEdge :=
  ⟨n,p,i,j,hn,hp,hEqual⟩

/-- Every old evidence path survives adding a single new,
    independently checked two-clock edge. -/
theorem v173_old_path_in_new_ledger
    (E : List V168TwoClockEdge)
    (e : V168TwoClockEdge)
    {n m : Nat}
    (hPath : V168Path E n m) :
    V168Path (e::E) n m := by
  exact v168_ledger_path_monotone E (e::E)
    (by intro x hx; simp [hx]) hPath

/-- The entire original-source component linked to representative
    rep becomes genuinely terminal-certified after ONE new actual
    edge rep->owner into a previously terminal-seeded class.

    No assumption that rep or its members were already Good.
    This is the key retroactive proof-reuse distinction. -/
theorem v173_one_new_edge_closes_entire_component
    (E : List V168TwoClockEdge)
    (seed : V168TerminalSeed)
    (e : V168TwoClockEdge)
    (rep : Nat)
    (hRep : e.source = rep)
    (hOwnerSeed : V168Path E e.other seed.source) :
    ∀ n : Nat, V168Path E n rep → CollatzGood n := by
  intro n hOld
  have hOld' : V168Path (e::E) n rep :=
    v173_old_path_in_new_ledger E e hOld
  have hEdge : V168Path (e::E) rep e.other := by
    have hh : V168Path (e::E) e.source e.other :=
      V168Path.observed e (by simp)
    simpa only [hRep] using hh
  have hSeed' : V168Path (e::E) e.other seed.source :=
    v173_old_path_in_new_ledger E e hOwnerSeed
  have hNew : V168Path (e::E) n seed.source :=
    V168Path.compose hOld' (V168Path.compose hEdge hSeed')
  exact v168_retroactive_terminal_reuse (e::E) seed hNew

/-- Event form of the preceding compiler with an explicit
    mathematical two-clock equality, not a guessed graph edge. -/
theorem v173_real_two_clock_meeting_closes_entire_component
    (E : List V168TwoClockEdge)
    (seed : V168TerminalSeed)
    (rep p i j : Nat)
    (hRepPos : 0<rep) (hPPos : 0<p)
    (hMeeting : iter shortcut i rep = iter shortcut j p)
    (hOwnerSeed : V168Path E p seed.source) :
    ∀ n : Nat, V168Path E n rep → CollatzGood n := by
  let e := v173RealEdge rep p i j hRepPos hPPos hMeeting
  exact v173_one_new_edge_closes_entire_component
    E seed e rep rfl hOwnerSeed

/-- Negative-control guard: if the representative were genuinely
    nonconvergent, no valid real meeting edge could attach it
    to an already certified terminal component.

    A bounded UNKNOWN timeout is NOT this nonconvergence premise. -/
theorem v173_no_false_terminal_reclosure
    (E : List V168TwoClockEdge)
    (seed : V168TerminalSeed)
    (rep p i j : Nat)
    (hRepPos : 0<rep) (hPPos : 0<p)
    (hMeeting : iter shortcut i rep = iter shortcut j p)
    (hOwnerSeed : V168Path E p seed.source)
    (hBad : ¬ CollatzGood rep) : False := by
  have hGood :=
    v173_real_two_clock_meeting_closes_entire_component
      E seed rep p i j hRepPos hPPos hMeeting hOwnerSeed
      rep (V168Path.identity rep)
  exact hBad hGood

#print axioms v173_old_path_in_new_ledger
#print axioms v173_one_new_edge_closes_entire_component
#print axioms v173_real_two_clock_meeting_closes_entire_component
#print axioms v173_no_false_terminal_reclosure

end SourceProduct
end CollatzFinal
