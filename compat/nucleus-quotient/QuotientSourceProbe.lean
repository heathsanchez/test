import Lean

namespace QuotientSourceProbe

universe u

def wrappedMk {α : Sort u} (r : α → α → Prop) (a : α) : Quot r :=
  (fun x => Quot.mk r x) a

theorem indirect_beta {α : Sort u} (r : α → α → Prop)
    (f : α → Nat)
    (respects : ∀ a b : α, r a b → f a = f b)
    (a : α) :
    Quot.lift f respects (wrappedMk r a) = f a := by
  rfl

end QuotientSourceProbe
