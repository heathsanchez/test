import C76Eta

/- A false ACCEPT if η-conversion silently equates unrelated closures. -/
example (f g : Nat → Nat) : (fun x : Nat => f x) = g := by
  rfl
