universe uState uLanguage uAuthority uPolicy uResidual uCandidate uFuture uFact

namespace TypedResidualKernel

variable {State : Type uState}
variable {Language : Type uLanguage}
variable {Authority : Type uAuthority}
variable {Policy : Type uPolicy}
variable {Residual : Type uResidual}
variable {Candidate : Type uCandidate}
variable {Future : Type uFuture}
variable {Fact : Type uFact}

variable (SelectionObligation :
  State → Language → Authority → Policy → Candidate → Prop)
variable (UniqueIfRequired : Policy → Candidate → Prop)
variable (IdentityResidual : State → Language → Authority → Residual → Prop)
variable (ChoiceResidual : State → Language → Authority → Policy → Residual → Prop)
variable (SearchIncomplete : State → Language → Residual → Prop)
variable (Complete : State → Language → Residual → Prop)
variable (InLanguage : Language → Future → Prop)
variable (Resolves : Future → Residual → Prop)
variable (Protected : State → Fact → Prop)

def NoCurrentResolution (M : Language) (ρ : Residual) : Prop :=
  ¬ ∃ σ : Future, InLanguage M σ ∧ Resolves σ ρ

/-- Every emitted status carries the evidence that warrants exactly that status.
The indices prevent evidence for one state/language/authority/policy snapshot from
being silently reused at another snapshot. -/
inductive Result (Ω : State) (M : Language) (u : Authority)
    (P : Policy) (ρ : Residual) : Type (max uCandidate 0) where
  | authorized (a : Candidate)
      (policyProof : SelectionObligation Ω M u P a)
      (uniquenessProof : UniqueIfRequired P a)
  | unknownIdentity
      (proof : IdentityResidual Ω M u ρ)
  | unknownChoice
      (proof : ChoiceResidual Ω M u P ρ)
  | unknownSearch
      (proof : SearchIncomplete Ω M ρ)
  | unknownExpressivity
      (completeProof : Complete Ω M ρ)
      (negativeProof : NoCurrentResolution InLanguage Resolves M ρ)

variable {SelectionObligation UniqueIfRequired IdentityResidual ChoiceResidual
  SearchIncomplete Complete InLanguage Resolves Protected}

abbrev R := Result SelectionObligation UniqueIfRequired IdentityResidual
  ChoiceResidual SearchIncomplete Complete InLanguage Resolves

/-- Emittability of expressive inadequacy is exactly possession of both proofs. -/
def ExpressivityEmittable (Ω : State) (M : Language) (u : Authority)
    (P : Policy) (ρ : Residual) : Prop :=
  ∃ (pc : Complete Ω M ρ)
    (pn : NoCurrentResolution InLanguage Resolves M ρ),
    Nonempty (R Ω M u P ρ)

theorem unknownExpressivity_emittable
    {Ω : State} {M : Language} {u : Authority} {P : Policy} {ρ : Residual}
    (pc : Complete Ω M ρ)
    (pn : NoCurrentResolution InLanguage Resolves M ρ) :
    ExpressivityEmittable (SelectionObligation := SelectionObligation)
      (UniqueIfRequired := UniqueIfRequired)
      (IdentityResidual := IdentityResidual) (ChoiceResidual := ChoiceResidual)
      (SearchIncomplete := SearchIncomplete) Complete InLanguage Resolves Ω M u P ρ := by
  exact ⟨pc, pn, ⟨R.unknownExpressivity pc pn⟩⟩

theorem emittable_implies_complete_and_negative
    {Ω : State} {M : Language} {u : Authority} {P : Policy} {ρ : Residual}
    (h : ExpressivityEmittable (SelectionObligation := SelectionObligation)
      (UniqueIfRequired := UniqueIfRequired)
      (IdentityResidual := IdentityResidual) (ChoiceResidual := ChoiceResidual)
      (SearchIncomplete := SearchIncomplete) Complete InLanguage Resolves Ω M u P ρ) :
    Complete Ω M ρ ∧ NoCurrentResolution InLanguage Resolves M ρ := by
  rcases h with ⟨pc, pn, _⟩
  exact ⟨pc, pn⟩

theorem incomplete_forbids_expressivity
    {Ω : State} {M : Language} {u : Authority} {P : Policy} {ρ : Residual}
    (hIncomplete : ¬ Complete Ω M ρ) :
    ¬ ExpressivityEmittable (SelectionObligation := SelectionObligation)
      (UniqueIfRequired := UniqueIfRequired)
      (IdentityResidual := IdentityResidual) (ChoiceResidual := ChoiceResidual)
      (SearchIncomplete := SearchIncomplete) Complete InLanguage Resolves Ω M u P ρ := by
  intro h
  exact hIncomplete (emittable_implies_complete_and_negative h).1

