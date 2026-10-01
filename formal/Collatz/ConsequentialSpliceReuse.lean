import Collatz.SourceCylinderExit

namespace CollatzFinal.SourceProduct

/-- Reuse the existing odd-merge cylinder law after erasing the incidental
3^8 source-family restriction from the V55 collision. -/
theorem collision_splice_dyadic_exit (u : Nat) :
    OrdinaryExit (188790896379371192347 + 2^69*u)
      (iter shortcut 69 (188790896379371192347 + 2^69*u)) := by
  apply ordinary_exit_of_source_cylinder_odd_merge
    (n := 188790896379371192347) (k := 69)
    (y := 104984528146202043887) (q := 42)
    (p := 69989685430801362591)
  all_goals decide

/-- This certified dyadic class contains no least positive counterexample. -/
theorem collision_splice_not_minimal_bad (u : Nat) :
    ¬ MinimalBad PositiveBad (188790896379371192347 + 2^69*u) := by
  intro h
  exact minimal_bad_has_no_ordinary_exit h 69 (collision_splice_dyadic_exit u)

#print axioms collision_splice_dyadic_exit
#print axioms collision_splice_not_minimal_bad

end CollatzFinal.SourceProduct
