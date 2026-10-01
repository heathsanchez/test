import Collatz.SourceCylinderExit
import Collatz.EarlierSourceCollision

set_option maxRecDepth 100000
set_option maxHeartbeats 0

namespace CollatzFinal.SourceProduct

/-- V71: the literal all-zero continuation of the V67 first residual r=30
is not an infinite protected survivor. Existing compiled merger machinery is
silent at depths 38..41; at depth 42 the source cylinder has an exact odd
lower-source merge after 101 shortcut steps. No new semantic coordinate or
merger constructor is introduced. -/
theorem r30_depth42_zero_tail_merger (u : Nat) :
    EarlierSourceCollision
      (113503680976663326228507 +
        16634111176194826206439739460943872 * u)
      (iter shortcut 101
        (113503680976663326228507 +
          16634111176194826206439739460943872 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_odd_merge
      (n := 113503680976663326228507)
      (k := 101)
      (y := 153723649420054465951604)
      (q := 63)
      (p := 102482432946702977301069)
      (by decide) (by decide) (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 101 * 6561 = 16634111176194826206439739460943872 := by decide
  have heq :
      113503680976663326228507 + 2 ^ 101 * (6561 * u) =
        113503680976663326228507 +
          16634111176194826206439739460943872 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (113503680976663326228507 +
          16634111176194826206439739460943872 * u)
        (iter shortcut 101
          (113503680976663326228507 +
            16634111176194826206439739460943872 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 113503680976663326228507 +
        16634111176194826206439739460943872 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

#print axioms r30_depth42_zero_tail_merger

end CollatzFinal.SourceProduct
