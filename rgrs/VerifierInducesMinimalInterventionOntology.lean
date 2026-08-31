import Std

universe u v w

namespace VerifierInducesMinimalInterventionOntology

def InterventionEq
    {W : Type u} {I : Type v}
    (response : W → I → Bool) (i j : I) : Prop :=
  ∀ world, response world i = response world j

theorem interventionEq_refl
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    ∀ i, InterventionEq response i i := by
  intro i world
  rfl

theorem interventionEq_symm
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    ∀ {i j}, InterventionEq response i j → InterventionEq response j i := by
  intro i j h world
  exact (h world).symm

theorem interventionEq_trans
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    ∀ {i j k}, InterventionEq response i j → InterventionEq response j k →
      InterventionEq response i k := by
  intro i j k hij hjk world
  exact (hij world).trans (hjk world)

def interventionSetoid
    {W : Type u} {I : Type v} (response : W → I → Bool) : Setoid I where
  r := InterventionEq response
  iseqv := ⟨interventionEq_refl response,
    @interventionEq_symm W I response,
    @interventionEq_trans W I response⟩

def InterventionOntology
    {W : Type u} {I : Type v} (response : W → I → Bool) :=
  Quotient (interventionSetoid response)

def interventionCode
    {W : Type u} {I : Type v} (response : W → I → Bool) :
    I → InterventionOntology response :=
  fun i => Quotient.mk (interventionSetoid response) i

theorem indistinguishable_interventions_collapse
    {W : Type u} {I : Type v} (response : W → I → Bool)
    {i j : I} (h : ∀ world, response world i = response world j) :
    interventionCode response i = interventionCode response j := by
  exact Quotient.sound h

theorem separated_interventions_remain_distinct
    {W : Type u} {I : Type v} (response : W → I → Bool)
    {i j : I} (world : W) (hsep : response world i ≠ response world j) :
    interventionCode response i ≠ interventionCode response j := by
  intro h
  have hs : InterventionEq response i j := Quotient.exact h
  exact hsep (hs world)

def Sufficient
    {W : Type u} {I : Type v} {R : Type w}
    (response : W → I → Bool) (q : I → R) : Prop :=
  ∀ world, ∃ decode : R → Bool, ∀ i, decode (q i) = response world i

theorem every_sufficient_encoding_preserves_separation
    {W : Type u} {I : Type v} {R : Type w}
    (response : W → I → Bool) (q : I → R)
    (hsuff : Sufficient response q)
    {i j : I} (world : W) (hsep : response world i ≠ response world j) :
    q i ≠ q j := by
  rcases hsuff world with ⟨decode, hdecode⟩
  intro heq
  apply hsep
  calc
    response world i = decode (q i) := (hdecode i).symm
    _ = decode (q j) := by rw [heq]
    _ = response world j := hdecode j

theorem sufficient_encoding_cannot_forget_more_than_verifier
    {W : Type u} {I : Type v} {R : Type w}
    (response : W → I → Bool) (q : I → R)
    (hsuff : Sufficient response q)
    {i j : I} (heq : q i = q j) :
    InterventionEq response i j := by
  intro world
  rcases hsuff world with ⟨decode, hdecode⟩
  calc
    response world i = decode (q i) := (hdecode i).symm
    _ = decode (q j) := by rw [heq]
    _ = response world j := hdecode j

theorem verifier_induces_minimal_intervention_ontology
    {W : Type u} {I : Type v} {R : Type w}
    (response : W → I → Bool) (q : I → R)
    (hsuff : Sufficient response q) :
    ∀ {i j : I}, q i = q j →
      interventionCode response i = interventionCode response j := by
  intro i j heq
  exact Quotient.sound
    (sufficient_encoding_cannot_forget_more_than_verifier response q hsuff heq)

def erasedResponse {W : Type u} {I : Type v} : W → I → Bool :=
  fun _ _ => true

theorem erasing_intervention_consequence_collapses_ontology
    {W : Type u} {I : Type v} (i j : I) :
    interventionCode (erasedResponse (W := W) (I := I)) i =
      interventionCode erasedResponse j := by
  exact Quotient.sound (by intro world; rfl)

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
  intro world
  cases world <;> rfl

theorem tiny_i0_separates_from_i1 :
    interventionCode tinyResponse .i0 ≠ interventionCode tinyResponse .i1 := by
  exact separated_interventions_remain_distinct tinyResponse .w0 (by decide)

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
