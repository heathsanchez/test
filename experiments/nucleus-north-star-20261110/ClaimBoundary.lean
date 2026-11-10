/-!
  Deliberately synthetic, source-level separation of a checked theorem
  from a strictly stronger intended requirement. Neither proposition is
  asserted to represent any real user's or JPL's intended requirement.
-/
set_option autoImplicit false

namespace NorthStarClaim

-- A correct but deliberately weak proposition: R follows *if assumed*.
theorem checkedTheorem : ∀ (R : Prop), R → R := by
  intro R h
  exact h

-- Constructive evidence: the checked proposition holds while the proposed
-- stronger requirement fails, witnessed by instantiating R := False.
theorem separation : (∀ (R : Prop), R → R) ∧ ¬ (∀ (R : Prop), R) := by
  constructor
  · exact checkedTheorem
  · intro h
    exact h False

#print axioms checkedTheorem
#print axioms separation

end NorthStarClaim
