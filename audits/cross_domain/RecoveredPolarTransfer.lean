import NavierStokes.PolarCharts
import KnownUpper
import RecoveredLower

/-! The target imports no withheld source lower-bound theorem. Its lower
estimate comes from the generated certificate; its upper estimate is the
allowed source capability. This is a new quantitative chart lemma, not a
repair of the original Navier-Stokes blow-up construction. -/
noncomputable section
namespace CrossDomainResidual.RecoveredPolarTransfer
open NavierStokes.PolarCharts

private theorem scalar_angle_bounds {x : ℝ} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x ∧ Real.arctan x ≤ x := by
  constructor
  · convert RecoveredLower.recovered_arctan_lower hx using 1 <;> ring
  · exact KnownUpper.arctan_le_self hx

theorem baseChart_angle_bounds {p : Plane}
    (hx : 0 < p.1) (hy : 0 ≤ p.2) :
    p.2 / p.1 - (p.2 / p.1) ^ 3 / 3 ≤ (baseChart p).2 ∧
    (baseChart p).2 ≤ p.2 / p.1 := by
  simpa only [baseChart, Prod.snd] using
    scalar_angle_bounds (div_nonneg hy hx.le)

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
end CrossDomainResidual.RecoveredPolarTransfer
