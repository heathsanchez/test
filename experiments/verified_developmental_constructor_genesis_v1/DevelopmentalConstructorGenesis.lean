import TypedResidualKernel

namespace VerifiedDevelopmentalConstructorGenesis
open TypedResidualKernel

abbrev Record4 := Bool × Bool × Bool × Bool
def oldRep (r : Record4) : Bool := r.2.2.2
def project (i : Fin 4) (r : Record4) : Bool :=
  match i with
  | 0 => r.1
  | 1 => r.2.1
  | 2 => r.2.2.1
  | 3 => r.2.2.2

theorem unary_recode_cannot_separate
    (f : Bool → Bool) (a b : Record4) (h : oldRep a = oldRep b) :
    f (oldRep a) = f (oldRep b) := by rw [h]

def refine (i : Fin 4) (r : Record4) : Bool × Bool := (oldRep r, project i r)

theorem refine_preserves_old (i : Fin 4) (r : Record4) : (refine i r).1 = oldRep r := by rfl

def heldLeft : Record4 := (false, false, false, false)
def heldRight : Record4 := (false, false, true, false)

theorem held_old_collision : oldRep heldLeft = oldRep heldRight := by rfl
theorem held_projection_separates : refine 2 heldLeft ≠ refine 2 heldRight := by decide
theorem sham_projection_fails : refine 0 heldLeft = refine 0 heldRight := by decide

def oldDevLanguage : List Nat := [0, 1, 2, 3]
def devResidual : Nat := 99
def sourceState : Nat := 8101
def nextState : Nat := 8102

def K : Kernel where
  State := Nat; Language := List Nat; Authority := Unit; Policy := Unit
  Residual := Nat; Candidate := Nat; Future := Nat; Fact := Nat
  selectionObligation := fun _ _ _ _ _ => True
  uniqueIfRequired := fun _ _ => True
  identityResidual := fun _ _ _ _ => True
  choiceResidual := fun _ _ _ _ _ => True
  searchIncomplete := fun Ω _ _ => Ω = sourceState
  complete := fun Ω M _ => Ω = sourceState ∧ M = oldDevLanguage
  inLanguage := fun M op => op ∈ M
  resolves := fun op ρ => op = 4 ∧ ρ = devResidual
  isProtected := fun _ f => f ∈ oldDevLanguage

theorem no_old_developmental_repair : NoCurrentResolution K oldDevLanguage devResidual := by
  simp [NoCurrentResolution, K, oldDevLanguage, devResidual]

def devExpressivity : Result K sourceState oldDevLanguage () () devResidual :=
  Result.unknownExpressivity ⟨rfl, rfl⟩ no_old_developmental_repair
def constructDeveloper : Step K devExpressivity nextState :=
  Step.proposeGenerator (fun _ h => h)

theorem developmental_genesis_is_licensed :
    constructDeveloper.kind = TransitionKind.proposeGenerator := by rfl
theorem developmental_genesis_preserves :
    ∀ f, K.isProtected sourceState f → K.isProtected nextState f :=
  step_preserves K constructDeveloper

end VerifiedDevelopmentalConstructorGenesis
