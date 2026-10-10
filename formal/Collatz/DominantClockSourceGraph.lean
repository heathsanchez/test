import Collatz.IdealFiniteClockGraphElimination

namespace CollatzFinal
namespace SourceProduct

/-!
V172 — SOURCE-CLOCK ENDPOINT DOMINANCE.

At a genuine endpoint y, if source p arrived at clock j and
source n arrived at clock i>=j, then p has AT LEAST as much of
the fixed finite clock budget remaining as n. The two real
original sources already share y, and every later endpoint of
n within its remaining budget is reached by p within budget.

Thus a complete finite source-clock coalescence quotient need
only continue the earliest-clock endpoint owner. It may skip
a later arrival WITHOUT throwing away any future component
connection: the connection is inherited by p and then by n.

This proves the LOCAL DOMINANCE RULE, not yet the entire C++
hash/union implementation. Independent exhaustive crosschecks
compare that implementation to the full canonical graph at
smaller source cutoffs and each synthetic negative control.

Neither the rule nor finite full-graph saturation establishes
the ALL-SCALE no-macroscopic-unseeded-component theorem.
The source-dependent horizon H(k)=8k remains independently
specified and effective. GLOBAL COLLATZ UNKNOWN.
-/

/-- Dominance is valid for ANY deterministic Nat map with true
    meeting clocks; the actual Collatz specialization follows.
    The clock inequality j<=i is the source of pruning gain. -/
theorem v172_dominated_endpoint_future
    (f : Nat → Nat)
    (n p i j t H : Nat)
    (hMeet : iter f i n = iter f j p)
    (hClock : j<=i)
    (hBudget : i+t<=H) :
    iter f (i+t) n = iter f (j+t) p ∧ j+t<=H := by
  constructor
  · calc
      iter f (i+t) n = iter f t (iter f i n) :=
        iter_add f i t n
      _ = iter f t (iter f j p) := by rw [hMeet]
      _ = iter f (j+t) p := (iter_add f j t p).symm
  · omega

/-- Any endpoint-state collision within the dominated source's
    remaining clock budget has a matching collision from the
    earlier-arriving owner p before H. This is exact, not a
    statistical statement. -/
theorem v172_earliest_clock_owner_captures_later_collision
    (X H n p r i j t u : Nat)
    (hn : 0<n) (hp : 0<p) (hr : 0<r)
    (hnX : n<X) (hpX : p<X) (hrX : r<X)
    (hMeet : iter shortcut i n = iter shortcut j p)
    (hEarlier : j<=i)
    (hBudget : i+t<=H)
    (hOther : iter shortcut (i+t) n =
      iter shortcut u r)
    (hOtherBudget : u<=H) :
    V170FullClockPath X H p r := by
  obtain ⟨hSame,hJClock⟩ :=
    v172_dominated_endpoint_future
      shortcut n p i j t H hMeet hEarlier hBudget
  refine V170FullClockPath.meeting
    (i:=j+t) (j:=u)
    hp hr hpX hrX hJClock hOtherBudget ?_
  exact hSame.symm.trans hOther

/-- The skipped original source n also retains the same
    connection to r, by composing its already-observed
    n->p meeting with the earlier-owner p->r future.
    No source/clock identity is lost. -/
theorem v172_skipped_suffix_keeps_full_class_connection
    (X H n p r i j t u : Nat)
    (hn : 0<n) (hp : 0<p) (hr : 0<r)
    (hnX : n<X) (hpX : p<X) (hrX : r<X)
    (hMeet : iter shortcut i n = iter shortcut j p)
    (hEarlier : j<=i)
    (hBudget : i+t<=H)
    (hOther : iter shortcut (i+t) n =
      iter shortcut u r)
    (hOtherBudget : u<=H) :
    V170FullClockPath X H n r := by
  have hi : i<=H := by omega
  have hj : j<=H := by omega
  have hnp : V170FullClockPath X H n p :=
    V170FullClockPath.meeting
      (i:=i) (j:=j)
      hn hp hnX hpX hi hj hMeet
  have hpr :=
    v172_earliest_clock_owner_captures_later_collision
      X H n p r i j t u hn hp hr
      hnX hpX hrX
      hMeet hEarlier hBudget hOther hOtherBudget
  exact V170FullClockPath.compose hnp hpr

/-- Even when the true terminal hit is found after the
    dominated meeting endpoint, the earlier-clock owner
    has a certified terminal hit under its own clock budget.
    The original source n has one too. -/
theorem v172_dominant_owner_inherits_terminal
    (n p i j t H : Nat)
    (hMeet : iter shortcut i n = iter shortcut j p)
    (hEarlier : j<=i)
    (hBudget : i+t<=H)
    (hTerminal : Terminal (iter shortcut (i+t) n)) :
    (∃ l, l<=H ∧ Terminal (iter shortcut l p)) ∧
    (∃ l, l<=H ∧ Terminal (iter shortcut l n)) := by
  obtain ⟨hFuture,hJClock⟩ :=
    v172_dominated_endpoint_future
      shortcut n p i j t H hMeet hEarlier hBudget
  constructor
  · exact ⟨j+t,hJClock,by simpa [hFuture] using hTerminal⟩
  · exact ⟨i+t,hBudget,hTerminal⟩

#print axioms v172_dominated_endpoint_future
#print axioms v172_earliest_clock_owner_captures_later_collision
#print axioms v172_skipped_suffix_keeps_full_class_connection
#print axioms v172_dominant_owner_inherits_terminal

end SourceProduct
end CollatzFinal
