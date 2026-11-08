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
A conditional finite certificate uses the source's actual Nat.allLTTR
Boolean procedure. It is a semantic result about the proposition, NOT a claim
that the runtime-tail-recursive procedure is definitionally equal to the
non-tail-recursive kernel reduction of Nat.decidableBallLT.
-/

theorem allLTTR_fin_sound {n : Nat} {P : Fin n → Prop} [DecidablePred P]
    (certificate : Nat.allLTTR n (fun k hk => decide (P ⟨k, hk⟩)) = true) :
    ∀ i : Fin n, P i := by
  intro i
  have h := (Nat.allLTTR_eq_true).mp certificate i.val i.isLt
  exact of_decide_eq_true h

theorem allLTTR_fin_complete {n : Nat} {P : Fin n → Prop} [DecidablePred P]
    (all : ∀ i : Fin n, P i) :
    Nat.allLTTR n (fun k hk => decide (P ⟨k, hk⟩)) = true := by
  apply (Nat.allLTTR_eq_true).mpr
  intro k hk
  exact decide_eq_true (all ⟨k, hk⟩)

theorem allLTTR_fin_agrees_with_decide {n : Nat} {P : Fin n → Prop}
    [DecidablePred P] :
    (Nat.allLTTR n (fun k hk => decide (P ⟨k, hk⟩)) = true) ↔
      decide (∀ i : Fin n, P i) = true := by
  constructor
  · intro h
    exact decide_eq_true (allLTTR_fin_sound h)
  · intro h
    exact allLTTR_fin_complete (of_decide_eq_true h)

theorem seven_finite_certificate_positive :
    Nat.allLTTR 7 (fun k _ => decide (k < 7)) = true := by
  apply (allLTTR_fin_complete (P := fun i : Fin 7 => i.val < 7))
  intro i
  exact i.isLt

end NucleusDecide

#print axioms NucleusDecide.isTrue_evaluates_true
#print axioms NucleusDecide.isFalse_evaluates_false
#print axioms NucleusDecide.checked_decide_true_implies_proof
#print axioms NucleusDecide.checked_decide_false_implies_refutation
#print axioms NucleusDecide.finite_domain_isTrue
#print axioms NucleusDecide.raw_true_cannot_certify_arbitrary_prop
#print axioms NucleusDecide.allLTTR_fin_sound
#print axioms NucleusDecide.allLTTR_fin_complete
#print axioms NucleusDecide.allLTTR_fin_agrees_with_decide
#print axioms NucleusDecide.seven_finite_certificate_positive
