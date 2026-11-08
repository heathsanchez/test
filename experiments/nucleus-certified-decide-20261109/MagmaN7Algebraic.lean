import Init

/-!
SOURCE-QUALIFIED COUNTERFACTUAL ONLY.
The original Arena export is unchanged, with its expensive decide proof.
This file reconstructs the same source definitions but provides an explicit
algebraic proof of EquationLHS. It cannot count as an original Arena ACCEPT.
-/

/-- The binary magma operation, written ◇. -/
class Magma (α : Type _) where
  op : α → α → α

@[inherit_doc] infix:65 " ◇ " => Magma.op

@[reducible] def EquationLHS (G : Type _) [Magma G] : Prop :=
  ∀ (x : G) (y : G) (z : G) (w : G) (u : G),
    x ◇ y = z ◇ (w ◇ u)

@[reducible] def EquationRHS (G : Type _) [Magma G] : Prop :=
  ∀ (x : G), x = x ◇ x

abbrev Goal : Prop :=
  ∃ (G : Type) (_ : Magma G), EquationLHS G ∧ ¬ EquationRHS G

namespace countermodel

def op (x y : Fin 7) : Fin 7 :=
  ⟨Nat.mod (Nat.add (Nat.mul 0 x.val) (Nat.mul 0 y.val)) 7, Nat.mod_lt _ (by decide)⟩

instance inst : Magma (Fin 7) := ⟨op⟩

end countermodel

-- Fresh proof term for the same proposition. Frozen original is untouched.
def algebraicCountermodel : Goal := by
  refine ⟨Fin 7, countermodel.inst, ?_⟩
  constructor
  · intro x y z w u
    change countermodel.op x y = countermodel.op z (countermodel.op w u)
    apply Fin.ext
    simp [countermodel.op]
  · intro h
    exact (of_decide_eq_false rfl) (h (1 : Fin 7))

#print axioms algebraicCountermodel