theorem existing_resolution_forbids_expressivity
    {Ω : State} {M : Language} {u : Authority} {P : Policy} {ρ : Residual}
    (hExisting : ∃ σ : Future, InLanguage M σ ∧ Resolves σ ρ) :
    ¬ ExpressivityEmittable (SelectionObligation := SelectionObligation)
      (UniqueIfRequired := UniqueIfRequired)
      (IdentityResidual := IdentityResidual) (ChoiceResidual := ChoiceResidual)
      (SearchIncomplete := SearchIncomplete) Complete InLanguage Resolves Ω M u P ρ := by
  intro h
  exact (emittable_implies_complete_and_negative h).2 hExisting

inductive TransitionKind where
  | act
  | refineIdentity
  | seekChoiceEvidence
  | improveSearch
  | proposeGenerator
  deriving DecidableEq

/-- The transition constructors are the constitution: no cross-boundary repair
constructor exists. Every constructor also requires preservation. -/
inductive Step {M : Language} {u : Authority} {P : Policy} {ρ : Residual}
    {Ω : State} : R Ω M u P ρ → State → Type (max uFact 0) where
  | act {a : Candidate} {pa : SelectionObligation Ω M u P a}
      {pu : UniqueIfRequired P a} {Ω' : State}
      (preserve : ∀ f, Protected Ω f → Protected Ω' f) :
      Step (.authorized a pa pu) Ω'
  | refineIdentity {pi : IdentityResidual Ω M u ρ} {Ω' : State}
      (preserve : ∀ f, Protected Ω f → Protected Ω' f) :
      Step (.unknownIdentity pi) Ω'
  | seekChoiceEvidence {pc : ChoiceResidual Ω M u P ρ} {Ω' : State}
      (preserve : ∀ f, Protected Ω f → Protected Ω' f) :
      Step (.unknownChoice pc) Ω'
  | improveSearch {ps : SearchIncomplete Ω M ρ} {Ω' : State}
      (preserve : ∀ f, Protected Ω f → Protected Ω' f) :
      Step (.unknownSearch ps) Ω'
  | proposeGenerator {pc : Complete Ω M ρ}
      {pn : NoCurrentResolution InLanguage Resolves M ρ} {Ω' : State}
      (preserve : ∀ f, Protected Ω f → Protected Ω' f) :
      Step (.unknownExpressivity pc pn) Ω'

def Step.kind {M : Language} {u : Authority} {P : Policy} {ρ : Residual}
    {Ω Ω' : State} {r : R Ω M u P ρ} (_ : Step Protected r Ω') :
    TransitionKind := by
  cases r with
  | authorized => exact .act
  | unknownIdentity => exact .refineIdentity
  | unknownChoice => exact .seekChoiceEvidence
  | unknownSearch => exact .improveSearch
  | unknownExpressivity => exact .proposeGenerator

theorem step_preserves {M : Language} {u : Authority} {P : Policy}
    {ρ : Residual} {Ω Ω' : State} {r : R Ω M u P ρ}
    (s : Step Protected r Ω') :
    ∀ f, Protected Ω f → Protected Ω' f := by
  cases s <;> assumption

/-- A development history existentially hides episode-local evidence, while each
edge remains proof-carrying. -/
inductive Path : State → State → Type (max uFact uLanguage uAuthority uPolicy uResidual) where
  | refl (Ω : State) : Path Ω Ω
  | cons {Ω Ω' Ω'' : State} {M : Language} {u : Authority} {P : Policy}
      {ρ : Residual} {r : R Ω M u P ρ}
      (head : Step Protected r Ω') (tail : Path Ω' Ω'') : Path Ω Ω''

theorem path_preserves {Ω Ω' : State} (p : Path Protected Ω Ω') :
    ∀ f, Protected Ω f → Protected Ω' f := by
  induction p with
  | refl =>
      intro f hf
      exact hf
  | cons head tail ih =>
      intro f hf
      exact ih f (step_preserves head f hf)

/-- The prohibited escalation has no Step constructor. Concretely, a search
unknown can only inhabit the improveSearch constructor. -/
theorem unknownSearch_only_improves
    {M : Language} {u : Authority} {P : Policy} {ρ : Residual} {Ω Ω' : State}
    {ps : SearchIncomplete Ω M ρ}
    (s : Step Protected (R.unknownSearch ps) Ω') :
    s.kind = .improveSearch := by
  rfl

theorem unknownChoice_only_seeks_evidence
    {M : Language} {u : Authority} {P : Policy} {ρ : Residual} {Ω Ω' : State}
    {pc : ChoiceResidual Ω M u P ρ}
    (s : Step Protected (R.unknownChoice pc) Ω') :
    s.kind = .seekChoiceEvidence := by
  rfl

end TypedResidualKernel
