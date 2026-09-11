import TypedResidualKernel

namespace VerifiedRepresentationGenesis
open TypedResidualKernel

theorem no_stateless_delay :
    ¬ ∃ f : Bool → Bool, ∀ previous current, f current = previous := by
  intro h
  obtain ⟨f, hf⟩ := h
  have h0 := hf false false
  have h1 := hf true false
  exact Bool.false_ne_true (h0.symm.trans h1)

def delayOutput (state : Bool) : Bool := state
def delayNext (_state input : Bool) : Bool := input

theorem one_bit_resolves (previous current : Bool) :
    delayOutput previous = previous ∧ delayNext previous current = current := by
  simp [delayOutput, delayNext]

theorem state_separator_necessary :
    (false, false).2 = (true, false).2 ∧
    (false, false).1 ≠ (true, false).1 := by decide

theorem prospective_change_reuse (previous current : Bool) :
    xor (delayOutput previous) current = xor previous current := by rfl

def oldLanguage : List Nat := [0, 1, 2, 3]
def extendedLanguage : List Nat := [0, 1, 2, 3, 4]
def sourceState : Nat := 7001
def nextState : Nat := 7002
def residual : Nat := 1

def K : Kernel where
  State := Nat; Language := List Nat; Authority := Unit; Policy := Unit
  Residual := Nat; Candidate := Nat; Future := Nat; Fact := Nat
  selectionObligation := fun _ _ _ _ _ => True
  uniqueIfRequired := fun _ _ => True
  identityResidual := fun _ _ _ _ => True
  choiceResidual := fun _ _ _ _ _ => True
  searchIncomplete := fun Ω _ _ => Ω = sourceState
  complete := fun Ω M _ => Ω = sourceState ∧ M = oldLanguage
  inLanguage := fun M σ => σ ∈ M
  resolves := fun σ ρ => σ = 4 ∧ ρ = residual
  isProtected := fun _ f => f ∈ oldLanguage

theorem old_negative : NoCurrentResolution K oldLanguage residual := by
  simp [NoCurrentResolution, K, oldLanguage, residual]
def expressive : Result K sourceState oldLanguage () () residual :=
  Result.unknownExpressivity ⟨rfl, rfl⟩ old_negative
def genesis : Step K expressive nextState := Step.proposeGenerator (fun _ h => h)

theorem genesis_is_only_licensed_kind : genesis.kind = TransitionKind.proposeGenerator := by rfl
theorem genesis_preserves_old :
    ∀ f, K.isProtected sourceState f → K.isProtected nextState f :=
  step_preserves K genesis

end VerifiedRepresentationGenesis
