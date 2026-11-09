set_option autoImplicit false

namespace NorthStar

axiom P : Prop
axiom Q : Prop
axiom givenQ : Q
axiom implication : Q → P

-- Valid in the assumed environment, not an unconditional proof of P.
theorem dependent : P := implication givenQ

-- The assumption lineage must survive another theorem's use of dependent.
theorem borrowed : P := dependent

-- No user axiom is needed for this proposition.
theorem independent : ∀ (R : Prop), R → R := by
  intro R h
  exact h

#print axioms dependent
#print axioms borrowed
#print axioms independent

end NorthStar
