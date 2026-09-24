import VeriTile.Triton.Math.Softmax

open scoped BigOperators

namespace MathGraphShiftCapability

/--
A consequence-sized capability compiled from the stable-softmax seed:
a normalized exponentially weighted finite quotient is invariant under a
common real-valued shift.

This deliberately contains no Triton AST, kernel scheduler, GPU model, or
VeriTile benchmark-specific symbol.
-/
theorem weighted_shift_invariant {S D : Nat}
    (qk : Fin S → ℝ) (v : Fin S → Fin D → ℝ) (d : Fin D) (M₁ M₂ : ℝ) :
    (∑ n : Fin S, Real.exp (qk n - M₁) * v n d) /
        (∑ n : Fin S, Real.exp (qk n - M₁))
      =
    (∑ n : Fin S, Real.exp (qk n - M₂) * v n d) /
        (∑ n : Fin S, Real.exp (qk n - M₂)) := by
  have hnum : ∀ M : ℝ,
      (∑ n : Fin S, Real.exp (qk n - M) * v n d)
        = Real.exp (-M) * ∑ n : Fin S, Real.exp (qk n) * v n d := by
    intro M
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl (fun n _ => ?_)
    rw [← mul_assoc, ← Real.exp_add]
    ring_nf
  have hden : ∀ M : ℝ,
      (∑ n : Fin S, Real.exp (qk n - M))
        = Real.exp (-M) * ∑ n : Fin S, Real.exp (qk n) := by
    intro M
    rw [Finset.mul_sum]
    refine Finset.sum_congr rfl (fun n _ => ?_)
    rw [← Real.exp_add]
    ring_nf
  rw [hnum M₁, hden M₁, hnum M₂, hden M₂]
  rw [mul_div_mul_left _ _ (Real.exp_ne_zero (-M₁))]
  rw [mul_div_mul_left _ _ (Real.exp_ne_zero (-M₂))]

end MathGraphShiftCapability
