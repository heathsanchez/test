import NavierStokes.PolarCharts
import ABAngleBounds

/-! A held-out quantitative estimate on the actual OpenAI polar-chart
interface. The source capability is the Alpöge–Buckmaster arctangent bound,
transcribed and independently checked in ABAngleBounds. This does not claim
that the original OpenAI construction needed this estimate or that it
improves the blow-up argument. -/
noncomputable section
namespace CrossDomainResidual.PolarChartTransfer
open NavierStokes.PolarCharts

private theorem scalar_angle_bounds {x : ℝ} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x ∧ Real.arctan x ≤ x :=
  ⟨ABAngleBounds.self_sub_cube_le_arctan hx, ABAngleBounds.arctan_le_self hx⟩

/-- A new two-sided quantitative estimate on the source's genuine chart. -/
theorem baseChart_angle_bounds {p : Plane}
    (hx : 0 < p.1) (hy : 0 ≤ p.2) :
    p.2 / p.1 - (p.2 / p.1) ^ 3 / 3 ≤ (baseChart p).2 ∧
    (baseChart p).2 ≤ p.2 / p.1 := by
  simpa only [baseChart, Prod.snd] using
    scalar_angle_bounds (div_nonneg hy hx.le)

/-- Held-out transfer to all four of the actual rotated local charts. -/
theorem localChart_angle_bounds (j : Index) {p : Plane}
    (hx : 0 < (rotate j p).1) (hy : 0 ≤ (rotate j p).2) :
    (rotate j p).2 / (rotate j p).1 -
        ((rotate j p).2 / (rotate j p).1) ^ 3 / 3 ≤
      (localChart j p).2 - offset j ∧
    (localChart j p).2 - offset j ≤
      (rotate j p).2 / (rotate j p).1 := by
  have h := baseChart_angle_bounds (p := rotate j p) hx hy
  simpa only [localChart_apply, Prod.snd, add_sub_cancel_right,
    radius_rotate, baseChart, Prod.snd] using h

#print axioms baseChart_angle_bounds
#print axioms localChart_angle_bounds
end CrossDomainResidual.PolarChartTransfer
