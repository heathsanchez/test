import NavierStokes.PolarCharts
import KnownUpper
import RecoveredProcedures

/-! A quantitative chart consequence, not a missing blow-up lemma. -/
noncomputable section
namespace CrossDomainResidual.ProcedurePolarTransfer
open NavierStokes.PolarCharts

private theorem scalar_angle_bounds {x : ℝ} (hx : 0 ≤ x) :
    x - x ^ 2 / 4 ≤ Real.arctan x ∧ Real.arctan x ≤ x := by
  constructor
  · exact ProcedureRepair.recovered_lower hx
  · exact KnownUpper.arctan_le_self hx

theorem baseChart_angle_bounds {p : Plane}
    (hx : 0 < p.1) (hy : 0 ≤ p.2) :
    p.2 / p.1 - (p.2 / p.1) ^ 2 / 4 ≤ (baseChart p).2 ∧
    (baseChart p).2 ≤ p.2 / p.1 := by
  simpa only [baseChart, Prod.snd] using
    scalar_angle_bounds (div_nonneg hy hx.le)

theorem localChart_angle_bounds (j : Index) {p : Plane}
    (hx : 0 < (rotate j p).1) (hy : 0 ≤ (rotate j p).2) :
    (rotate j p).2 / (rotate j p).1 -
        ((rotate j p).2 / (rotate j p).1) ^ 2 / 4 ≤
      (localChart j p).2 - offset j ∧
    (localChart j p).2 - offset j ≤
      (rotate j p).2 / (rotate j p).1 := by
  have h := baseChart_angle_bounds (p := rotate j p) hx hy
  simpa only [localChart_apply, Prod.snd, add_sub_cancel_right,
    radius_rotate, baseChart, Prod.snd] using h

theorem recovered_angle_gt_seven_tenths :
    (7 / 10 : ℝ) < Real.arctan 1 := by
  have h := ProcedureRepair.recovered_lower (show (0 : ℝ) ≤ 1 by norm_num)
  norm_num at h
  rw [Real.arctan_one]
  linarith

#print axioms baseChart_angle_bounds
#print axioms localChart_angle_bounds
#print axioms recovered_angle_gt_seven_tenths
end CrossDomainResidual.ProcedurePolarTransfer
