import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/-!
V116. Exact three-step (odd,odd,even) shortcut block. This is a
bounded-prefix separator, not a Collatz proof. The unrestricted
high-endpoint-precision ⇒ source-cap claim is not used.
-/

/-- The genuine shortcut trace is
8q+3 -> 12q+5 -> 18q+8 -> 9q+4. -/
theorem triple_110_step1 (q : Nat) :
    shortcut (8*q+3) = 12*q+5 := by
  have h : (8*q+3)%2 ≠ 0 := by omega
  simp only [shortcut, h, ite_false]
  omega

theorem triple_110_step2 (q : Nat) :
    shortcut (12*q+5) = 18*q+8 := by
  have h : (12*q+5)%2 ≠ 0 := by omega
  simp only [shortcut, h, ite_false]
  omega

theorem triple_110_step3 (q : Nat) :
    shortcut (18*q+8) = 9*q+4 := by
  have h : (18*q+8)%2 = 0 := by omega
  simp only [shortcut, h, ite_true]
  omega

theorem triple_110 (q : Nat) :
    iter shortcut 3 (8*q+3) = 9*q+4 := by
  change shortcut (shortcut (shortcut (8*q+3))) = _
  rw [triple_110_step1, triple_110_step2, triple_110_step3]

/-- Three genuine steps increase the positive source,
although the last step is even. -/
theorem triple_110_ascends (q : Nat) :
    8*q+3 < iter shortcut 3 (8*q+3) := by
  rw [triple_110]
  omega

/-- The exact centre for the recurring 110 affine block is -5.
The formula 8*(T^3(x)+5)=9*(x+5) holds on the lawful cylinder. -/
theorem triple_110_center (q : Nat) :
    8 * (iter shortcut 3 (8*q+3) + 5) =
       9 * (8*q+3+5) := by
  rw [triple_110]
  omega

theorem signed_block_fixed_centre (x : Int) :
    8*x = 9*x+5 ↔ x = -5 := by
  constructor <;> intro h <;> omega

/-- Already for a whole genuine 110 block, assuming the ORIGINAL
source is not 2 mod 3, the first three endpoints cannot produce
a strictly smaller source through the canonical odd inverse cone.
This is FINITE PREFIX information, not an infinite bar. -/
theorem triple_110_no_capped_ternary_prefix
    (q : Nat) (hmod : (8*q+3)%3 ≠ 2)
    (j t : Nat) (hj : j ≤ 3)
    (hy : iter shortcut j (8*q+3) = 3*t+2) :
    8*q+3 ≤ 2*t+1 := by
  have h0 : iter shortcut 0 (8*q+3) = 8*q+3 := rfl
  have h1 : iter shortcut 1 (8*q+3) = 12*q+5 := by
    change shortcut (8*q+3) = _
    exact triple_110_step1 q
  have h2 : iter shortcut 2 (8*q+3) = 18*q+8 := by
    change shortcut (shortcut (8*q+3)) = _
    rw [triple_110_step1, triple_110_step2]
  have h3 := triple_110 q
  have cases : j=0 ∨ j=1 ∨ j=2 ∨ j=3 := by omega
  rcases cases with h | h | h | h
  · rw [h, h0] at hy
    have hc : (8*q+3)%3 = 2 := by omega
    exact False.elim (hmod hc)
  · rw [h, h1] at hy
    omega
  · rw [h, h2] at hy
    omega
  · rw [h, h3] at hy
    omega

#print axioms triple_110
#print axioms triple_110_ascends
#print axioms triple_110_center
#print axioms signed_block_fixed_centre
#print axioms triple_110_no_capped_ternary_prefix

end SourceProduct
end CollatzFinal
