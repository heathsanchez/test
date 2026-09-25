import Mathlib
import MathGraphConsequentialQuotient

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

noncomputable def observationSpec {X : Type u} {Y : Type v}
    (observe : X → Y) :
    MathGraphConsequentialQuotient.ConsequenceSpec X Y where
  rel := ObservationEq observe
  rel_refl := (observationEq_equivalence observe).1
  rel_symm := (observationEq_equivalence observe).2.1
  rel_trans := (observationEq_equivalence observe).2.2
  observe := observe
  observe_respects := by
    intro x y h
    exact h

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

/-- Every existing ConsequenceSpec relation refines the canonical observation
kernel for its own protected observer. -/
theorem spec_relation_refines_kernel {X : Type u} {Y : Type v}
    (S : MathGraphConsequentialQuotient.ConsequenceSpec X Y) :
    ∀ ⦃x y⦄, S.rel x y → ObservationEq S.observe x y := by
  intro x y h
  exact S.observe_respects h

end MathGraphObservationKernel
