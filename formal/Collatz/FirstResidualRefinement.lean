import Collatz.CylinderCoalescence

-- The concrete 59-step exact reducer needs more elaborator recursion,
-- not a new axiom or a weakened theorem.
set_option maxRecDepth 16384
set_option maxHeartbeats 2000000

namespace CollatzFinal
namespace SourceProduct

/-- First exact CRT representative still UNKNOWN under the fixed V120 grammar.
This theorem uses a NEW depth-59 parity prefix, rather than pretending the
entire old depth-12 CRT residue cylinder is now resolved. -/
theorem source27_first_below_at_59 :
    iter shortcut 59 27 = 23 := by decide

theorem source27_odd_count_59 :
    oddCount 27 59 = 37 := by decide

theorem source27_slope_contracts :
    3 ^ oddCount 27 59 < 2 ^ 59 := by
  rw [source27_odd_count_59]
  decide

/-- New smaller-source coalescence on one very narrow but infinite
family: 27+2^59*q. Its period is NOT the original 2^12*3^7 product.
This is strictly scoped evidence, not universal natural-source closure. -/
theorem source27_refined_all_offsets (q : Nat) :
    LowerMerge shortcut (27 + 2 ^ 59 * q)
      (iter shortcut 59 (27 + 2 ^ 59 * q)) := by
  exact cylinder_direct_all_offsets 27 59 q
    (by rw [source27_first_below_at_59]; decide)
    (Nat.le_of_lt source27_slope_contracts)

#print axioms source27_first_below_at_59
#print axioms source27_odd_count_59
#print axioms source27_slope_contracts
#print axioms source27_refined_all_offsets

end SourceProduct
end CollatzFinal
