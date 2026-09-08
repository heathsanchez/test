import Mathlib

/-! Source-derived capability. The three proof bodies below are transcribed
from tristanbuckmaster/fluid_lean, commit d0124689230b58b4f86e7b90ac59de06404b3b6b,
euler-blowup/EulerBlowup/Elementary.lean, blob
5814b45a6fc141985c5bc59a7152ef98f8c0c6e6.
The independent source check imports EulerBlowup.Elementary itself. This copy
is isolated so the target can check it without changing either upstream's
manifest. No new fluid theorem is claimed by this extraction. -/
noncomputable section
open Real Set
namespace CrossDomainResidual.ABAngleBounds

theorem arctan_le_self {x : ℝ} (hx : 0 ≤ x) : arctan x ≤ x := by
  have hmono : Monotone (fun x : ℝ => x - arctan x) := by
    apply monotone_of_deriv_nonneg
    · exact differentiable_id.sub differentiable_arctan
    · intro y
      have hd : deriv (fun x : ℝ => x - arctan x) y = 1 - 1 / (1 + y ^ 2) :=
        ((hasDerivAt_id y).sub (hasDerivAt_arctan y)).deriv
      rw [hd]
      have h1 : 0 < 1 + y ^ 2 := by positivity
      rw [sub_nonneg, div_le_one h1]
      nlinarith [sq_nonneg y]
  have h := hmono hx
  simp only [sub_self, arctan_zero, sub_nonneg] at h
  exact h

theorem self_sub_cube_le_arctan {x : ℝ} (hx : 0 ≤ x) : x - x ^ 3 / 3 ≤ arctan x := by
  have hmono : Monotone (fun x : ℝ => arctan x - (x - x ^ 3 / 3)) := by
    apply monotone_of_deriv_nonneg
    · exact differentiable_arctan.sub (by fun_prop)
    · intro y
      have hd : deriv (fun x : ℝ => arctan x - (x - x ^ 3 / 3)) y = 1 / (1 + y ^ 2) - (1 - y ^ 2) := by
        have h2 : HasDerivAt (fun x : ℝ => x - x ^ 3 / 3) (1 - y ^ 2) y := by
          have h3 : HasDerivAt (fun x : ℝ => x ^ 3 / 3) ((3 : ℕ) * y ^ (3 - 1) / 3) y :=
            (hasDerivAt_pow 3 y).div_const 3
          have h4 := (hasDerivAt_id' y).sub h3
          have h5 : (1 : ℝ) - (3 : ℕ) * y ^ (3 - 1) / 3 = 1 - y ^ 2 := by push_cast; ring
          rw [h5] at h4
          exact h4
        exact ((hasDerivAt_arctan y).sub h2).deriv
      rw [hd]
      have h1 : 0 < 1 + y ^ 2 := by positivity
      rw [sub_nonneg, le_div_iff₀ h1]
      nlinarith [sq_nonneg y, sq_nonneg (y ^ 2)]
  have h := hmono hx
  simp only [arctan_zero] at h
  norm_num at h
  linarith

theorem tilt_from_stretch {ψ₀ G : ℝ} (hψ : 0 < ψ₀) (hG : 0 < G) :
    1 / G - ψ₀ ^ 2 / (3 * G ^ 3) ≤ arctan (ψ₀ / G) / ψ₀ ∧ arctan (ψ₀ / G) / ψ₀ ≤ 1 / G := by
  have hx : 0 ≤ ψ₀ / G := by positivity
  constructor
  · rw [le_div_iff₀ hψ]
    have h := self_sub_cube_le_arctan hx
    calc (1 / G - ψ₀ ^ 2 / (3 * G ^ 3)) * ψ₀ = ψ₀ / G - (ψ₀ / G) ^ 3 / 3 := by
          field_simp
      _ ≤ arctan (ψ₀ / G) := h
  · rw [div_le_iff₀ hψ]
    have h := arctan_le_self hx
    calc arctan (ψ₀ / G) ≤ ψ₀ / G := h
      _ = 1 / G * ψ₀ := by field_simp

end CrossDomainResidual.ABAngleBounds
