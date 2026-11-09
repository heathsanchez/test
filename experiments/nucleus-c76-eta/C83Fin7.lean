import Init

/-!
C83 source-era Lean 4.34.1 concrete Fin 7 equality decision census.
Each closed decision is checked by kernel definitional reduction via rfl.
This is a certificate basis, NOT authorization to rewrite unrelated
captured contexts or to accept original n7 without its actual proof.
-/

namespace C83Fin7

theorem case_0_0 : decide ((0 : Fin 7) = (0 : Fin 7)) = true := by
  rfl

theorem case_0_1 : decide ((0 : Fin 7) = (1 : Fin 7)) = false := by
  rfl

theorem case_0_2 : decide ((0 : Fin 7) = (2 : Fin 7)) = false := by
  rfl

theorem case_0_3 : decide ((0 : Fin 7) = (3 : Fin 7)) = false := by
  rfl

theorem case_0_4 : decide ((0 : Fin 7) = (4 : Fin 7)) = false := by
  rfl

theorem case_0_5 : decide ((0 : Fin 7) = (5 : Fin 7)) = false := by
  rfl

theorem case_0_6 : decide ((0 : Fin 7) = (6 : Fin 7)) = false := by
  rfl

theorem case_1_0 : decide ((1 : Fin 7) = (0 : Fin 7)) = false := by
  rfl

theorem case_1_1 : decide ((1 : Fin 7) = (1 : Fin 7)) = true := by
  rfl

theorem case_1_2 : decide ((1 : Fin 7) = (2 : Fin 7)) = false := by
  rfl

theorem case_1_3 : decide ((1 : Fin 7) = (3 : Fin 7)) = false := by
  rfl

theorem case_1_4 : decide ((1 : Fin 7) = (4 : Fin 7)) = false := by
  rfl

theorem case_1_5 : decide ((1 : Fin 7) = (5 : Fin 7)) = false := by
  rfl

theorem case_1_6 : decide ((1 : Fin 7) = (6 : Fin 7)) = false := by
  rfl

theorem case_2_0 : decide ((2 : Fin 7) = (0 : Fin 7)) = false := by
  rfl

theorem case_2_1 : decide ((2 : Fin 7) = (1 : Fin 7)) = false := by
  rfl

theorem case_2_2 : decide ((2 : Fin 7) = (2 : Fin 7)) = true := by
  rfl

theorem case_2_3 : decide ((2 : Fin 7) = (3 : Fin 7)) = false := by
  rfl

theorem case_2_4 : decide ((2 : Fin 7) = (4 : Fin 7)) = false := by
  rfl

theorem case_2_5 : decide ((2 : Fin 7) = (5 : Fin 7)) = false := by
  rfl

theorem case_2_6 : decide ((2 : Fin 7) = (6 : Fin 7)) = false := by
  rfl

theorem case_3_0 : decide ((3 : Fin 7) = (0 : Fin 7)) = false := by
  rfl

theorem case_3_1 : decide ((3 : Fin 7) = (1 : Fin 7)) = false := by
  rfl

theorem case_3_2 : decide ((3 : Fin 7) = (2 : Fin 7)) = false := by
  rfl

theorem case_3_3 : decide ((3 : Fin 7) = (3 : Fin 7)) = true := by
  rfl

theorem case_3_4 : decide ((3 : Fin 7) = (4 : Fin 7)) = false := by
  rfl

theorem case_3_5 : decide ((3 : Fin 7) = (5 : Fin 7)) = false := by
  rfl

theorem case_3_6 : decide ((3 : Fin 7) = (6 : Fin 7)) = false := by
  rfl

theorem case_4_0 : decide ((4 : Fin 7) = (0 : Fin 7)) = false := by
  rfl

theorem case_4_1 : decide ((4 : Fin 7) = (1 : Fin 7)) = false := by
  rfl

theorem case_4_2 : decide ((4 : Fin 7) = (2 : Fin 7)) = false := by
  rfl

theorem case_4_3 : decide ((4 : Fin 7) = (3 : Fin 7)) = false := by
  rfl

theorem case_4_4 : decide ((4 : Fin 7) = (4 : Fin 7)) = true := by
  rfl

theorem case_4_5 : decide ((4 : Fin 7) = (5 : Fin 7)) = false := by
  rfl

