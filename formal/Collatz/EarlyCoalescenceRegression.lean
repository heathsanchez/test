import Collatz.DeepAnchorCapSeparation

namespace CollatzFinal
namespace SourceProduct

/-- The existing all-offset inverse-odd constructor produces a strictly
smaller coalescent for every source 155 + 2048*q. This is a reusable
early-merge certificate, not a new universal termination theorem. -/
theorem source155_family_early_merge (q : Nat) :
    LowerMerge shortcut (155 + 2048 * q) (111 + 1458 * q) := by
  have hbase : 2 * iter shortcut 11 155 = 3 * 111 + 1 := by decide
  have hcoef : 2 * 3 ^ oddCount 155 11 = 3 * 1458 := by decide
  have h := cylinder_inverse_odd_all_offsets 155 11 q 111 1458
      hbase hcoef (by decide) (by decide)
  simpa only [show (2 : Nat) ^ 11 = 2048 by decide] using h

/-- Concrete clocks: the source 155 merges after 11 shortcut steps
with the smaller odd source 111 after one step. -/
theorem source155_merges_at_11 :
    iter shortcut 11 155 = iter shortcut 1 111 := by decide

#print axioms source155_family_early_merge
#print axioms source155_merges_at_11

end SourceProduct
end CollatzFinal
