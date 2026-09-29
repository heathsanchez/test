import Collatz.SourceProductZeroTail

namespace CollatzFinal
namespace SourceProduct

/-- The exact SourceProduct tail is just the unrevealed dyadic quotient of the
original source. This makes the finite pre-zero-tail phase explicit. -/
theorem at_tail_eq_source_div_pow
    {n : Nat} (hn : 0 < n) (k : Nat) :
    (stateAt n k).tail = n / 2 ^ k := by
  have h := (common_tail (at_valid hn k)).1
  simpa only [at_source, at_depth] using h.symm

/-- Any depth whose dyadic modulus already exceeds the fixed source is in the
zero-tail regime. -/
theorem at_tail_zero_of_source_lt_pow
    {n k : Nat} (hn : 0 < n) (hlt : n < 2 ^ k) :
    (stateAt n k).tail = 0 := by
  rw [at_tail_eq_source_div_pow hn k]
  exact Nat.div_eq_of_lt hlt

/-- Macro-rank closeout for the exact remaining Collatz kernel.

Unlike [kernel_empty_of_rank], the rank need not decrease on every shortcut
step. It is enough that every live zero-tail state has some later live
zero-tail continuation with strictly smaller quotient rank. A post-fixed
counterexample path contains that later state automatically, so strong
induction on the quotient rank eliminates the whole zero-tail kernel.

This is the formal interface needed by a return-cell / protected-future
certificate: ordinary shortcut steps may move inside one macro cell; only the
next certified macro continuation must decrease rank. -/
theorem zero_tail_kernel_empty_of_eventual_rank
    {Q : Type}
    (project : State → Q)
    (rank : Q → Nat)
    (hprogress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          ZeroTailLive (iter step j s) ∧
          rank (project (iter step j s)) < rank (project s)) :
    KernelEmpty ZeroTailLive Next := by
  intro S hsub hPost
  have aux : ∀ r, ∀ s, rank (project s) = r → ¬ S s := by
    intro r
    induction r using Nat.strongRecOn with
    | ind r ih =>
        intro s hrs hs
        have hzero : ZeroTailLive s := hsub s hs
        obtain ⟨j, hjlive, hdec⟩ := hprogress s hzero
        have hSj : S (iter step j s) :=
          postfixed_iter_mem S hPost j s hs
        have hlt : rank (project (iter step j s)) < r := by
          simpa [hrs] using hdec
        exact ih (rank (project (iter step j s))) hlt
          (iter step j s) rfl hSj
  intro s
  exact aux (rank (project s)) s rfl

/-- One-shot Collatz interface: a protected quotient with an eventually
decreasing macro rank on every ZeroTailLive state closes positive Collatz.
The finite positive-tail prefix requires no additional invariant. -/
theorem collatz_of_zero_tail_eventual_rank
    {Q : Type}
    (project : State → Q)
    (rank : Q → Nat)
    (hprogress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          ZeroTailLive (iter step j s) ∧
          rank (project (iter step j s)) < rank (project s)) :
    ∀ n, 0 < n → CollatzGood n := by
  exact collatz_of_zero_tail_kernel_empty
    (zero_tail_kernel_empty_of_eventual_rank project rank hprogress)

#print axioms at_tail_eq_source_div_pow
#print axioms at_tail_zero_of_source_lt_pow
#print axioms zero_tail_kernel_empty_of_eventual_rank
#print axioms collatz_of_zero_tail_eventual_rank

end SourceProduct
end CollatzFinal
