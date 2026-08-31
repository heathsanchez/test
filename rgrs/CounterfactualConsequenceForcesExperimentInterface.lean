import «rgrs/PassiveEvidenceCannotDetermineCausalRole»

namespace CounterfactualConsequenceForcesExperimentInterface

open PassiveEvidenceCannotDetermineCausalRole

/-- Two opaque verifier worlds. -/
inductive World where
  | A
  | B
  deriving DecidableEq

/-- Both worlds are observationally identical at the passive interface. -/
def passiveRep : World → PassiveView
  | .A => passiveA
  | .B => passiveB

/-- The required causal continuation differs between the two worlds. -/
def requiredRole : World → PairRole
  | .A => .p0
  | .B => .p1

/-- The active experiment consequence records only the verifier responses to the
    same two anonymous deletion interventions. -/
def experimentConsequence : World → Bool × Bool
  | .A => deletionSignature verifierA
  | .B => deletionSignature verifierB

/-- Factorization through a representation: every target consequence is a
    function only of the information retained by that representation. -/
def FactorsThrough {X R Y : Type} (q : X → R) (c : X → Y) : Prop :=
  ∃ h : R → Y, c = h ∘ q

/-- Passive observation identifies the two worlds. -/
theorem passive_representation_collapses_worlds :
    passiveRep .A = passiveRep .B := by
  exact passive_views_are_equal

/-- The required causal role separates them. -/
theorem required_roles_differ : requiredRole .A ≠ requiredRole .B := by
  decide

/-- Therefore causal target selection cannot factor through the passive
    representation. -/
theorem causal_role_does_not_factor_through_passive :
    ¬ FactorsThrough passiveRep requiredRole := by
  rintro ⟨h, hh⟩
  have hA : requiredRole .A = h (passiveRep .A) := by
    simpa [Function.comp_apply] using congrFun hh .A
  have hB : requiredRole .B = h (passiveRep .B) := by
    simpa [Function.comp_apply] using congrFun hh .B
  have hp : h (passiveRep .A) = h (passiveRep .B) := by
    rw [passive_representation_collapses_worlds]
  exact required_roles_differ (hA.trans (hp.trans hB.symm))

/-- The counterfactual experiment consequence distinguishes the worlds. -/
theorem experiment_consequence_separates_worlds :
    experimentConsequence .A ≠ experimentConsequence .B := by
  exact active_intervention_separates_worlds

/-- Canonical least consequential refinement: retain the passive code and add
    exactly the newly justified counterfactual consequence. -/
def refinedRep (w : World) : PassiveView × (Bool × Bool) :=
  (passiveRep w, experimentConsequence w)

/-- Every old passive observation survives by projection. -/
theorem passive_factors_through_refinement :
    FactorsThrough refinedRep passiveRep := by
  exact ⟨Prod.fst, rfl⟩

/-- The new experiment consequence survives by projection. -/
theorem experiment_factors_through_refinement :
    FactorsThrough refinedRep experimentConsequence := by
  exact ⟨Prod.snd, rfl⟩

/-- The required causal role is decoded solely from the new counterfactual
    component. -/
def roleDecoder : PassiveView × (Bool × Bool) → PairRole
  | (_, (false, true)) => .p0
  | (_, (true, false)) => .p1
  | _ => .p0

theorem causal_role_factors_through_refinement :
    FactorsThrough refinedRep requiredRole := by
  refine ⟨roleDecoder, ?_⟩
  funext w
  cases w <;> rfl

/-- Universal property of the product repair: any alternative representation
    that already realizes both the old passive interface and the new experiment
    consequence canonically maps to this refinement. -/
theorem refinement_is_least_common_completion
    {R : Type} (q : World → R)
    (hold : FactorsThrough q passiveRep)
    (hexp : FactorsThrough q experimentConsequence) :
    FactorsThrough q refinedRep := by
  rcases hold with ⟨hp, hpEq⟩
  rcases hexp with ⟨he, heEq⟩
  refine ⟨fun r => (hp r, he r), ?_⟩
  funext w
  simp only [refinedRep, Function.comp_apply]
  have h1 := congrFun hpEq w
  have h2 := congrFun heEq w
  exact Prod.ext h1 h2

/-- Exact ablation: remove the counterfactual component and causal selection
    becomes impossible again. -/
theorem counterfactual_ablation_restores_obstruction :
    ¬ FactorsThrough passiveRep requiredRole :=
  causal_role_does_not_factor_through_passive

/-- End-to-end MSI theorem for active experimentation.

    In this exact finite witness, the old passive interface collapses two worlds
    that require opposite causal repairs.  The verifier-generated deletion
    consequence separates those worlds.  Pairing that consequence with the old
    interface is a least common completion, makes the causal target factorable,
    and loses that capability under exact counterfactual ablation.

    Thus the experiment response is not merely useful extra data here: it is a
    consequential distinction that the old interface provably cannot omit while
    remaining sufficient for causal continuation. -/
theorem counterfactual_consequence_forces_minimal_experiment_interface :
    passiveRep .A = passiveRep .B ∧
    requiredRole .A ≠ requiredRole .B ∧
    (¬ FactorsThrough passiveRep requiredRole) ∧
    experimentConsequence .A ≠ experimentConsequence .B ∧
    FactorsThrough refinedRep passiveRep ∧
    FactorsThrough refinedRep experimentConsequence ∧
    FactorsThrough refinedRep requiredRole ∧
    (∀ {R : Type} (q : World → R),
      FactorsThrough q passiveRep →
      FactorsThrough q experimentConsequence →
      FactorsThrough q refinedRep) := by
  exact ⟨passive_representation_collapses_worlds,
    required_roles_differ,
    causal_role_does_not_factor_through_passive,
    experiment_consequence_separates_worlds,
    passive_factors_through_refinement,
    experiment_factors_through_refinement,
    causal_role_factors_through_refinement,
    fun q hp he => refinement_is_least_common_completion q hp he⟩

#check causal_role_does_not_factor_through_passive
#check experiment_consequence_separates_worlds
#check passive_factors_through_refinement
#check experiment_factors_through_refinement
#check causal_role_factors_through_refinement
#check refinement_is_least_common_completion
#check counterfactual_ablation_restores_obstruction
#check counterfactual_consequence_forces_minimal_experiment_interface

end CounterfactualConsequenceForcesExperimentInterface
