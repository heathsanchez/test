import Collatz.GuardedExitObligation
import Collatz.SourceProductZeroTail

namespace CollatzFinal.SourceProduct

/-- The exact operational waist for the protected Collatz future.
The original source is retained because OrdinaryExit is source-relative;
the current endpoint is retained because actual continuation is deterministic. -/
abbrev ProtectedState := Nat × Nat

def protectedStep (q : ProtectedState) : ProtectedState :=
  (q.1, shortcut q.2)

def protectedObservation (q : ProtectedState) : Prop :=
  OrdinaryExit q.1 q.2

/-- The full SourceProduct state projects exactly through one protected step. -/
theorem protected_step_projection (s : State) :
    protectedStep (projection s) = projection (step s) := by
  change (s.source, shortcut (endpoint s)) = projection (step s)
  exact (projection_step s).symm

/-- The original source is invariant under every number of exact state steps. -/
theorem iter_step_source (j : Nat) (s : State) :
    (iter step j s).source = s.source := by
  induction j generalizing s with
  | zero => rfl
  | succ j ih =>
      simpa [iter, step] using ih (step s)

/-- The whole SourceProduct trajectory factors through (source,current endpoint). -/
theorem projection_iter_step (j : Nat) (s : State) :
    projection (iter step j s) =
      (s.source, iter shortcut j (endpoint s)) := by
  change ((iter step j s).source, endpoint (iter step j s)) =
    (s.source, iter shortcut j (endpoint s))
  rw [iter_step_source, endpoint_iter_step]

/-- Every authorized future OrdinaryExit observation factors through the pair
(source,current endpoint). Depth, odds, tail and residue fields are therefore
not protected semantic distinctions for this observation family. -/
theorem protected_future_factors (j : Nat) (s : State) :
    OrdinaryExit (iter step j s).source (endpoint (iter step j s)) ↔
      OrdinaryExit s.source (iter shortcut j (endpoint s)) := by
  rw [iter_step_source, endpoint_iter_step]

/-- Consequently, two full states with the same protected projection have the
same OrdinaryExit observation after every lawful future continuation. -/
theorem same_projection_same_protected_futures
    {s t : State} (h : projection s = projection t) :
    ∀ j,
      OrdinaryExit (iter step j s).source (endpoint (iter step j s)) ↔
      OrdinaryExit (iter step j t).source (endpoint (iter step j t)) := by
  have hs : s.source = t.source := congrArg Prod.fst h
  have he : endpoint s = endpoint t := congrArg Prod.snd h
  intro j
  rw [iter_step_source, iter_step_source, endpoint_iter_step, endpoint_iter_step,
    hs, he]

/-- The source coordinate cannot be erased: the same endpoint can have a
different protected observation under a different original source. -/
theorem source_coordinate_separator :
    protectedObservation (4, 3) ∧ ¬ protectedObservation (1, 3) := by
  simpa [protectedObservation] using immediate_exit_guard_needs_origin

/-- The current-endpoint coordinate cannot be erased from the observation
interface either: with the source fixed, two currents are separated already at
the zero-step observation. This is coordinate necessity for this interface,
not a claim of global quotient minimality. -/
theorem current_coordinate_separator :
    protectedObservation (1, 1) ∧ ¬ protectedObservation (1, 3) := by
  constructor
  · exact Or.inl (Or.inl rfl)
  · intro h
    rcases h with ht | hd | hm
    · rcases ht with h1 | h2 <;> omega
    · omega
    · rcases hm with ⟨p, b, hp, hlt, _⟩
      omega

/-- The protected existential objective is exactly the already-qualified
source-indexed ExitObligation on this operational waist. -/
theorem protected_objective_is_exit_obligation (source current : Nat) :
    ExitObligation source current =
      Eventually shortcut (OrdinaryExit source) current := by
  rfl

#print axioms protected_step_projection
#print axioms iter_step_source
#print axioms projection_iter_step
#print axioms protected_future_factors
#print axioms same_projection_same_protected_futures
#print axioms source_coordinate_separator
#print axioms current_coordinate_separator
#print axioms protected_objective_is_exit_obligation

end CollatzFinal.SourceProduct
