import Init

/-!
This theorem refutes the *universal identification* of a successor neutral
with an arbitrary independent Nat variable. It does NOT claim every
instantiation of the two is unequal, nor invalidate the original source
theorem; it falsifies a proposed unchecked conversion axiom.
-/
namespace NucleusStage16RigidNeutral

theorem succ_zero_ne_zero : Nat.succ 0 ≠ 0 := by decide

theorem no_universal_succ_free :
    ¬ (∀ (a b : Nat), Nat.succ a = b) := by
  intro h
  have absurd : Nat.succ 0 = 0 := h 0 0
  cases absurd

end NucleusStage16RigidNeutral
