import Std

abbrev History := Fin 4
abbrev Observation := History → Bool

def sameObservation (q : Observation) (a b : History) : Prop := q a = q b

def Refines (q₁ q₂ : Observation) : Prop :=
  ∀ a b, sameObservation q₁ a b → sameObservation q₂ a b

def xorObservation : Observation
  | ⟨0, _⟩ => false | ⟨1, _⟩ => true
  | ⟨2, _⟩ => true  | ⟨3, _⟩ => false

def singletonObservation : Observation
  | ⟨3, _⟩ => true | _ => false

theorem xor_not_refines_singleton :
    ¬ Refines xorObservation singletonObservation := by
  intro h
  have z := h ⟨0, by omega⟩ ⟨3, by omega⟩
  simp [sameObservation, xorObservation, singletonObservation] at z

theorem singleton_not_refines_xor :
    ¬ Refines singletonObservation xorObservation := by
  intro h
  have z := h ⟨0, by omega⟩ ⟨1, by omega⟩
  simp [sameObservation, xorObservation, singletonObservation] at z

inductive RepairVerdict where
  | canonicalRepair
  | multipleMinimalRepairs
  | noRepairInMetaSubstrate

structure MultipleMinimalCertificate where
  left : Observation
  right : Observation
  incomparableLR : ¬ Refines left right
  incomparableRL : ¬ Refines right left

def certifiedOutcome : MultipleMinimalCertificate :=
  ⟨xorObservation, singletonObservation,
   xor_not_refines_singleton, singleton_not_refines_xor⟩
