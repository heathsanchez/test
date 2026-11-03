set_option autoImplicit false
namespace NucleusReference
universe u
-- Proof irrelevance under an arbitrary dependent local predicate.
theorem dependentFinalProof {C : Type u} {R : C → C → Prop}
    (p q : ∀ x, R x x) (F : ∀ x y, R x y → Prop)
    (a _b : C) (w : F a a (p a)) : F a a (q a) := w

-- The same rule with a nondependent proposition also remains valid.
theorem constantFinalProof {C : Type u} {P : Prop}
    (p q : P) (F : C → C → P → Prop)
    (a b : C) (w : F a b p) : F a b q := w
#print axioms dependentFinalProof
#print axioms constantFinalProof
end NucleusReference
