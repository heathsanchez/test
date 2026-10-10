import Collatz.NonvacuousExitRankClosure

namespace CollatzFinal
namespace SourceProduct

/-!
V157 — AUDIT OF V156 PROGRESS: THE UNIVERSAL EXIT-OR-RANK
PREMISE IS LOGICALLY EQUIVALENT TO FULL COLLATZ FOR
EVERY PROJECTED NAT-VALUED RANK PAIR.

This file does NOT close the conjecture. It prevents the verified
V156 conditional closeout from being misread as an independently
obtained universal theorem.

If Collatz holds, a source-attached live state s has a real
terminal future under the actual shortcut, so its first
disjunct (Exit) eventually holds independently of rank.
V156 already shows conversely that the disjunction for ALL
live zero-tail states implies the conjecture.

Hence no rank choice can make the quantifier easier *just by
restating this contract*. A new proof needs an independently
verified property of the specific odd arithmetic of the map.
-/

/-- If every positive original source converges, every reachable
    Live state has a real future exit. This uses only actual
    source/clock lineage, not an assumed affine quotient or
    a compressed future-class decision. -/
theorem v157_collatz_implies_live_eventual_exit
    (hGood : ∀ n : Nat, 0<n → CollatzGood n)
    (s : State) (hLive : Live s) :
    ∃ j : Nat, Exit (iter step j s) := by
  obtain ⟨n,k,hn,hs⟩ := hLive.1
  have hg : CollatzGood n := hGood n hn
  have hfuture : CollatzGood (iter shortcut k n) :=
    eventually_iter_forward shortcut Terminal
      terminal_forward_invariant hg k
  have hend : CollatzGood (endpoint s) := by
    simpa [hs, at_endpoint] using hfuture
  obtain ⟨j,hTerm⟩ := hend
  refine ⟨j, Or.inl ?_⟩
  simpa [endpoint_iter_step] using hTerm

/-- The corrected V156 contract, named as a proposition in order
    to audit its exact logical strength for any given rank choice. -/
def V157ExitOrRankProgress
    {Q : Type} (project : State → Q)
    (major minor : Q → Nat) : Prop :=
  ∀ s, ZeroTailLive s →
    ∃ j,
      Exit (iter step j s) ∨
      (ZeroTailLive (iter step j s) ∧
        (major (project (iter step j s)) < major (project s) ∨
         (major (project (iter step j s)) = major (project s) ∧
          minor (project (iter step j s)) < minor (project s))))

/-- For ANY rank pair and projection, the V156 universal
    exit-or-rank premise is EQUIVALENT to full positive Collatz.
    The conditional implication is sound, but it is not an
    independently supplied solution. -/
theorem v157_exit_or_rank_iff_collatz
    {Q : Type} (project : State → Q)
    (major minor : Q → Nat) :
    V157ExitOrRankProgress project major minor ↔
      (∀ n : Nat, 0<n → CollatzGood n) := by
  constructor
  · intro hProgress
    exact v156_collatz_of_exit_or_lex_rank
      project major minor hProgress
  · intro hGood
    intro s hs
    obtain ⟨j,hExit⟩ :=
      v157_collatz_implies_live_eventual_exit hGood s hs.1
    exact ⟨j,Or.inl hExit⟩

/-- Even stripping all ranks from V156 and demanding eventual
    genuine exit still leaves exactly the Collatz conjecture.
    This is an audit of proof power, not a candidate proof. -/
def V157EventuallyExitAllZeroTailLive : Prop :=
  ∀ s : State, ZeroTailLive s →
    ∃ j, Exit (iter step j s)

theorem v157_exit_only_iff_collatz :
    V157EventuallyExitAllZeroTailLive ↔
      (∀ n : Nat, 0<n → CollatzGood n) := by
  constructor
  · intro hExit
    apply v156_collatz_of_exit_or_lex_rank
      (project := fun _ : State => ())
      (major := fun _ : Unit => 0)
      (minor := fun _ : Unit => 0)
    intro s hs
    obtain ⟨j,hj⟩ := hExit s hs
    exact ⟨j,Or.inl hj⟩
  · intro hGood s hs
    exact v157_collatz_implies_live_eventual_exit hGood s hs.1

/-- The full original zero-tail kernel emptiness, V156 corrected
    ranked progress, and plain terminal/merge exit are one and the
    same unproved proposition, regardless of rank. -/
theorem v157_three_way_exact_frontier
    {Q : Type} (project : State → Q)
    (major minor : Q → Nat) :
    (KernelEmpty ZeroTailLive Next ↔
      V157ExitOrRankProgress project major minor) ∧
    (KernelEmpty ZeroTailLive Next ↔
      V157EventuallyExitAllZeroTailLive) := by
  constructor
  · exact zero_tail_kernel_empty_iff_collatz.trans
      (v157_exit_or_rank_iff_collatz project major minor).symm
  · exact zero_tail_kernel_empty_iff_collatz.trans
      v157_exit_only_iff_collatz.symm

#print axioms v157_collatz_implies_live_eventual_exit
#print axioms v157_exit_or_rank_iff_collatz
#print axioms v157_exit_only_iff_collatz
#print axioms v157_three_way_exact_frontier

end SourceProduct
end CollatzFinal
