import Collatz.BiadicRankedNormalization

namespace CollatzFinal
namespace SourceProduct

/-- Eventual-progress closeout matching the executable V47 semantics.

For a live zero-tail state we do not need to predict the next protected cell,
and we do not need a live lower-rank witness before an already-certified exit.
It is enough that some later iterate either:
* is no longer Live (so a terminal/descent/lower-merge Exit has occurred), or
* is still ZeroTailLive and has strictly smaller protected quotient rank.

Any post-fixed subset of ZeroTailLive contains every later iterate.  Therefore
the exit branch contradicts membership in Live, while the rank branch is
eliminated by strong induction exactly as in
[zero_tail_kernel_empty_of_eventual_rank]. -/
theorem zero_tail_kernel_empty_of_eventual_progress_or_exit
    {Q : Type}
    (project : State → Q)
    (rank : Q → Nat)
    (hprogress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          (¬ Live (iter step j s)) ∨
          (ZeroTailLive (iter step j s) ∧
            rank (project (iter step j s)) < rank (project s))) :
    KernelEmpty ZeroTailLive Next := by
  intro S hsub hPost
  have aux : ∀ r, ∀ s, rank (project s) = r → ¬ S s := by
    intro r
    induction r using Nat.strongRecOn with
    | ind r ih =>
        intro s hrs hs
        have hzero : ZeroTailLive s := hsub s hs
        obtain ⟨j, hj⟩ := hprogress s hzero
        have hSj : S (iter step j s) :=
          postfixed_iter_mem S hPost j s hs
        have hzeroj : ZeroTailLive (iter step j s) :=
          hsub (iter step j s) hSj
        rcases hj with hjexit | hjdec
        · exact hjexit hzeroj.1
        · have hlt : rank (project (iter step j s)) < r := by
            simpa [hrs] using hjdec.2
          exact ih (rank (project (iter step j s))) hlt
            (iter step j s) rfl hSj
  intro s
  exact aux (rank (project s)) s rfl

/-- One-shot positive-Collatz theorem for the exact V47 progress shape.

The only Collatz-specific premise left here is the eventual macro-progress
witness.  Search/compilers may discover such witnesses, but a global promotion
requires this premise source-independently. -/
theorem collatz_of_zero_tail_eventual_progress_or_exit
    {Q : Type}
    (project : State → Q)
    (rank : Q → Nat)
    (hprogress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          (¬ Live (iter step j s)) ∨
          (ZeroTailLive (iter step j s) ∧
            rank (project (iter step j s)) < rank (project s))) :
    ∀ n, 0 < n → CollatzGood n := by
  exact collatz_of_zero_tail_kernel_empty
    (zero_tail_kernel_empty_of_eventual_progress_or_exit
      project rank hprogress)

#print axioms zero_tail_kernel_empty_of_eventual_progress_or_exit
#print axioms collatz_of_zero_tail_eventual_progress_or_exit

end SourceProduct
end CollatzFinal