theorem case_4_6 : decide ((4 : Fin 7) = (6 : Fin 7)) = false := by
  rfl

theorem case_5_0 : decide ((5 : Fin 7) = (0 : Fin 7)) = false := by
  rfl

theorem case_5_1 : decide ((5 : Fin 7) = (1 : Fin 7)) = false := by
  rfl

theorem case_5_2 : decide ((5 : Fin 7) = (2 : Fin 7)) = false := by
  rfl

theorem case_5_3 : decide ((5 : Fin 7) = (3 : Fin 7)) = false := by
  rfl

theorem case_5_4 : decide ((5 : Fin 7) = (4 : Fin 7)) = false := by
  rfl

theorem case_5_5 : decide ((5 : Fin 7) = (5 : Fin 7)) = true := by
  rfl

theorem case_5_6 : decide ((5 : Fin 7) = (6 : Fin 7)) = false := by
  rfl

theorem case_6_0 : decide ((6 : Fin 7) = (0 : Fin 7)) = false := by
  rfl

theorem case_6_1 : decide ((6 : Fin 7) = (1 : Fin 7)) = false := by
  rfl

theorem case_6_2 : decide ((6 : Fin 7) = (2 : Fin 7)) = false := by
  rfl

theorem case_6_3 : decide ((6 : Fin 7) = (3 : Fin 7)) = false := by
  rfl

theorem case_6_4 : decide ((6 : Fin 7) = (4 : Fin 7)) = false := by
  rfl

theorem case_6_5 : decide ((6 : Fin 7) = (5 : Fin 7)) = false := by
  rfl

theorem case_6_6 : decide ((6 : Fin 7) = (6 : Fin 7)) = true := by
  rfl

-- Explicit Eq.refl tests whether two selected source decisions reduce
-- definitionally, rather than relying only on the rfl tactic.
theorem direct_same : decide ((0 : Fin 7) = (0 : Fin 7)) = true :=
  Eq.refl _
theorem direct_distinct : decide ((0 : Fin 7) = (1 : Fin 7)) = false :=
  Eq.refl _

end C83Fin7


#print axioms C83Fin7.case_0_0
#print axioms C83Fin7.case_0_1
#print axioms C83Fin7.case_0_2
#print axioms C83Fin7.case_0_3
#print axioms C83Fin7.case_0_4
#print axioms C83Fin7.case_0_5
#print axioms C83Fin7.case_0_6
#print axioms C83Fin7.case_1_0
#print axioms C83Fin7.case_1_1
#print axioms C83Fin7.case_1_2
#print axioms C83Fin7.case_1_3
#print axioms C83Fin7.case_1_4
#print axioms C83Fin7.case_1_5
#print axioms C83Fin7.case_1_6
#print axioms C83Fin7.case_2_0
#print axioms C83Fin7.case_2_1
#print axioms C83Fin7.case_2_2
#print axioms C83Fin7.case_2_3
#print axioms C83Fin7.case_2_4
#print axioms C83Fin7.case_2_5
#print axioms C83Fin7.case_2_6
#print axioms C83Fin7.case_3_0
#print axioms C83Fin7.case_3_1
#print axioms C83Fin7.case_3_2
#print axioms C83Fin7.case_3_3
#print axioms C83Fin7.case_3_4
#print axioms C83Fin7.case_3_5
#print axioms C83Fin7.case_3_6
#print axioms C83Fin7.case_4_0
#print axioms C83Fin7.case_4_1
#print axioms C83Fin7.case_4_2
#print axioms C83Fin7.case_4_3
#print axioms C83Fin7.case_4_4
#print axioms C83Fin7.case_4_5
#print axioms C83Fin7.case_4_6
#print axioms C83Fin7.case_5_0
#print axioms C83Fin7.case_5_1
#print axioms C83Fin7.case_5_2
#print axioms C83Fin7.case_5_3
#print axioms C83Fin7.case_5_4
#print axioms C83Fin7.case_5_5
#print axioms C83Fin7.case_5_6
#print axioms C83Fin7.case_6_0
#print axioms C83Fin7.case_6_1
#print axioms C83Fin7.case_6_2
#print axioms C83Fin7.case_6_3
#print axioms C83Fin7.case_6_4
#print axioms C83Fin7.case_6_5
#print axioms C83Fin7.case_6_6
#print axioms C83Fin7.direct_same
#print axioms C83Fin7.direct_distinct
