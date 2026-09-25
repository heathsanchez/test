import Mathlib

universe u v

namespace MathGraphConsequentialQuotient

/--
A consequence-relative quotient specification.

`rel` records distinctions the protected observer is certified not to see.
The only trust-bearing requirement is `observe_respects`: related source states
must have exactly the same protected consequence.
-/
structure ConsequenceSpec (X : Type u) (Y : Type v) where
  rel : X → X → Prop
  rel_refl : ∀ x, rel x x
  rel_symm : ∀ {x y}, rel x y → rel y x
  rel_trans : ∀ {x y z}, rel x y → rel y z → rel x z
  observe : X → Y
  observe_respects : ∀ {x y}, rel x y → observe x = observe y

def ConsequenceSpec.setoid {X : Type u} {Y : Type v}
    (S : ConsequenceSpec X Y) : Setoid X where
  r := S.rel
  iseqv := ⟨S.rel_refl, S.rel_symm, S.rel_trans⟩

abbrev ConsequenceSpec.Quotient {X : Type u} {Y : Type v}
    (S : ConsequenceSpec X Y) := Quotient S.setoid

def ConsequenceSpec.project {X : Type u} {Y : Type v}
    (S : ConsequenceSpec X Y) (x : X) : S.Quotient :=
  Quotient.mk S.setoid x

noncomputable def ConsequenceSpec.quotientObserve {X : Type u} {Y : Type v}
    (S : ConsequenceSpec X Y) : S.Quotient → Y :=
  Quotient.lift S.observe (fun _ _ h => S.observe_respects h)

@[simp] theorem ConsequenceSpec.quotientObserve_project
    {X : Type u} {Y : Type v} (S : ConsequenceSpec X Y) (x : X) :
    S.quotientObserve (S.project x) = S.observe x := rfl

theorem ConsequenceSpec.project_eq_of_rel
    {X : Type u} {Y : Type v} (S : ConsequenceSpec X Y)
    {x y : X} (h : S.rel x y) :
    S.project x = S.project y :=
  Quotient.sound h

/--
The protected observation factors exactly through the compiled quotient.
This is the executable form of "discard only certified-invisible distinctions".
-/
theorem ConsequenceSpec.factorization
    {X : Type u} {Y : Type v} (S : ConsequenceSpec X Y) :
    S.observe = fun x => S.quotientObserve (S.project x) := by
  funext x
  rfl

end MathGraphConsequentialQuotient
