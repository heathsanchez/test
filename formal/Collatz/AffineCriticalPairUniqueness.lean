import Collatz.ParityCollisionBridge

namespace CollatzFinal
namespace SourceProduct

/-!
Among the odd-prefix equivariant affine maps F_a(n)=a*n+(a-1)
with odd positive coefficient a, the only maps that coalesce after the
*same two-step even-odd boundary for ALL eligible sources* are
a=1 (identity) and a=3 (V115's nontrivial transform).

The universal necessity needs only the test source n=2.
This rules out a redundant finite search over larger multipliers
for this SAME local critical-pair rule. It does not exclude other
longer-word collisions or prove any universal Collatz exit.
-/

/-- For an odd positive a, F_a(2)=3*a-1. If the required
two-step collision occurs there, a is 1 or 3. -/
theorem odd_affine_collision_at_two_necessary
    (a : Nat) (ha : a % 2 = 1)
    (h : iter shortcut 2 (3 * a - 1) = 2) :
    a = 1 ∨ a = 3 := by
  let k := a / 2
  have haForm : a = 2 * k + 1 := by
    dsimp [k]
    omega
  have hstart : 3 * a - 1 = 2 * (3 * k + 1) := by
    rw [haForm]
    omega
  have hfirst : shortcut (3 * a - 1) = 3 * k + 1 := by
    rw [hstart]
    exact shortcut_double_predecessor (3 * k + 1)
  have hsecond : shortcut (3 * k + 1) = 2 := by
    simpa [iter, hfirst] using h
  by_cases heven : (3 * k + 1) % 2 = 0
  · have hdiv : (3 * k + 1) / 2 = 2 := by
      simpa [shortcut, heven] using hsecond
    right
    rw [haForm]
    omega
  · have hdiv : (3 * (3 * k + 1) + 1) / 2 = 2 := by
      simpa [shortcut, heven] using hsecond
    left
    rw [haForm]
    omega

/-- The two possible affine coefficients at the n=2 critical pair
are exactly the identity a=1 and V115's a=3. -/
theorem odd_affine_collision_at_two_iff
    (a : Nat) (ha : a % 2 = 1) :
    iter shortcut 2 (3 * a - 1) = 2 ↔ (a = 1 ∨ a = 3) := by
  constructor
  · exact odd_affine_collision_at_two_necessary a ha
  · intro h
    rcases h with rfl | rfl
    · decide
    · decide

/-- A UNIVERSAL two-step even→odd synchronization requirement
implies that a=1 or a=3. This is only a restriction on a narrowly
defined affine transport schema. -/
theorem universal_two_step_odd_affine_transport_unique
    (a : Nat) (ha : a % 2 = 1)
    (h :
      ∀ n : Nat,
        n % 2 = 0 →
        (shortcut n) % 2 = 1 →
        iter shortcut 2 (a * n + (a - 1)) = iter shortcut 2 n) :
    a = 1 ∨ a = 3 := by
  have h2 : iter shortcut 2 (a * 2 + (a - 1)) =
      iter shortcut 2 2 :=
    h 2 (by decide) (by decide)
  have hpos : 0 < a := by omega
  have hEq : a * 2 + (a - 1) = 3 * a - 1 := by omega
  have htarget : iter shortcut 2 (3 * a - 1) = 2 := by
    rw [hEq] at h2
    have ht : iter shortcut 2 2 = 2 := by decide
    simpa [ht] using h2
  exact odd_affine_collision_at_two_necessary a ha htarget

#print axioms odd_affine_collision_at_two_necessary
#print axioms odd_affine_collision_at_two_iff
#print axioms universal_two_step_odd_affine_transport_unique

end SourceProduct
end CollatzFinal
