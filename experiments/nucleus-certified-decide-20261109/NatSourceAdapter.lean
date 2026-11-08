import NucleusDecide

namespace NucleusDecide

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

#print axioms NucleusDecide.allLTTR_fin_sound
#print axioms NucleusDecide.allLTTR_fin_complete
#print axioms NucleusDecide.allLTTR_fin_agrees_with_decide
#print axioms NucleusDecide.seven_finite_certificate_positive
