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
