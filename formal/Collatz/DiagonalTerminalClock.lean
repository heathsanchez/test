import Collatz.SparseExceptionalMassClosure

namespace CollatzFinal
namespace SourceProduct

/-!
V153 — SOURCE-ATTACHED DIAGONAL TERMINAL CLOCK.

The finite predicate below has a very narrow semantics: it asks whether
the ACTUAL shortcut orbit reaches the *real* terminal {1,2} by clock c*k.

It removes all abstract exceptional-predicate choice from V151's
interface: the population being counted is an executable first-hitting
time tail, at scale 2^k and budget c*k. Every admitted convergence fact
has its own explicit (and replayable) terminal clock.

This formal reduction is conditional, NOT a Collatz solution. Its one
remaining asymptotic hypothesis is the density-zero property of that
particular numerical stopping-time tail. Finite measurements cannot
establish it. The external predecessor-amplifier is still explicit.
-/

/-- Positive examples have genuine finite terminal clocks <= c*k. -/
def V153WithinTerminal (c k n : Nat) : Prop :=
  ∃ t : Nat, t ≤ c*k ∧ Terminal (iter shortcut t n)

/-- A real eventual terminal hit is sufficient for V150's *stricter*
    proof-carrying terminal/lower-merger grammar. When n>2 the merge
    uses p=1 or p=2, a strictly earlier source already terminal. -/
theorem v153_terminal_hit_is_closed
    (n t : Nat) (hn : 0<n)
    (hh : Terminal (iter shortcut t n)) :
    V150Closed n := by
  by_cases hinit : Terminal n
  · exact V150Closed.terminal hinit
  · have hgt : 2 < n := by
      unfold Terminal at hinit
      omega
    rcases hh with h1 | h2
    · have hm : LowerMerge shortcut n 1 := by
        refine ⟨by omega, t, 0, ?_⟩
        simpa [iter] using h1
      exact V150Closed.merger hm
        (V150Closed.terminal (Or.inl rfl))
    · have hm : LowerMerge shortcut n 2 := by
        refine ⟨by omega, t, 0, ?_⟩
        simpa [iter] using h2
      exact V150Closed.merger hm
        (V150Closed.terminal (Or.inr rfl))

/-- A canonical scale-indexed exceptional predicate, decidable for
    every concrete triple (c,k,n); all excluded positives carry
    a real V150Closed witness, not merely strict descent. -/
def V153Uncertified (c k n : Nat) : Prop :=
  ¬ V153WithinTerminal c k n

theorem v153_diagonal_terminal_coverage
    (c : Nat) :
    ∀ k n : Nat, 0<n → n<2^k →
      ¬ V153Uncertified c k n → V150Closed n := by
  intro k n hn _ hncert
  have hh : V153WithinTerminal c k n := by
    exact Classical.byContradiction hncert
  obtain ⟨t,_,ht⟩ := hh
  exact v153_terminal_hit_is_closed n t hn ht

/-- The ONLY new asymptotic obligation, with no arbitrary E:
    along unbounded dyadic scales, the exact number of starts
    not yet terminal by c*k has vanishing relative upper density. -/
def V153SparseTerminalClock (c : Nat) : Prop :=
  V151SparseCertifiedEnvelope (fun k n => V153Uncertified c k n)

/-- If a single linear-in-bitlength terminal clock has sparse
    timeout mass, the full V151 bridge closes Collatz, still
    conditional on the externally supplied predecessor amplifier. -/
theorem v153_collatz_of_sparse_diagonal_terminal_clock
    (c : Nat)
    (hAmp : V150PredecessorAmplifier)
    (hSparse : V153SparseTerminalClock c) :
    ∀ n : Nat, 0<n → CollatzGood n := by
  exact v151_collatz_of_sparse_proof_carrying_exceptional_mass
    hAmp (fun k n => V153Uncertified c k n)
    (v153_diagonal_terminal_coverage c) hSparse

/-- Exact falsifier for the proposed sparse clock: under the
    *explicit* external amplifier, any genuine least positive bad
    source would force a fixed positive lower density of actual
    first-hitting-time tail starts at ALL sufficiently large scales.
    This is a necessary obstruction, not evidence of a bad source. -/
theorem v153_minimal_bad_forces_diagonal_timeout_density
    (c : Nat) (hAmp : V150PredecessorAmplifier)
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    ∃ q X0 : Nat, 0<q ∧
      ∀ k : Nat, X0≤2^k →
        2^k ≤ q*v150EnvelopeCount
          (fun k n => V153Uncertified c k n) k := by
  obtain ⟨q,X0,hq,hLower⟩ :=
    v150_amplify_actual_minimal_bad hAmp hmin
  refine ⟨q,X0,hq,?_⟩
  intro k hk
  have hbound :=
    v150_proof_carrying_envelope_bounds_true_bad_count
      (fun k n => V153Uncertified c k n)
      (v153_diagonal_terminal_coverage c) k
  exact Nat.le_trans (hLower (2^k) hk)
    (Nat.mul_le_mul_left q hbound)

#print axioms v153_terminal_hit_is_closed
#print axioms v153_diagonal_terminal_coverage
#print axioms v153_collatz_of_sparse_diagonal_terminal_clock
#print axioms v153_minimal_bad_forces_diagonal_timeout_density

end SourceProduct
end CollatzFinal
