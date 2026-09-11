namespace TypedResidualKernel

structure Kernel where
  State : Type
  Language : Type
  Authority : Type
  Policy : Type
  Residual : Type
  Candidate : Type
  Future : Type
  Fact : Type
  selectionObligation : State → Language → Authority → Policy → Candidate → Prop
  uniqueIfRequired : Policy → Candidate → Prop
  identityResidual : State → Language → Authority → Residual → Prop
  choiceResidual : State → Language → Authority → Policy → Residual → Prop
  searchIncomplete : State → Language → Residual → Prop
  complete : State → Language → Residual → Prop
  inLanguage : Language → Future → Prop
  resolves : Future → Residual → Prop
  isProtected : State → Fact → Prop

variable (K : Kernel)

def NoCurrentResolution (M : K.Language) (ρ : K.Residual) : Prop :=
  ¬ ∃ σ : K.Future, K.inLanguage M σ ∧ K.resolves σ ρ

/-- Every status carries exactly its warrant. The indices prevent evidence from
being reused at another state, language, authority, policy, or residual. -/
inductive Result (Ω : K.State) (M : K.Language) (u : K.Authority)
    (P : K.Policy) (ρ : K.Residual) : Type where
  | authorized (a : K.Candidate)
      (policyProof : K.selectionObligation Ω M u P a)
      (uniquenessProof : K.uniqueIfRequired P a)
  | unknownIdentity (proof : K.identityResidual Ω M u ρ)
  | unknownChoice (proof : K.choiceResidual Ω M u P ρ)
  | unknownSearch (proof : K.searchIncomplete Ω M ρ)
  | unknownExpressivity
      (completeProof : K.complete Ω M ρ)
      (negativeProof : NoCurrentResolution K M ρ)

def ExpressivityEmittable (Ω : K.State) (M : K.Language)
    (ρ : K.Residual) : Prop :=
  K.complete Ω M ρ ∧ NoCurrentResolution K M ρ

theorem unknownExpressivity_emittable
    {Ω : K.State} {M : K.Language} {ρ : K.Residual}
    (pc : K.complete Ω M ρ) (pn : NoCurrentResolution K M ρ) :
    ExpressivityEmittable K Ω M ρ :=
  ⟨pc, pn⟩

theorem unknownExpressivity_constructible
    {Ω : K.State} {M : K.Language} {u : K.Authority} {P : K.Policy}
    {ρ : K.Residual} (pc : K.complete Ω M ρ)
    (pn : NoCurrentResolution K M ρ) :
    Nonempty (Result K Ω M u P ρ) :=
  ⟨Result.unknownExpressivity pc pn⟩

theorem emittable_implies_complete_and_negative
    {Ω : K.State} {M : K.Language} {ρ : K.Residual}
    (h : ExpressivityEmittable K Ω M ρ) :
    K.complete Ω M ρ ∧ NoCurrentResolution K M ρ := h

theorem incomplete_forbids_expressivity
    {Ω : K.State} {M : K.Language} {ρ : K.Residual}
    (hIncomplete : ¬ K.complete Ω M ρ) :
    ¬ ExpressivityEmittable K Ω M ρ := by
  intro h
  exact hIncomplete (emittable_implies_complete_and_negative K h).1

theorem existing_resolution_forbids_expressivity
    {Ω : K.State} {M : K.Language} {ρ : K.Residual}
    (hExisting : ∃ σ : K.Future, K.inLanguage M σ ∧ K.resolves σ ρ) :
    ¬ ExpressivityEmittable K Ω M ρ := by
  intro h
  exact (emittable_implies_complete_and_negative K h).2 hExisting

inductive TransitionKind where
  | act
  | refineIdentity
  | seekChoiceEvidence
  | improveSearch
  | proposeGenerator
  deriving DecidableEq

