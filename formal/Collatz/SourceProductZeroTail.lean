import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/-- The unresolved part after the finite original-source tail is consumed. -/
def ZeroTailLive (s : State) : Prop := Live s ∧ s.tail = 0

theorem zero_tail_source_residue {s : State} (hs : Valid s) (hz : s.tail = 0) :
    s.sourceResidue = s.source := by
  have h := hs.2.2.2
  simpa only [hz, Nat.mul_zero, Nat.add_zero] using h.symm

theorem zero_tail_endpoint_residue_step (s : State) (hz : s.tail = 0) :
    (step s).endpointResidue = shortcut s.endpointResidue := by
  simp [step, hz]

/-- No infinite post-fixed obstruction is confined to the positive-tail region.
    Its zero-tail subkernel must already be nonempty. -/
theorem kernel_empty_of_zero_tail
    (hempty : KernelEmpty ZeroTailLive Next) : KernelEmpty Live Next := by
  intro S hLive hPost s hs
  have hZero : ∀ t, ¬ (S t ∧ t.tail = 0) := by
    apply hempty (fun t => S t ∧ t.tail = 0)
    · intro t ht
      exact ⟨hLive t ht.1, ht.2⟩
    · intro t ht
      obtain ⟨u, hu, hSu⟩ := hPost t ht.1
      refine ⟨u, hu, hSu, ?_⟩
      change u = step t at hu
      rw [hu]
      exact tail_zero_persists t ht.2
  have hDrop : ∀ t u, S t → Next t u → u.tail < t.tail := by
    intro t u ht hu
    have hn : t.tail ≠ 0 := fun hz => hZero t ⟨ht, hz⟩
    have hp : 0 < t.tail := by omega
    change u = step t at hu
    rw [hu]
    exact tail_strict_until_zero t hp
  have hRank := kernel_empty_of_rank S Next (fun t => t.tail) hDrop
  exact hRank S (fun _ ht => ht) hPost s hs

theorem endpoint_iter_step (j : Nat) (s : State) :
    endpoint (iter step j s) = iter shortcut j (endpoint s) := by
  induction j generalizing s with
  | zero => rfl
  | succ j ih =>
      simpa [iter, step_endpoint] using ih (step s)

theorem postfixed_iter_mem
    (S : State → Prop)
    (hPost : PostFixed Next S) :
    ∀ j s, S s → S (iter step j s) := by
  intro j
  induction j with
  | zero =>
      intro s hs
      simpa [iter] using hs
  | succ j ih =>
      intro s hs
      obtain ⟨t, ht, hSt⟩ := hPost s hs
      change t = step s at ht
      simpa [iter, ← ht] using ih t hSt

/-- If positive Collatz termination is assumed, no zero-tail live post-fixed
    kernel can exist. This is the converse of the conditional closure below. -/
theorem zero_tail_kernel_empty_of_collatz
    (hgood : ∀ n, 0 < n → CollatzGood n) :
    KernelEmpty ZeroTailLive Next := by
  intro S hsub hPost s hs
  have hLive : Live s := (hsub s hs).1
  obtain ⟨n, k, hn, hstate⟩ := hLive.1
  have hnGood : CollatzGood n := hgood n hn
  have hEndpointGood : CollatzGood (endpoint s) := by
    have hkGood : CollatzGood (iter shortcut k n) :=
      eventually_iter_forward shortcut Terminal terminal_forward_invariant hnGood k
    simpa [hstate, at_endpoint] using hkGood
  obtain ⟨j, hj⟩ := hEndpointGood
  have hSj : S (iter step j s) := postfixed_iter_mem S hPost j s hs
  have hLivej : Live (iter step j s) := (hsub _ hSj).1
  apply hLivej.2
  left
  simpa [endpoint_iter_step] using hj

/-- Conditional closure: zero-tail kernel emptiness remains an explicit premise. -/
theorem collatz_of_zero_tail_kernel_empty
    (hempty : KernelEmpty ZeroTailLive Next) :
    ∀ n, 0 < n → CollatzGood n := by
  exact collatz_of_product_kernel_empty (kernel_empty_of_zero_tail hempty)

/-- Exact boundary: the remaining zero-tail kernel problem is equivalent to the
    original positive Collatz termination statement. The normalization has not
    by itself supplied the missing termination invariant. -/
theorem zero_tail_kernel_empty_iff_collatz :
    KernelEmpty ZeroTailLive Next ↔
      (∀ n, 0 < n → CollatzGood n) := by
  constructor
  · exact collatz_of_zero_tail_kernel_empty
  · exact zero_tail_kernel_empty_of_collatz

#print axioms zero_tail_source_residue
#print axioms zero_tail_endpoint_residue_step
#print axioms kernel_empty_of_zero_tail
#print axioms collatz_of_zero_tail_kernel_empty
#print axioms zero_tail_kernel_empty_iff_collatz

end SourceProduct
end CollatzFinal
