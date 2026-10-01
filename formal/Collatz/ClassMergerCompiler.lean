import Collatz.FutureCoalescenceQuotient
import Collatz.ConsequentialSpliceReuse
import Collatz.LiveSpliceGuard
import Collatz.ComposedSeamGuard

set_option maxRecDepth 10000
set_option maxHeartbeats 2000000

namespace CollatzFinal.SourceProduct

/-- Canonical compiled capability: the source's future coalesces with the
future of one strictly earlier positive source. -/
structure LowerClassMerge (n : Nat) where
  lower : Nat
  sourceDepth : Nat
  lowerDepth : Nat
  lower_positive : 0 < lower
  lower_lt_source : lower < n
  common_future :
    iter shortcut sourceDepth n = iter shortcut lowerDepth lower

theorem LowerClassMerge.toOrbitCoalescent
    {n : Nat} (m : LowerClassMerge n) :
    OrbitCoalescent n m.lower := by
  exact ⟨m.sourceDepth, m.lowerDepth, m.common_future⟩

theorem LowerClassMerge.closes_source
    {n : Nat} (hn : 1 < n) (m : LowerClassMerge n) :
    ExitObligation n n := by
  exact (exitObligation_iff_smaller_coalescent hn).2
    ⟨m.lower, m.lower_positive, m.lower_lt_source, m.toOrbitCoalescent⟩

/-- Any previously certified OrdinaryExit on an actual source orbit compiles
losslessly to the one canonical lower-class-merger capability. -/
theorem compile_ordinaryExit_on_source_orbit
    {n k : Nat}
    (hn : 1 < n)
    (hexit : OrdinaryExit n (iter shortcut k n)) :
    LowerClassMerge n := by
  have hcollision :
      EarlierSourceCollision n (iter shortcut k n) :=
    (ordinaryExit_iff_earlierSourceCollision hn).1 hexit
  rcases hcollision with ⟨p, b, hp, hlt, hpb⟩
  exact
    { lower := p
      sourceDepth := k
      lowerDepth := b
      lower_positive := hp
      lower_lt_source := hlt
      common_future := hpb.symm }

/-- V57's dyadic splice is not a distinct semantic capability after
compilation: it is one guarded producer of LowerClassMerge. -/
theorem v57_collision_splice_compiled (u : Nat) :
    LowerClassMerge (188790896379371192347 + 2^69*u) := by
  apply compile_ordinaryExit_on_source_orbit
  · omega
  · exact collision_splice_dyadic_exit u

/-- V58's live splice compiles to the same capability type. -/
theorem v58_live_splice_compiled (u : Nat) :
    LowerClassMerge (3403982007377265835376667 + 2^83*u) := by
  apply compile_ordinaryExit_on_source_orbit
  · omega
  · exact live_splice_guard_exit u

/-- V60's composed seam guard also compiles to the same capability type. -/
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
  exact (v57_collision_splice_compiled u).closes_source (by omega)

theorem v58_compiled_closes (u : Nat) :
    ExitObligation
      (3403982007377265835376667 + 2^83*u)
      (3403982007377265835376667 + 2^83*u) := by
  exact (v58_live_splice_compiled u).closes_source (by omega)

theorem v60_compiled_closes (u : Nat) :
    ExitObligation
      (926660659327753256987 + 2^71*u)
      (926660659327753256987 + 2^71*u) := by
  exact (v60_composed_seam_compiled u).closes_source (by omega)

/-- The universal research target can now be stated entirely in the compiled
capability language. No mechanism-specific rank or centre field appears. -/
def UniversalLowerClassMerge : Prop :=
  ∀ n, 1 < n → Nonempty (LowerClassMerge n)

theorem collatz_of_universal_compiled_mergers
    (h : UniversalLowerClassMerge) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply collatz_of_every_source_coalesces_lower
  intro n hn
  obtain ⟨m⟩ := h n hn
  exact
    ⟨m.lower, m.lower_positive, m.lower_lt_source,
      m.toOrbitCoalescent⟩

#print axioms LowerClassMerge.toOrbitCoalescent
#print axioms LowerClassMerge.closes_source
#print axioms compile_ordinaryExit_on_source_orbit
#print axioms v57_collision_splice_compiled
#print axioms v58_live_splice_compiled
#print axioms v60_composed_seam_compiled
#print axioms v57_compiled_closes
#print axioms v58_compiled_closes
#print axioms v60_compiled_closes
#print axioms collatz_of_universal_compiled_mergers

end CollatzFinal.SourceProduct