/-- These are the only lawful responses. There is no constructor from search
uncertainty to language extension or from choice uncertainty to arbitrary act. -/
inductive Step {M : K.Language} {u : K.Authority} {P : K.Policy}
    {ρ : K.Residual} {Ω : K.State} : Result K Ω M u P ρ → K.State → Type where
  | act {a : K.Candidate} {pa : K.selectionObligation Ω M u P a}
      {pu : K.uniqueIfRequired P a} {Ω' : K.State}
      (preserve : ∀ f, K.isProtected Ω f → K.isProtected Ω' f) :
      Step (.authorized a pa pu) Ω'
  | refineIdentity {pi : K.identityResidual Ω M u ρ} {Ω' : K.State}
      (preserve : ∀ f, K.isProtected Ω f → K.isProtected Ω' f) :
      Step (.unknownIdentity pi) Ω'
  | seekChoiceEvidence {pc : K.choiceResidual Ω M u P ρ} {Ω' : K.State}
      (preserve : ∀ f, K.isProtected Ω f → K.isProtected Ω' f) :
      Step (.unknownChoice pc) Ω'
  | improveSearch {ps : K.searchIncomplete Ω M ρ} {Ω' : K.State}
      (preserve : ∀ f, K.isProtected Ω f → K.isProtected Ω' f) :
      Step (.unknownSearch ps) Ω'
  | proposeGenerator {pc : K.complete Ω M ρ}
      {pn : NoCurrentResolution K M ρ} {Ω' : K.State}
      (preserve : ∀ f, K.isProtected Ω f → K.isProtected Ω' f) :
      Step (.unknownExpressivity pc pn) Ω'

def Step.kind {M : K.Language} {u : K.Authority} {P : K.Policy}
    {ρ : K.Residual} {Ω Ω' : K.State} {r : Result K Ω M u P ρ}
    (s : Step K r Ω') : TransitionKind := by
  cases s with
  | act => exact .act
  | refineIdentity => exact .refineIdentity
  | seekChoiceEvidence => exact .seekChoiceEvidence
  | improveSearch => exact .improveSearch
  | proposeGenerator => exact .proposeGenerator

theorem step_preserves {M : K.Language} {u : K.Authority} {P : K.Policy}
    {ρ : K.Residual} {Ω Ω' : K.State} {r : Result K Ω M u P ρ}
    (s : Step K r Ω') : ∀ f, K.isProtected Ω f → K.isProtected Ω' f := by
  cases s <;> assumption

inductive Path : K.State → K.State → Type where
  | refl (Ω : K.State) : Path Ω Ω
  | cons {Ω Ω' Ω'' : K.State} {M : K.Language} {u : K.Authority}
      {P : K.Policy} {ρ : K.Residual} {r : Result K Ω M u P ρ}
      (head : Step K r Ω') (tail : Path Ω' Ω'') : Path Ω Ω''

theorem path_preserves {Ω Ω' : K.State} (p : Path K Ω Ω') :
    ∀ f, K.isProtected Ω f → K.isProtected Ω' f := by
  induction p with
  | refl =>
      intro f hf
      exact hf
  | cons head tail ih =>
      intro f hf
      exact ih f (step_preserves K head f hf)

theorem unknownSearch_only_improves
    {M : K.Language} {u : K.Authority} {P : K.Policy} {ρ : K.Residual}
    {Ω Ω' : K.State} {ps : K.searchIncomplete Ω M ρ}
    (s : Step K
      (Result.unknownSearch ps : Result K Ω M u P ρ) Ω') :
    s.kind = TransitionKind.improveSearch := by
  cases s
  rfl

theorem unknownChoice_only_seeks_evidence
    {M : K.Language} {u : K.Authority} {P : K.Policy} {ρ : K.Residual}
    {Ω Ω' : K.State} {pc : K.choiceResidual Ω M u P ρ}
    (s : Step K (Result.unknownChoice pc) Ω') :
    s.kind = TransitionKind.seekChoiceEvidence := by
  cases s
  rfl

theorem unknownExpressivity_only_proposes_generator
    {M : K.Language} {u : K.Authority} {P : K.Policy} {ρ : K.Residual}
    {Ω Ω' : K.State} {pc : K.complete Ω M ρ}
    {pn : NoCurrentResolution K M ρ}
    (s : Step K
      (Result.unknownExpressivity pc pn : Result K Ω M u P ρ) Ω') :
    s.kind = TransitionKind.proposeGenerator := by
  cases s
  rfl

end TypedResidualKernel
