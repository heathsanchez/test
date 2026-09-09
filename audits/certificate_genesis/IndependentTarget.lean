import Mathlib

/-! Independent mathematical truth check. This module imports neither the
synthesis result nor the source lower-bound theorem. -/
namespace CrossDomainResidual.IndependentTarget

 theorem angle_gt_seven_tenths :
    (7 / 10 : ℝ) < Real.arctan 1 := by
  rw [Real.arctan_one]
  have h := Real.pi_gt_three
  linarith

#print axioms angle_gt_seven_tenths
end CrossDomainResidual.IndependentTarget
