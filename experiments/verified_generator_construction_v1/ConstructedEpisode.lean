import TypedResidualKernel

namespace VerifiedGeneratorConstruction
open TypedResidualKernel

def oldLanguage : List Nat := [0, 3, 5, 10, 12, 15]
def extendedLanguage : List Nat := List.range 16
def target : Nat := 8
def reuseTarget : Nat := 4
def sourceState : Nat := 1
def nextState : Nat := 2

theorem old_complete_negative : ¬ ∃ σ, σ ∈ oldLanguage ∧ σ = target := by decide
theorem constructed_resolves : target ∈ extendedLanguage := by decide
theorem frozen_reuse : reuseTarget ∉ oldLanguage ∧ reuseTarget ∈ extendedLanguage := by decide
theorem ablation_restores : target ∉ oldLanguage ∧ reuseTarget ∉ oldLanguage := by decide

def K : Kernel where
  State := Nat; Language := List Nat; Authority := Unit; Policy := Unit
  Residual := Nat; Candidate := Nat; Future := Nat; Fact := Nat
  selectionObligation := fun _ _ _ _ _ => True
  uniqueIfRequired := fun _ _ => True
  identityResidual := fun _ _ _ _ => True
  choiceResidual := fun _ _ _ _ _ => True
  searchIncomplete := fun Ω _ _ => Ω = 1
  complete := fun Ω M _ => Ω = 1 ∧ M = oldLanguage
  inLanguage := fun M σ => σ ∈ M
  resolves := fun σ ρ => σ = ρ
  isProtected := fun _ f => f ∈ oldLanguage

def searchResult : Result K sourceState oldLanguage () () target := Result.unknownSearch rfl
def expressiveResult : Result K sourceState oldLanguage () () target :=
  Result.unknownExpressivity ⟨rfl, rfl⟩ old_complete_negative
def constructionStep : Step K expressiveResult nextState := Step.proposeGenerator (fun _ h => h)

theorem only_expressivity_licenses_construction :
    constructionStep.kind = TransitionKind.proposeGenerator := by rfl
theorem proof_carrying_preservation :
    ∀ f, K.isProtected sourceState f → K.isProtected nextState f :=
  step_preserves K constructionStep
theorem existing_resolution_blocks_reescalation :
    ¬ ExpressivityEmittable K sourceState extendedLanguage target := by
  apply existing_resolution_forbids_expressivity
  exact ⟨target, constructed_resolves, rfl⟩

end VerifiedGeneratorConstruction
