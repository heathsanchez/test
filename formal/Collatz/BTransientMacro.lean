import Collatz.TwelveOddBlockContraction

namespace CollatzFinal
namespace SourceProduct

/-- Endpoint transport commutes with an arbitrary finite SourceProduct step
block.  This lets local shortcut-block certificates lift directly to the
stateful zero-tail kernel. -/
theorem iter_step_endpoint (k : Nat) (s : State) :
    endpoint (iter step k s) = iter shortcut k (endpoint s) := by
  induction k generalizing s with
  | zero =>
      rfl
  | succ k ih =>
      simp only [iter]
      rw [ih, step_endpoint]

/-- A sparse twelve-odd macro is one block containing exactly twelve odd
shortcut steps and taking at least twenty ordinary shortcut steps.  These are
exactly the local blocks whose cost profile lies on the V30/V37 B side. -/
def SparseTwelveNext (s t : State) : Prop :=
  ∃ k,
    20 ≤ k ∧
    oddCount (endpoint s) k = 12 ∧
    t = iter step k s

/-- Above the exact V30 floor, endpoint value itself is a well-founded rank for
the sparse/B macro relation. -/
def SparseTwelveLive (s : State) : Prop :=
  262 ≤ endpoint s

theorem sparse_twelve_next_strict_endpoint_descent
    {s t : State}
    (hs : SparseTwelveLive s)
    (hst : SparseTwelveNext s t) :
    endpoint t < endpoint s := by
  rcases hst with ⟨k, hk, hq, rfl⟩
  rw [iter_step_endpoint]
  exact twelve_odd_long_block_strict_descent hs hk hq

/-- The B/sparse macro phase cannot itself carry an infinite post-fixed
residual kernel: every such macro strictly lowers the natural endpoint rank.

This is the exact formal reason the 15,762 unrepresented V37 B presentations
do not need to be added as recurrent chamber states merely to obtain a
well-founded proof architecture.  A complete Collatz closeout still needs a
normalization theorem showing that every live B phase either exits or reaches
a later protected non-B macro state. -/
theorem sparse_twelve_kernel_empty :
    KernelEmpty SparseTwelveLive SparseTwelveNext := by
  exact kernel_empty_of_rank
    SparseTwelveLive SparseTwelveNext endpoint
    (by
      intro s t hs hst
      exact sparse_twelve_next_strict_endpoint_descent hs hst)

#print axioms iter_step_endpoint
#print axioms sparse_twelve_next_strict_endpoint_descent
#print axioms sparse_twelve_kernel_empty

end SourceProduct
end CollatzFinal
