import EulerBlowup.Elementary
import RecoveredProcedures
import HeldoutProcedure

noncomputable section
namespace CrossDomainResidual.ProcedureSourceCheck

/-- The generated estimate dominates the source cubic bound on this ray. -/
theorem quadratic_stronger_on {x : ℝ} (hx : 3 / 4 ≤ x) :
    x - x ^ 3 / 3 ≤ x - x ^ 2 / 4 := by
  have h0 : 0 ≤ x ^ 2 := sq_nonneg x
  have h1 : 0 ≤ 4 * x - 3 := by linarith
  nlinarith [mul_nonneg h0 h1]

theorem recovered_implies_source_on {x : ℝ} (hx : 3 / 4 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x := by
  have h0 : 0 ≤ x := by linarith
  exact (quadratic_stronger_on hx).trans (ProcedureRepair.recovered_lower h0)

theorem original_source_check {x : ℝ} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x :=
  EulerBlowup.self_sub_cube_le_arctan hx

theorem strict_improvement_at_one :
    (1 : ℝ) - 1 ^ 3 / 3 < 1 - 1 ^ 2 / 4 := by norm_num

#print axioms quadratic_stronger_on
#print axioms recovered_implies_source_on
#print axioms original_source_check
#print axioms strict_improvement_at_one
end CrossDomainResidual.ProcedureSourceCheck
