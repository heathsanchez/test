import Std

universe u v

namespace VerifierInducesMinimalInterventionOntology

/-- Candidate interventions have no semantic names.  Their identity is determined
    only by how every verifier context responds to them. -/
def InterventionEq
    {W : Type u} {I : Type v}
    (response : W → I → Bool) (i j : I) : Prop :=
  ∀ w, response w i = response w j

 theorem interventionEq_refl
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    ∀ i, InterventionEq response i i := by
  intro i w
  rfl

 theorem interventionEq_symm
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    ∀ {i j}, InterventionEq response i j → InterventionEq response j i := by
  intro i j h w
  exact (h w).symm

 theorem interventionEq_trans
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    ∀ {i j k}, InterventionEq response i j → InterventionEq response j k →
      InterventionEq response i k := by
  intro i j k hij hjk w
  exact (hij w).trans (hjk w)

/-- Verifier-consequence equivalence is a Setoid on interventions. -/
def interventionSetoid
    {W : Type u} {I : Type v} (response : W → I → Bool) : Setoid I where
  r := InterventionEq response
  iseqv := ⟨interventionEq_refl response,
    @interventionEq_symm W I response,
    @interventionEq_trans W I response⟩

/-- The intervention ontology is not a supplied labeling scheme: it is the
    quotient of anonymous interventions by all verifier-visible consequences. -/
def InterventionOntology
    {W : Type u} {I : Type v} (response : W → I → Bool) :=
  Quotient (interventionSetoid response)

/-- Canonical quotient map. -/
def interventionCode
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    I → InterventionOntology response :=
  fun i => Quotient.mk (interventionSetoid response) i

/-- Interventions with identical verifier behavior become the same ontology
    object. -/
theorem indistinguishable_interventions_collapse
    {W : Type u} {I : Type v} (response : W → I → Bool)
    {i j : I} (h : ∀ w, response w i = response w j) :
    interventionCode response i = interventionCode response j := by
  exact Quotient.sound h

/-- Any verifier context that separates two interventions forces them to remain
    distinct in the induced ontology. -/
theorem separated_interventions_remain_distinct
    {W : Type u} {I : Type v} (response : W → I → Bool)
    {i j : I} (w : W) (hsep : response w i ≠ response w j) :
    interventionCode response i ≠ interventionCode response j := by
  intro h
  have hs : InterventionEq response i j := Quotient.exact h
  exact hsep (hs w)

/-- A representation of interventions is sufficient when every verifier response
    factors through it. -/
def Sufficient
    {W : Type u} {I : Type v} {R : Type*}
    (response : W → I → Bool) (q : I → R) : Prop :=
  ∀ w, ∃ decode : R → Bool, ∀ i, decode (q i) = response w i

/-- Every sufficient intervention representation must preserve every distinction
    made by the verifier family. -/
theorem every_sufficient_encoding_preserves_separation
    {W : Type u} {I : Type v} {R : Type*}
    (response : W → I → Bool) (q : I → R)
    (hsuff : Sufficient response q)
    {i j : I} (w : W) (hsep : response w i ≠ response w j) :
    q i ≠ q j := by
  rcases hsuff w with ⟨decode, hdecode⟩
  intro heq
  apply hsep
  calc
    response w i = decode (q i) := (hdecode i).symm
    _ = decode (q j) := by rw [heq]
    _ = response w j := hdecode j

/-- Conversely, if a representation identifies two interventions, every verifier
    consequence must identify them too. -/
theorem sufficient_encoding_cannot_forget_more_than_verifier
    {W : Type u} {I : Type v} {R : Type*}
    (response : W → I → Bool) (q : I → R)
    (hsuff : Sufficient response q)
    {i j : I} (heq : q i = q j) :
    InterventionEq response i j := by
  intro w
  rcases hsuff w with ⟨decode, hdecode⟩
  calc
    response w i = decode (q i) := (hdecode i).symm
    _ = decode (q j) := by rw [heq]
    _ = response w j := hdecode j

/-- The quotient is therefore the coarsest identity compatible with all verifier
    consequences: any sufficient interface may refine it, but may not collapse
    two quotient-distinct interventions. -/
theorem verifier_induces_minimal_intervention_ontology
    {W : Type u} {I : Type v} {R : Type*}
    (response : W → I → Bool) (q : I → R)
    (hsuff : Sufficient response q) :
    ∀ {i j : I}, q i = q j →
      interventionCode response i = interventionCode response j := by
  intro i j heq
  exact Quotient.sound
    (sufficient_encoding_cannot_forget_more_than_verifier response q hsuff heq)

/-- If the verifier is intervention-insensitive, the ontology collapses
    completely. -/
def erasedResponse {W : Type u} {I : Type v} : W → I → Bool :=
  fun _ _ => true

 theorem erasing_intervention_consequence_collapses_ontology
    {W : Type u} {I : Type v} (i j : I) :
    interventionCode (erasedResponse (W := W) (I := I)) i =
      interventionCode erasedResponse j := by
  exact Quotient.sound (by intro w; rfl)

/-- Tiny anonymous witness showing the quotient can generate nontrivial
    experimental structure solely from verifier response. -/
inductive TinyWorld where | w0 | w1
inductive TinyIntervention where | i0 | i1 | i2

def tinyResponse : TinyWorld → TinyIntervention → Bool
  | .w0, .i0 => false
  | .w0, .i1 => true
  | .w0, .i2 => true
  | .w1, .i0 => true
  | .w1, .i1 => false
  | .w1, .i2 => false

theorem tiny_i1_i2_collapse :
    interventionCode tinyResponse .i1 = interventionCode tinyResponse .i2 := by
  apply Quotient.sound
  intro w
  cases w <;> rfl

 theorem tiny_i0_separates_from_i1 :
    interventionCode tinyResponse .i0 ≠ interventionCode tinyResponse .i1 := by
  exact separated_interventions_remain_distinct tinyResponse .w0 (by decide)

/-- End-to-end meta-MSI statement: the same consequence-induced quotient law
    used for object identity applies one level up to experimental actions.
    Intervention identity is the intersection of all verifier kernels over
    worlds; no semantic intervention labels are needed for the quotient.

    Remaining scaffold: the candidate carrier `I` and the verifier-response
    family are supplied.  This does not generate interventions ex nihilo. -/
theorem consequence_induces_experiment_identity :
    interventionCode tinyResponse .i1 = interventionCode tinyResponse .i2 ∧
    interventionCode tinyResponse .i0 ≠ interventionCode tinyResponse .i1 := by
  exact ⟨tiny_i1_i2_collapse, tiny_i0_separates_from_i1⟩

#check indistinguishable_interventions_collapse
#check separated_interventions_remain_distinct
#check every_sufficient_encoding_preserves_separation
#check sufficient_encoding_cannot_forget_more_than_verifier
#check verifier_induces_minimal_intervention_ontology
#check erasing_intervention_consequence_collapses_ontology
#check consequence_induces_experiment_identity

end VerifierInducesMinimalInterventionOntology
