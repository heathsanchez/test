import Collatz.SourceCylinderExit
set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

namespace CollatzFinal.SourceProduct

/-- A guarded exit cut from the previously unresolved t = 900 + 1024*u cell.
This does not assert that every u eventually enables this guard. -/
theorem live_splice_guard_exit (u : Nat) :
    OrdinaryExit (3403982007377265835376667 + 2^83*u)
      (iter shortcut 83 (3403982007377265835376667 + 2^83*u)) := by
  apply ordinary_exit_of_source_cylinder_odd_merge
    (n := 3403982007377265835376667) (k := 83)
    (y := 2274064932508594153124870) (q := 51)
    (p := 1516043288339062768749913)
  all_goals decide

theorem live_splice_guard_not_minimal_bad (u : Nat) :
    ¬ MinimalBad PositiveBad (3403982007377265835376667 + 2^83*u) := by
  intro h
  exact minimal_bad_has_no_ordinary_exit h 83 (live_splice_guard_exit u)

#print axioms live_splice_guard_exit
#print axioms live_splice_guard_not_minimal_bad

end CollatzFinal.SourceProduct
