import Init

/-!
This file proves the conditional Decidable-to-Bool reduction boundary.
The source proof P is indispensable: a raw Bool or neutral recursor head
is not a typed constructor certificate. C64 n7 still lacks that proof.
-/

namespace NucleusDecide

theorem isTrue_evaluates_true {P : Prop} (proof : P) :
    @decide P (Decidable.isTrue proof) = true := by
  rfl

theorem isFalse_evaluates_false {P : Prop} (refutation : ¬ P) :
    @decide P (Decidable.isFalse refutation) = false := by
  rfl

theorem checked_decide_true_implies_proof {P : Prop} (d : Decidable P)
    (h : @decide P d = true) : P := by
  cases d with
  | isTrue proof => exact proof
  | isFalse _ => cases h

theorem checked_decide_false_implies_refutation {P : Prop} (d : Decidable P)
    (h : @decide P d = false) : ¬ P := by
  cases d with
  | isTrue _ => cases h
  | isFalse refutation => exact refutation

theorem finite_domain_isTrue {n : Nat} {P : Fin n → Prop}
    (proof : ∀ i : Fin n, P i) :
    @decide (∀ i : Fin n, P i) (Decidable.isTrue proof) = true := by
  rfl

theorem raw_true_cannot_certify_arbitrary_prop :
    ¬ (∀ P : Prop, True → P) := by
  intro claim
  exact claim False True.intro


/-!
Independent, axiom-free finite certificate composition.
This does not trust a list of Boolean observations: each leaf contains a
typed Decidable and a checked equality showing its actual decision is true.
-/
inductive FinDecisionCertificate : (n : Nat) → (Fin n → Prop) → Type where
  | nil {P : Fin 0 → Prop} : FinDecisionCertificate 0 P
  | cons {n : Nat} {P : Fin (n + 1) → Prop}
      (head : Decidable (P ⟨0, Nat.zero_lt_succ n⟩))
      (headTrue : @decide (P ⟨0, Nat.zero_lt_succ n⟩) head = true)
      (tail : FinDecisionCertificate n (fun i => P i.succ)) :
      FinDecisionCertificate (n + 1) P

theorem fin_certificate_sound {n : Nat} {P : Fin n → Prop}
    (cert : FinDecisionCertificate n P) : ∀ i : Fin n, P i := by
  induction cert with
  | nil =>
      intro i
      exact Fin.elim0 i
  | cons head headTrue tail ih =>
      intro i
      cases i using Fin.cases with
      | zero =>
          exact checked_decide_true_implies_proof head headTrue
      | succ j =>
          exact ih j

end NucleusDecide

#print axioms NucleusDecide.isTrue_evaluates_true
#print axioms NucleusDecide.isFalse_evaluates_false
#print axioms NucleusDecide.checked_decide_true_implies_proof
#print axioms NucleusDecide.checked_decide_false_implies_refutation
#print axioms NucleusDecide.finite_domain_isTrue
#print axioms NucleusDecide.raw_true_cannot_certify_arbitrary_prop
#print axioms NucleusDecide.fin_certificate_sound
