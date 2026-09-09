import EulerBlowup.Elementary
import RecoveredLower

/-! Post-recovery validation only. The generated proof has already been
frozen and checked in the OpenAI target environment before this module runs.
These implications compare exact statements; they do not establish that the
source theorem was unknown to the experimenter or absent from Mathlib. -/
noncomputable section
namespace CrossDomainResidual.RecoveredSourceCheck

theorem recovered_implies_source {x : ℝ} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x := by
  convert RecoveredLower.recovered_arctan_lower hx using 1 <;> ring

theorem source_implies_recovered {x : ℝ} (hx : 0 ≤ x) :
    x - x ^ 3 / 3 ≤ Real.arctan x :=
  EulerBlowup.self_sub_cube_le_arctan hx

#print axioms recovered_implies_source
#print axioms source_implies_recovered
end CrossDomainResidual.RecoveredSourceCheck
