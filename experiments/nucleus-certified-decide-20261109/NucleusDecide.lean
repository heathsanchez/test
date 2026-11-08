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
  | isFalse _ => simp at h

theorem checked_decide_false_implies_refutation {P : Prop} (d : Decidable P)
    (h : @decide P d = false) : ¬ P := by
  cases d with
  | isTrue _ => simp at h
  | isFalse refutation => exact refutation

theorem finite_domain_isTrue {n : Nat} {P : Fin n → Prop}
    (proof : ∀ i : Fin n, P i) :
    @decide (∀ i : Fin n, P i) (Decidable.isTrue proof) = true := by
  rfl

theorem raw_true_cannot_certify_arbitrary_prop :
    ¬ (∀ P : Prop, True → P) := by
  intro claim
  exact claim False True.intro

end NucleusDecide

#print axioms NucleusDecide.checked_decide_true_implies_proof
#print axioms NucleusDecide.finite_domain_isTrue
#print axioms NucleusDecide.raw_true_cannot_certify_arbitrary_prop
