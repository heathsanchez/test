import Collatz.FutureCoalescenceQuotient
import Collatz.ConsequentialSpliceReuse
import Collatz.LiveSpliceGuard
import Collatz.ComposedSeamGuard

set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

namespace CollatzFinal.SourceProduct

/-- Canonical compiled capability: the source's future coalesces with the
future of one strictly earlier positive source. This is a proposition, not a
mechanism-specific data structure. -/
def LowerClassMerge (n : Nat) : Prop :=
  ∃ p a b,
    0 < p ∧
    p < n ∧
    iter shortcut a n = iter shortcut b p

theorem lowerClassMerge_to_smaller_coalescent
    {n : Nat} (m : LowerClassMerge n) :
    ∃ p, 0 < p ∧ p < n ∧ OrbitCoalescent n p := by
  rcases m with ⟨p, a, b, hp, hlt, hcommon⟩
  exact ⟨p, hp, hlt, ⟨a, b, hcommon⟩⟩

theorem lowerClassMerge_closes_source
    {n : Nat} (hn : 1 < n) (m : LowerClassMerge n) :
    ExitObligation n n := by
  exact (exitObligation_iff_smaller_coalescent hn).2
    (lowerClassMerge_to_smaller_coalescent m)

/-- Any previously certified OrdinaryExit on an actual source orbit compiles
losslessly to the one canonical lower-class-merger proposition. -/
theorem compile_ordinaryExit_on_source_orbit
    {n k : Nat}
    (hn : 1 < n)
    (hexit : OrdinaryExit n (iter shortcut k n)) :
    LowerClassMerge n := by
  have hcollision :
      EarlierSourceCollision n (iter shortcut k n) :=
    (ordinaryExit_iff_earlierSourceCollision hn).1 hexit
  rcases hcollision with ⟨p, b, hp, hlt, hpb⟩
  exact ⟨p, k, b, hp, hlt, hpb.symm⟩

/-- V57's dyadic splice is not a distinct semantic capability after
compilation: it is one guarded producer of LowerClassMerge. -/
theorem v57_collision_splice_compiled (u : Nat) :
    LowerClassMerge (188790896379371192347 + 2^69*u) := by
  apply compile_ordinaryExit_on_source_orbit
  · omega
  · exact collision_splice_dyadic_exit u

/-- V58's live splice compiles to the same capability proposition. -/
theorem v58_live_splice_compiled (u : Nat) :
    LowerClassMerge (3403982007377265835376667 + 2^83*u) := by
  apply compile_ordinaryExit_on_source_orbit
  · omega
  · exact live_splice_guard_exit u

/-- V60's composed seam guard also compiles to the same capability proposition. -/
theorem v60_composed_seam_compiled (u : Nat) :
    LowerClassMerge (926660659327753256987 + 2^71*u) := by
  apply compile_ordinaryExit_on_source_orbit
  · omega
  · exact composed_seam_guard_exit u

/-- Once compiled, the mechanism label is irrelevant to the QED interface:
all three historical guards discharge the same source-level obligation. -/
theorem v57_compiled_closes (u : Nat) :
    ExitObligation
      (188790896379371192347 + 2^69*u)
      (188790896379371192347 + 2^69*u) := by
  exact lowerClassMerge_closes_source (by omega)
    (v57_collision_splice_compiled u)

theorem v58_compiled_closes (u : Nat) :
    ExitObligation
      (3403982007377265835376667 + 2^83*u)
      (3403982007377265835376667 + 2^83*u) := by
  exact lowerClassMerge_closes_source (by omega)
    (v58_live_splice_compiled u)

theorem v60_compiled_closes (u : Nat) :
    ExitObligation
      (926660659327753256987 + 2^71*u)
      (926660659327753256987 + 2^71*u) := by
  exact lowerClassMerge_closes_source (by omega)
    (v60_composed_seam_compiled u)

/-- The universal research target can now be stated entirely in the compiled
capability language. No mechanism-specific rank or centre field appears. -/
def UniversalLowerClassMerge : Prop :=
  ∀ n, 1 < n → LowerClassMerge n

theorem collatz_of_universal_compiled_mergers
    (h : UniversalLowerClassMerge) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply collatz_of_every_source_coalesces_lower
  intro n hn
  exact lowerClassMerge_to_smaller_coalescent (h n hn)

#print axioms lowerClassMerge_to_smaller_coalescent
#print axioms lowerClassMerge_closes_source
#print axioms compile_ordinaryExit_on_source_orbit
#print axioms v57_collision_splice_compiled
#print axioms v58_live_splice_compiled
#print axioms v60_composed_seam_compiled
#print axioms v57_compiled_closes
#print axioms v58_compiled_closes
#print axioms v60_compiled_closes
#print axioms collatz_of_universal_compiled_mergers

end CollatzFinal.SourceProduct
