import Mathlib
import ProgramRules

namespace OpenDevelopment.TypedProgramSemantics
open ProgramRules

def o2 : Program := .product (.affine (-1) 1) (.affine 1 1)
def o3 : Program := .product (.affine (-1) 3) (.affine 1 (-2))
def acquiredO3 : Program := .product (.monomial 1 1) o2
def o4 : Program := .product (.monomial 1 1)
  (.product (.affine (-1) 2) (.affine 1 1))

theorem o2_valid : Valid (.interval 0 1) o2 := by
  norm_num [o2, Valid]

theorem o3_valid : Valid (.interval 2 3) o3 := by
  norm_num [o3, Valid]

theorem acquiredO3_valid : Valid (.interval 0 1) acquiredO3 := by
  norm_num [acquiredO3, o2, Valid, NonnegativeDomain]

theorem o4_valid : Valid (.interval 0 1) o4 := by
  norm_num [o4, Valid, NonnegativeDomain]

theorem o2_commutes (x : ℝ) : eval o2 x = 1 - x ^ 2 := by
  simp [o2, eval]
  ring

theorem o3_commutes (x : ℝ) : eval o3 x = -6 + 5 * x - x ^ 2 := by
  simp [o3, eval]
  ring

theorem acquiredO3_commutes (x : ℝ) : eval acquiredO3 x = x - x ^ 3 := by
  simp [acquiredO3, o2, eval]
  ring

theorem o4_commutes (x : ℝ) : eval o4 x = 2*x + x^2 - x^3 := by
  simp [o4, eval]
  ring

theorem o2_sound {x : ℝ} (hx : 0 ≤ x ∧ x ≤ 1) : 0 ≤ 1 - x ^ 2 := by
  rw [← o2_commutes]
  exact sound o2 (.interval 0 1) x o2_valid hx

theorem o3_sound {x : ℝ} (hx : 2 ≤ x ∧ x ≤ 3) : 0 ≤ -6 + 5 * x - x ^ 2 := by
  rw [← o3_commutes]
  exact sound o3 (.interval 2 3) x o3_valid hx

theorem acquiredO3_sound {x : ℝ} (hx : 0 ≤ x ∧ x ≤ 1) : 0 ≤ x - x ^ 3 := by
  rw [← acquiredO3_commutes]
  exact sound acquiredO3 (.interval 0 1) x acquiredO3_valid hx

theorem o4_sound {x : ℝ} (hx : 0 ≤ x ∧ x ≤ 1) : 0 ≤ 2*x + x^2 - x^3 := by
  rw [← o4_commutes]
  exact sound o4 (.interval 0 1) x o4_valid hx

#print axioms o2_commutes
#print axioms o3_commutes
#print axioms o2_sound
#print axioms o3_sound
#print axioms acquiredO3_commutes
#print axioms o4_commutes
#print axioms acquiredO3_sound
#print axioms o4_sound
end OpenDevelopment.TypedProgramSemantics
