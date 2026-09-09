import Mathlib

namespace OpenDevelopment.ProcedureRules

theorem intervalAffine_sound (a b l u : ℝ)
    (hl : 0 ≤ a * l + b) (hu : 0 ≤ a * u + b)
    {x : ℝ} (hx : l ≤ x ∧ x ≤ u) : 0 ≤ a * x + b := by
  by_cases ha : 0 ≤ a
  · have h := mul_nonneg ha (sub_nonneg.mpr hx.1)
    nlinarith
  · have h := mul_nonneg (neg_nonneg.mpr (le_of_not_ge ha)) (sub_nonneg.mpr hx.2)
    nlinarith

theorem product_sound {a b : ℝ} (ha : 0 ≤ a) (hb : 0 ≤ b) : 0 ≤ a * b :=
  mul_nonneg ha hb

#print axioms intervalAffine_sound
#print axioms product_sound
end OpenDevelopment.ProcedureRules
