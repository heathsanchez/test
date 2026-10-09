/-!
Proof of the exact Nat.sub successor definitional computation in the pinned Lean kernel.
This file does not modify Nucleus or accept any Arena input.
-/
set_option autoImplicit false
namespace NucleusSubSuccWitness
theorem sub_succ_rfl (a b : Nat) :
    Nat.sub a (Nat.succ b) = Nat.pred (Nat.sub a b) := by
  rfl
theorem sub_zero_rfl (a : Nat) : Nat.sub a 0 = a := by
  rfl
theorem nat_hsub_alias_rfl (a b : Nat) :
    (a - b) = Nat.sub a b := by
  rfl
theorem hsub_succ_rfl (a b : Nat) :
    (a - Nat.succ b) = Nat.pred (Nat.sub a b) := by
  rfl
theorem false_quotient_separator :
    Nat.sub 2 (Nat.succ 0) ≠ Nat.sub 2 0 := by
  decide
end NucleusSubSuccWitness
