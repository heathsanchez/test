import Mathlib

/-! Independently checked soundness rules for the frozen certificate language.
These rules are generic in their coefficients, factors and interval endpoints.
They do not import the withheld estimate or any generated certificate. -/
namespace CrossDomainResidual.ProcedureRules

/-- Horner evaluation of a finite coefficient list. -/
def coeffPoly : List ℝ → ℝ → ℝ
  | [], _ => 0
  | a :: as, x => a + x * coeffPoly as x

theorem coeffPoly_sound (cs : List ℝ) :
    (∀ a ∈ cs, 0 ≤ a) → ∀ {x : ℝ}, 0 ≤ x → 0 ≤ coeffPoly cs x := by
  induction cs with
  | nil =>
      intro hc x hx
      simp [coeffPoly]
  | cons a as ih =>
      intro hc x hx
      have ha : 0 ≤ a := hc a (by simp)
      have hs : ∀ b ∈ as, 0 ≤ b := by
        intro b hb
        exact hc b (by simp [hb])
      simpa only [coeffPoly] using add_nonneg ha (mul_nonneg hx (ih hs hx))

/-- A monomial times a nonnegative quadratic square is nonnegative on the ray. -/
theorem halfLineSquare_sound (k : ℕ) (A r D : ℝ)
    (hA : 0 ≤ A) (hD : 0 ≤ D) {x : ℝ} (hx : 0 ≤ x) :
    0 ≤ x ^ k * (A * (x - r) ^ 2 + D) := by
  exact mul_nonneg (pow_nonneg hx _) (add_nonneg (mul_nonneg hA (sq_nonneg _)) hD)

/-- Endpoint checking is sound for every affine function on a compact interval. -/
theorem intervalAffine_sound (a b l u : ℝ)
    (hl : 0 ≤ a * l + b) (hu : 0 ≤ a * u + b)
    {x : ℝ} (hx : l ≤ x ∧ x ≤ u) :
    0 ≤ a * x + b := by
  by_cases ha : 0 ≤ a
  · have h := mul_nonneg ha (sub_nonneg.mpr hx.1)
    nlinarith
  · have h := mul_nonneg (neg_nonneg.mpr (le_of_not_ge ha)) (sub_nonneg.mpr hx.2)
    nlinarith

/-- Soundness is preserved by adding independently certified expressions. -/
theorem sum_sound {a b : ℝ} (ha : 0 ≤ a) (hb : 0 ≤ b) : 0 ≤ a + b :=
  add_nonneg ha hb

/-- Soundness is preserved by multiplying independently certified expressions. -/
theorem product_sound {a b : ℝ} (ha : 0 ≤ a) (hb : 0 ≤ b) : 0 ≤ a * b :=
  mul_nonneg ha hb

#print axioms coeffPoly_sound
#print axioms halfLineSquare_sound
#print axioms intervalAffine_sound
#print axioms sum_sound
#print axioms product_sound
end CrossDomainResidual.ProcedureRules
