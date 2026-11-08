import Init

/-!
C79 source-pinned Lean 4.34.1 decidable_of_decidable_of_iff transport.
The original implementation uses if hp : p and recursor reductions;
the newer Lean 4.36 Decidable representation is NOT admissible here.

These lemmas establish conditional source semantics, not arbitrary
definitional equality between unrelated Decidable instances.
-/

namespace C79Transport

theorem actual_source_transport_true {p q : Prop}
    (equiv : p ↔ q) (hp : p) :
    @decidable_of_decidable_of_iff p q (Decidable.isTrue hp) equiv =
      Decidable.isTrue (equiv.mp hp) := by
  rfl

theorem actual_source_transport_false {p q : Prop}
    (equiv : p ↔ q) (hn : ¬ p) :
    @decidable_of_decidable_of_iff p q (Decidable.isFalse hn) equiv =
      Decidable.isFalse (fun hq => absurd (equiv.mpr hq) hn) := by
  rfl

theorem original_transport_preserves_decide {p q : Prop}
    (equiv : p ↔ q) (decision : Decidable p) :
    @decide q (@decidable_of_decidable_of_iff p q decision equiv) =
      @decide p decision := by
  cases decision with
  | isTrue hp => rfl
  | isFalse hn => rfl

#print axioms C79Transport.actual_source_transport_true
#print axioms C79Transport.actual_source_transport_false
#print axioms C79Transport.original_transport_preserves_decide
