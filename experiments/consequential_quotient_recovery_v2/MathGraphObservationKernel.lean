import Mathlib
universe u v

namespace MathGraphObservationKernel

def ObservationEq {X : Type u} {Y : Type v}
    (observe : X → Y) (x y : X) : Prop :=
  observe x = observe y

theorem observationEq_equivalence {X : Type u} {Y : Type v}
    (observe : X → Y) : Equivalence (ObservationEq observe) := by
  refine ⟨?_, ?_, ?_⟩
  · intro x
    rfl
  · intro x y h
    exact h.symm
  · intro x y z hxy hyz
    exact hxy.trans hyz

def observationSetoid {X : Type u} {Y : Type v}
    (observe : X → Y) : Setoid X where
  r := ObservationEq observe
  iseqv := observationEq_equivalence observe

/-- A relation is safe for the declared protected observation if it never
identifies states whose protected observations differ. -/
def SafeRelation {X : Type u} {Y : Type v}
    (observe : X → Y) (R : X → X → Prop) : Prop :=
  ∀ ⦃x y⦄, R x y → ObservationEq observe x y

/--
Static MSI universal property: observation equality is the greatest safe
relation, hence its quotient is the coarsest state representation preserving
the declared protected observation.
-/
theorem observationEq_greatest_safe {X : Type u} {Y : Type v}
    (observe : X → Y) {R : X → X → Prop}
    (hR : SafeRelation observe R) :
    ∀ ⦃x y⦄, R x y → ObservationEq observe x y := by
  intro x y hxy
  exact hR hxy

end MathGraphObservationKernel
