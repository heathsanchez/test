import Init

/-!
C76 source-separator model: the original NDJSON body of Expr7369 has
App(BVar2,BVar0), while C74 standard event28 supplies a BVar1.
Under the SAME actual captured environment, a lambda with that shape can
η-contract to its owning function. This does NOT establish equality across
C74's different captured contexts. This file is independent of that claim.
-/

namespace C76Eta

theorem same_context_eta {α β : Type} (f : α → β) :
    (fun x : α => f x) = f := by
  rfl

theorem transported_eta {α β : Type} (f g : α → β)
    (context_warrant : f = g) :
    (fun x : α => f x) = g := by
  cases context_warrant
  rfl

theorem different_context_not_eta :
    (fun x : Nat => (fun _ : Nat => 0) x) ≠ (fun _ : Nat => 1) := by
  intro eq
  have contradiction : (0 : Nat) = 1 :=
    congrArg (fun fn : Nat → Nat => fn 0) eq
  cases contradiction

#print axioms C76Eta.same_context_eta
#print axioms C76Eta.transported_eta
#print axioms C76Eta.different_context_not_eta
