import Std

/- A source-distinct proof-planning target: iteration composition.
   Induction over m requires an induction hypothesis polymorphic in x,
   since the successor obligation uses x := f x.
   This is a protected Lean theorem, not a synthesized repair operator. -/

namespace CapstoneInduction

def iterate (f : Nat → Nat) : Nat → Nat → Nat
  | 0, x => x
  | n + 1, x => iterate f n (f x)

theorem iterate_add (f : Nat → Nat) (m n : Nat) (x : Nat) :
    iterate f (m + n) x = iterate f n (iterate f m x) := by
  induction m generalizing x with
  | zero =>
      simp [iterate]
  | succ m ih =>
      simpa [Nat.succ_add, iterate] using ih (f x)

end CapstoneInduction
