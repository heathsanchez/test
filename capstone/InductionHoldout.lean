import Std
namespace CapstoneInductionHoldout

def advance (g : Nat → Nat) : Nat → Nat → Nat
  | 0, seed => seed
  | k + 1, seed => advance g k (g seed)

theorem advance_compose (g : Nat → Nat) (a b : Nat) (seed : Nat) :
    advance g (a + b) seed = advance g b (advance g a seed) := by
  induction a with
  | zero => simp [advance]
  | succ a ih => simpa [Nat.succ_add, advance] using ih (g seed)

end CapstoneInductionHoldout
