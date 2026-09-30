import Collatz.SourceCylinderExit

set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

namespace CollatzFinal.SourceProduct

/-- A shortcut output divisible by three can only have an even predecessor. -/
theorem shortcut_multiple_three_preimage {p y : Nat}
    (hy : y % 3 = 0) (ht : shortcut p = y) : p = 2*y := by
  by_cases hp : p%2 = 0
  · have he : p/2 = y := by simpa only [shortcut, hp, ite_true] using ht
    omega
  · have hodd : p = 2*(p/2)+1 := by omega
    have he : shortcut p = 3*(p/2)+2 := by
      simp only [shortcut, hp, ite_false]
      omega
    rw [ht] at he
    omega

/-- Exact all-depth obstruction to closing a multiple of three at time zero. -/
theorem iter_multiple_three_preimage (k : Nat) {p y : Nat}
    (hy : y%3 = 0) (ht : iter shortcut k p = y) : p = 2^k*y := by
  induction k generalizing p with
  | zero => simpa only [iter, Nat.pow_zero, Nat.one_mul] using ht
  | succ k ih =>
    have hh : shortcut p = 2^k*y := ih (by simpa only [iter] using ht)
    have hm : (2^k*y)%3 = 0 := by simp [Nat.mul_mod, hy]
    have hp := shortcut_multiple_three_preimage hm hh
    rw [hp]
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

theorem multiple_three_no_smaller_start_preimage (k : Nat) {p y : Nat}
    (hy : y%3 = 0) (hlt : p < y) : iter shortcut k p ≠ y := by
  intro ht
  have he := iter_multiple_three_preimage k hy ht
  have hb : y ≤ 2^k*y := by
    induction k with
    | zero => simp
    | succ k ih =>
      rw [Nat.pow_succ]
      have hm : 2^k*2*y = 2*(2^k*y) := by
        simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      rw [hm]
      omega
  omega

def hardSource : Nat := 3294206330938702138381104133963803
def hardRay (t : Nat) : Nat := hardSource + (2^191*27)*t

theorem hard_ray_has_no_smaller_start_preimage (t k p : Nat)
    (hp : p < hardRay t) : iter shortcut k p ≠ hardRay t := by
  apply multiple_three_no_smaller_start_preimage k _ hp
  simp only [hardRay, hardSource, Nat.add_mod, Nat.mul_mod]
  omega

/-- The exact base witness exits at 279; the qualified cylinder is explicitly narrow. -/
theorem hard_source_exit_cylinder (u : Nat) :
    OrdinaryExit (hardSource + 2^279*u)
      (iter shortcut 279 (hardSource + 2^279*u)) := by
  apply ordinary_exit_of_source_cylinder_direct
    (y := 3189501699593601134635187603066116) (q := 176)
  · decide
  · decide
  · decide
  · decide

/-- In the previously studied ray, only t divisible by 2^88 is closed here. -/
theorem hard_ray_exit_subcylinder (u : Nat) :
    OrdinaryExit (hardRay (2^88*u))
      (iter shortcut 279 (hardRay (2^88*u))) := by
  have he : hardRay (2^88*u) = hardSource + 2^279*(27*u) := by
    unfold hardRay
    have hc : (2^191*27 : Nat)*2^88 = 2^279*27 := by decide
    simp only [← Nat.mul_assoc, hc]
  rw [he]
  exact hard_source_exit_cylinder (27*u)

#print axioms shortcut_multiple_three_preimage
#print axioms iter_multiple_three_preimage
#print axioms multiple_three_no_smaller_start_preimage
#print axioms hard_ray_has_no_smaller_start_preimage
#print axioms hard_source_exit_cylinder
#print axioms hard_ray_exit_subcylinder

end CollatzFinal.SourceProduct
