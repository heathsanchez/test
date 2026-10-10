import Collatz.SparseTwoGiantElimination

namespace CollatzFinal
namespace SourceProduct

/-!
V171 — UNIVERSAL FINITE CLOCK GRAPH EXISTS BY CONSTRUCTION.

This is NOT another representation of arbitrary trajectories: it removes
the separate graph-completeness ASSUMPTION from the V170 conditional
elimination theorem.

At cutoff X and clock H, create one finite, genuine, proof-carrying edge
from each original positive source n<X to every actual endpoint T^t(n)
that is positive, for every clock 0<=t<=H. A finite list of these edges
exists without knowing whether ANY endpoint is eventually terminal.
Every such edge is a valid two-clock future equality (t,0).

A clock-bounded source hitting any positive target b<X therefore has a
certified V168Path to b in the canonical list by construction, not by
assuming an external C++ implementation is complete.

Only the EXTERNAL timed predecessor density and the UNPROVED sparse
second-giant exclusion remain in the canonical conditional finish line.
Global Collatz UNKNOWN — NO QED.
-/

/-- A single real source and real clock, with positivity of the real
endpoint supplied explicitly. This does NOT claim convergence. -/
def v171ActualEndpointEdge
    (n t : Nat)
    (hn : 0 < n) (hp : 0 < iter shortcut t n) :
    V168TwoClockEdge where
  source := n
  other := iter shortcut t n
  sourceClock := t
  otherClock := 0
  sourcePositive := hn
  otherPositive := hp
  sameEndpoint := by simp only [iter]

/-- A list of either one actual edge or no edge, depending only on
DECIDABLE finite source and endpoint positivity. -/
noncomputable def v171StepEdges (n t : Nat) :
    List V168TwoClockEdge := by
  classical
  if hn : 0 < n then
    if hp : 0 < iter shortcut t n then
      exact [v171ActualEndpointEdge n t hn hp]
    else
      exact []
  else
    exact []

/-- Every clock 0..H for ONE original source. -/
noncomputable def v171ClockEdges (n : Nat) : Nat → List V168TwoClockEdge
  | 0 => v171StepEdges n 0
  | H + 1 => v171ClockEdges n H ++ v171StepEdges n (H+1)

/-- Every original source 0..X-1 with every true clock 0..H. -/
noncomputable def v171SourceEdges (H : Nat) : Nat → List V168TwoClockEdge
  | 0 => []
  | X + 1 => v171SourceEdges H X ++ v171ClockEdges X H

/-- A genuine positive clocked endpoint produces exactly its own
proof-carrying canonical source edge. -/
theorem v171_step_edge_member (n t : Nat)
    (hn : 0 < n) (hp : 0 < iter shortcut t n) :
    v171ActualEndpointEdge n t hn hp ∈ v171StepEdges n t := by
  classical
  simp [v171StepEdges, hn, hp]

/-- No finite-clock edge is lost when the clock budget increases. -/
theorem v171_step_member_clock
    (n t H : Nat) (ht : t ≤ H)
    (e : V168TwoClockEdge)
    (he : e ∈ v171StepEdges n t) :
    e ∈ v171ClockEdges n H := by
  induction H with
  | zero =>
      have ht0 : t = 0 := by omega
      subst t
      simpa [v171ClockEdges] using he
  | succ H ih =>
      by_cases hle : t ≤ H
      · simpa [v171ClockEdges] using
          (List.mem_append.mpr (Or.inl (ih hle)))
      · have hEq : t = H+1 := by omega
        subst t
        simpa [v171ClockEdges] using
          (List.mem_append.mpr (Or.inr he))

/-- No original source edge is lost when the height cutoff grows. -/
theorem v171_clock_member_source
    (H n X : Nat) (hnX : n < X)
    (e : V168TwoClockEdge)
    (he : e ∈ v171ClockEdges n H) :
    e ∈ v171SourceEdges H X := by
  induction X with
  | zero => omega
  | succ X ih =>
      by_cases hlt : n < X
      · simpa [v171SourceEdges] using
          (List.mem_append.mpr (Or.inl (ih hlt)))
      · have hEq : n = X := by omega
        subst n
        simpa [v171SourceEdges] using
          (List.mem_append.mpr (Or.inr he))

/-- If a true source n<X reaches positive b by a true clock t<=H,
then the COMPLETE FINITE canonical graph has a checked actual edge
n -> b. This discharges the recording premise from V170. -/
theorem v171_canonical_hit_path
    (H X n b : Nat)
    (hn : 0 < n) (hnX : n < X)
    (hb : 0 < b)
    (hHit : V169HitWithin n b H) :
    V168Path (v171SourceEdges H X) n b := by
  obtain ⟨t, ht, hEq⟩ := hHit
  have hp : 0 < iter shortcut t n := by
    rw [hEq]
    exact hb
  let e : V168TwoClockEdge := v171ActualEndpointEdge n t hn hp
  have hStep : e ∈ v171StepEdges n t :=
    v171_step_edge_member n t hn hp
  have hClock : e ∈ v171ClockEdges n H :=
    v171_step_member_clock n t H ht e hStep
  have hSource : e ∈ v171SourceEdges H X :=
    v171_clock_member_source H n X hnX e hClock
  have hPath : V168Path (v171SourceEdges H X) e.source e.other :=
    V168Path.observed e hSource
  simpa only [e, v171ActualEndpointEdge, hEq] using hPath

/-- A complete finite source/clock ledger exists for EVERY height
and EVERY finite clock schedule. Nothing about Collatz convergence
is needed to construct or check its individual edges. -/
noncomputable def v171CanonicalClockGraph
    (H : Nat → Nat) (k : Nat) : List V168TwoClockEdge :=
  v171SourceEdges (H k) (2^k)

theorem v171_canonical_ledger_complete
    (H : Nat → Nat) :
    V170CompleteLedger (v171CanonicalClockGraph H) H := by
  intro k b hb hbX n hn hnX hHit
  exact v171_canonical_hit_path (H k) (2^k) n b
    hn hnX hb hHit

/-- ONE LESS INDEPENDENT PREMISE than V170:
the graph is now canonical and COMPLETENESS PROVED, not assumed.
What remains genuinely UNKNOWN is an arithmetic sparse exclusion of
two macroscopic finite-clock components (plus external timed density). -/
theorem v171_collatz_of_ordinary_timed_density_and_canonical_no_two_giants
    (H : Nat → Nat)
    (hDensity : V169TimedTargetDensity H)
    (hNoTwoGiants :
      V170SparseNoTwoGiants (v171CanonicalClockGraph H)) :
    ∀ n : Nat, 0 < n → CollatzGood n := by
  exact v170_collatz_of_ordinary_timed_density_and_sparse_unique_giant
    H (v171CanonicalClockGraph H)
    hDensity
    (v171_canonical_ledger_complete H)
    hNoTwoGiants

#print axioms v171_step_edge_member
#print axioms v171_step_member_clock
#print axioms v171_clock_member_source
#print axioms v171_canonical_hit_path
#print axioms v171_canonical_ledger_complete
#print axioms v171_collatz_of_ordinary_timed_density_and_canonical_no_two_giants

end SourceProduct
end CollatzFinal
