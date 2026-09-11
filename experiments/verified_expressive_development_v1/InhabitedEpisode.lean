import TypedResidualKernel

namespace VerifiedExpressiveDevelopment

open TypedResidualKernel

def oldLanguage : List Nat := [0, 3, 5, 10, 12, 15]
def extendedLanguage : List Nat := List.range 16
def target : Nat := 8
def reuseTarget : Nat := 4
def sourceDigest : Nat := 1001
def nextDigest : Nat := 1002

theorem old_negative :
    ¬ ∃ σ : Nat, σ ∈ oldLanguage ∧ σ = target := by decide

theorem generator_novel : target ∉ oldLanguage := by decide
theorem residual_resolved : target ∈ extendedLanguage := by decide
theorem prospective_reuse_available :
    reuseTarget ∉ oldLanguage ∧ reuseTarget ∈ extendedLanguage := by decide

theorem old_preserved :
    ∀ σ : Nat, σ ∈ oldLanguage → σ ∈ extendedLanguage := by
  intro σ h
  exact List.mem_cons_of_mem target h

theorem removal_restores_obstruction :
    target ∉ oldLanguage ∧ reuseTarget ∉ oldLanguage := by decide

def episodeKernel : Kernel where
  State := Nat
  Language := List Nat
  Authority := Unit
  Policy := Unit
  Residual := Nat
  Candidate := Nat
  Future := Nat
  Fact := Nat
  selectionObligation := fun _ _ _ _ _ => True
  uniqueIfRequired := fun _ _ => True
  identityResidual := fun _ _ _ _ => True
  choiceResidual := fun _ _ _ _ _ => True
  searchIncomplete := fun Ω _ _ => Ω = sourceDigest
  complete := fun Ω M _ => Ω = sourceDigest ∧ M = oldLanguage
  inLanguage := fun M σ => σ ∈ M
  resolves := fun σ ρ => σ = ρ
  isProtected := fun _ fact => fact ∈ oldLanguage

theorem complete_old :
    episodeKernel.complete sourceDigest oldLanguage target := by
  exact ⟨rfl, rfl⟩

theorem no_old_resolution :
    NoCurrentResolution episodeKernel oldLanguage target := by
  exact old_negative

def searchResult :
    Result episodeKernel sourceDigest oldLanguage () () target :=
  Result.unknownSearch rfl

def expressiveResult :
    Result episodeKernel sourceDigest oldLanguage () () target :=
  Result.unknownExpressivity complete_old no_old_resolution

def genesisStep :
    Step episodeKernel expressiveResult nextDigest :=
  Step.proposeGenerator (fun _ h => h)

theorem transition_is_generator_proposal :
    genesisStep.kind = TransitionKind.proposeGenerator := by rfl

theorem transition_preserves_old :
    ∀ fact, episodeKernel.isProtected sourceDigest fact →
      episodeKernel.isProtected nextDigest fact :=
  step_preserves episodeKernel genesisStep

def episodePath : Path episodeKernel sourceDigest nextDigest :=
  Path.cons genesisStep (Path.refl nextDigest)

theorem history_preserves_old :
    ∀ fact, episodeKernel.isProtected sourceDigest fact →
      episodeKernel.isProtected nextDigest fact :=
  path_preserves episodeKernel episodePath

theorem stale_complete_certificate_rejected :
    ¬ episodeKernel.complete nextDigest oldLanguage target := by decide

theorem existing_resolution_blocks_expressivity :
    ¬ ExpressivityEmittable episodeKernel sourceDigest extendedLanguage target := by
  apply existing_resolution_forbids_expressivity
  exact ⟨target, residual_resolved, rfl⟩

end VerifiedExpressiveDevelopment
