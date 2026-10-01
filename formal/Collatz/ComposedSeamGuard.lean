import Collatz.SourceCylinderExit
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

namespace CollatzFinal.SourceProduct

/-- The V59 composed live seam enables a protected quarter-owner exit.
The incidental original source factor 3^8 is erased. -/
theorem composed_seam_guard_exit (u : Nat) :
    OrdinaryExit (926660659327753256987 + 2^71*u)
      (iter shortcut 71 (926660659327753256987 + 2^71*u)) := by
  apply ordinary_exit_of_source_cylinder_odd_merge
    (n := 926660659327753256987) (k := 71)
    (y := 1159437909126090129572) (q := 44)
    (p := 772958606084060086381)
  all_goals decide

theorem composed_seam_guard_not_minimal_bad (u : Nat) :
    ¬ MinimalBad PositiveBad (926660659327753256987 + 2^71*u) := by
  intro h
  exact minimal_bad_has_no_ordinary_exit h 71 (composed_seam_guard_exit u)

#print axioms composed_seam_guard_exit
#print axioms composed_seam_guard_not_minimal_bad

end CollatzFinal.SourceProduct
