import Collatz.BackwardParameterCover
set_option maxRecDepth 100000
set_option maxHeartbeats 1000000
namespace CollatzFinal.SourceProduct
theorem backward_cell_exit_0 (u : Nat) : OrdinaryExit (familySource 3 2 u) (iter shortcut 61 (familySource 3 2 u)) := by
  have hx := ordinary_exit_of_source_cylinder_odd_merge (n := 11385388088368765599771) (k := 61) (q := 37) (y := 6669999212475107563466) (p := 4446666141650071708977) (by decide) (by decide) (by decide) (by decide) (by decide) (by decide) (6561 * u)
  have heq : familySource 3 2 u = 11385388088368765599771 + 2 ^ 61 * (6561 * u) := by
    unfold familySource
    simp only [Nat.mul_add]
    omega
  rw [heq]
  exact hx
#print axioms backward_cell_exit_0
theorem backward_cell_exit_1 (u : Nat) : OrdinaryExit (familySource 0 3 u) (iter shortcut 62 (familySource 0 3 u)) := by
  have hx := ordinary_exit_of_source_cylinder_odd_merge (n := 38911100780481085467) (k := 62) (q := 38) (y := 34193434103597612279) (p := 22795622735731741519) (by decide) (by decide) (by decide) (by decide) (by decide) (by decide) (6561 * u)
  have heq : familySource 0 3 u = 38911100780481085467 + 2 ^ 62 * (6561 * u) := by
    unfold familySource
    simp only [Nat.mul_add]
    omega
  rw [heq]
  exact hx
#print axioms backward_cell_exit_1
theorem backward_cell_exit_2 (u : Nat) : OrdinaryExit (familySource 5 3 u) (iter shortcut 62 (familySource 5 3 u)) := by
  have hx := ordinary_exit_of_source_cylinder_direct (n := 18949706080094288609307) (k := 62) (q := 39) (y := 16652202408452037167146) (by decide) (by decide) (by decide) (by decide) (6561 * u)
  have heq : familySource 5 3 u = 18949706080094288609307 + 2 ^ 62 * (6561 * u) := by
    unfold familySource
    simp only [Nat.mul_add]
    omega
  rw [heq]
  exact hx
#print axioms backward_cell_exit_2
end CollatzFinal.SourceProduct
