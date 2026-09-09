import Mathlib
import ProgramRules

namespace OpenDevelopment.TypedProgramSemantics
open ProgramRules

def o2 : Program := .product (.affine (-1) 1) (.affine 1 1)
def o3 : Program := .product (.affine (-1) 3) (.affine 1 (-2))

theorem o2_valid : Valid (.interval 0 1) o2 := by
  norm_num [o2, Valid]

theorem o3_valid : Valid (.interval 2 3) o3 := by
  norm_num [o3, Valid]

theorem o2_commutes (x : ℝ) : eval o2 x = 1 - x ^ 2 := by
  simp [o2, eval]
  ring

theorem o3_commutes (x : ℝ) : eval o3 x = -6 + 5 * x - x ^ 2 := by
  simp [o3, eval]
  ring

theorem o2_sound {x : ℝ} (hx : 0 ≤ x ∧ x ≤ 1) : 0 ≤ 1 - x ^ 2 := by
  rw [← o2_commutes]
  exact sound o2 (.interval 0 1) x o2_valid hx

theorem o3_sound {x : ℝ} (hx : 2 ≤ x ∧ x ≤ 3) : 0 ≤ -6 + 5 * x - x ^ 2 := by
  rw [← o3_commutes]
  exact sound o3 (.interval 2 3) x o3_valid hx

#print axioms o2_commutes
#print axioms o3_commutes
#print axioms o2_sound
#print axioms o3_sound
end OpenDevelopment.TypedProgramSemantics
