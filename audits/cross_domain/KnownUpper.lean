import Mathlib

/-! The allowed upper-bound capability, transcribed from
tristanbuckmaster/fluid_lean@d0124689230b58b4f86e7b90ac59de06404b3b6,
EulerBlowup/Elementary.lean. The withheld lower theorem is not imported. -/
noncomputable section
namespace CrossDomainResidual.KnownUpper
open Real Set

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

#print axioms arctan_le_self
end CrossDomainResidual.KnownUpper
