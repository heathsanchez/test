import Std.Tactic

universe u

namespace EvidenceGeneratesInterventionOntology

structure Evidence (α : Type u) where
  args : List α

abbrev CandidateIntervention {α : Type u} (e : Evidence α) := Fin e.args.length

def deleteAt {α : Type u} (xs : List α) (p : Fin xs.length) : List α :=
  xs.take p.val ++ xs.drop (p.val + 1)

def response {α : Type u} (V : List α → Bool) (e : Evidence α)
    (p : CandidateIntervention e) : Bool :=
  V (deleteAt e.args p)

def InterventionEq {α : Type u} (V : List α → Bool) (e : Evidence α)
    (p q : CandidateIntervention e) : Prop :=
  response V e p = response V e q

def interventionSetoid {α : Type u} (V : List α → Bool) (e : Evidence α) :
    Setoid (CandidateIntervention e) where
  r := InterventionEq V e
  iseqv := by
    constructor
    · intro p; rfl
    · intro p q h; exact h.symm
    · intro p q r hpq hqr; exact hpq.trans hqr

def InterventionOntology {α : Type u} (V : List α → Bool) (e : Evidence α) :=
  Quotient (interventionSetoid V e)

def code {α : Type u} (V : List α → Bool) (e : Evidence α) :
    CandidateIntervention e → InterventionOntology V e :=
  fun p => Quotient.mk (interventionSetoid V e) p

theorem same_response_collapses
    {α : Type u} (V : List α → Bool) (e : Evidence α)
    {p q : CandidateIntervention e}
    (h : response V e p = response V e q) :
    code V e p = code V e q := by
  exact Quotient.sound h

theorem different_response_forces_distinct_interventions
    {α : Type u} (V : List α → Bool) (e : Evidence α)
    {p q : CandidateIntervention e}
    (h : response V e p ≠ response V e q) :
    code V e p ≠ code V e q := by
  intro heq
  exact h (Quotient.exact heq)

/-- Explicit unique-existence form, avoiding any supplied intervention label. -/
def UniqueRejectingIntervention
    {α : Type u} (V : List α → Bool) (e : Evidence α) : Prop :=
  ∃ p : CandidateIntervention e,
    response V e p = false ∧
    ∀ q : CandidateIntervention e,
      response V e q = false → q = p

noncomputable def selectedIntervention
    {α : Type u} {V : List α → Bool} {e : Evidence α}
    (h : UniqueRejectingIntervention V e) : CandidateIntervention e :=
  Classical.choose h

theorem selected_intervention_is_verifier_rejecting
    {α : Type u} {V : List α → Bool} {e : Evidence α}
    (h : UniqueRejectingIntervention V e) :
    response V e (selectedIntervention h) = false := by
  exact (Classical.choose_spec h).1

def erasedVerifier {α : Type u} : List α → Bool := fun _ => true

theorem erasure_collapses_generated_interventions
    {α : Type u} (e : Evidence α) (p q : CandidateIntervention e) :
    code (erasedVerifier (α := α)) e p = code erasedVerifier e q := by
  exact Quotient.sound rfl

def pairEvidence : Evidence Bool := ⟨[false, true]⟩

def pairVerifier : List Bool → Bool
  | [false, true] => true
  | [true] => false
  | [false] => true
  | _ => false

def pos0 : CandidateIntervention pairEvidence := ⟨0, by decide⟩
def pos1 : CandidateIntervention pairEvidence := ⟨1, by decide⟩

theorem pair_interventions_are_verifier_distinct :
    code pairVerifier pairEvidence pos0 ≠ code pairVerifier pairEvidence pos1 := by
  apply different_response_forces_distinct_interventions
  decide

theorem pair_has_unique_rejecting_intervention :
    UniqueRejectingIntervention pairVerifier pairEvidence := by
  refine ⟨pos0, ?_, ?_⟩
  · rfl
  · intro p hp
    apply Fin.ext
    have hlt : p.val < 2 := p.isLt
    have h0or1 : p.val = 0 ∨ p.val = 1 := by omega
    cases h0or1 with
    | inl h0 => exact h0
    | inr h1 =>
        exfalso
        have hptrue : response pairVerifier pairEvidence p = true := by
          simp [response, deleteAt, pairEvidence, h1, pairVerifier]
        rw [hp] at hptrue
        contradiction

theorem evidence_generates_verifier_selected_intervention_ontology :
    code pairVerifier pairEvidence pos0 ≠ code pairVerifier pairEvidence pos1 ∧
    ∃ h : UniqueRejectingIntervention pairVerifier pairEvidence,
      response pairVerifier pairEvidence (selectedIntervention h) = false := by
  exact ⟨pair_interventions_are_verifier_distinct,
    ⟨pair_has_unique_rejecting_intervention,
      selected_intervention_is_verifier_rejecting pair_has_unique_rejecting_intervention⟩⟩

#check same_response_collapses
#check different_response_forces_distinct_interventions
#check selected_intervention_is_verifier_rejecting
#check erasure_collapses_generated_interventions
#check pair_interventions_are_verifier_distinct
#check pair_has_unique_rejecting_intervention
#check evidence_generates_verifier_selected_intervention_ontology

end EvidenceGeneratesInterventionOntology
