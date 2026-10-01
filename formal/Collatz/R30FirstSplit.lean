import Collatz.SourceCylinderExit
import Collatz.EarlierSourceCollision

set_option maxRecDepth 100000
set_option maxHeartbeats 0

namespace CollatzFinal.SourceProduct

/-- First protected-future separator inside the V67 first residual r=30.
No direct/M1/quarter-splice cylinder is available at refinement depths 18..21.
At depth 22, the child r=3670046 has a uniform direct descent after 81
shortcut steps; therefore the whole child cylinder coalesces with an earlier
positive source. -/
theorem r30_depth22_first_split_merger (u : Nat) :
    EarlierSourceCollision
      (13880697533041245190008864795 +
        15863524604983164030494441472 * u)
      (iter shortcut 81
        (13880697533041245190008864795 +
          15863524604983164030494441472 * u)) := by
  have hx :=
    ordinary_exit_of_source_cylinder_direct
      (n := 13880697533041245190008864795)
      (k := 81)
      (y := 12364188933328561335056835446)
      (q := 51)
      (by decide) (by decide) (by decide) (by decide)
      (6561 * u)
  have hS :
      2 ^ 81 * 6561 = 15863524604983164030494441472 := by decide
  have heq :
      13880697533041245190008864795 + 2 ^ 81 * (6561 * u) =
        13880697533041245190008864795 +
          15863524604983164030494441472 * u := by
    rw [← Nat.mul_assoc, hS]
  have ho :
      OrdinaryExit
        (13880697533041245190008864795 +
          15863524604983164030494441472 * u)
        (iter shortcut 81
          (13880697533041245190008864795 +
            15863524604983164030494441472 * u)) := by
    simpa only [heq] using hx
  have hsource :
      1 < 13880697533041245190008864795 +
        15863524604983164030494441472 * u := by omega
  exact (ordinaryExit_iff_earlierSourceCollision hsource).mp ho

#print axioms r30_depth22_first_split_merger

end CollatzFinal.SourceProduct
