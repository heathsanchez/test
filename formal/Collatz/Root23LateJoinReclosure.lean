import Collatz.RootChartOverlapCompiler
import Collatz.FirstResidualRefinement

namespace CollatzFinal

/-!
V133 — root-23 chart learned as a CONSEQUENCE of the V122 source-27
delayed-join separator, not as another general CRT coverage score.

V131's sound two-clock parity-chart constructor gives, for all t>=0:
  T^7(23+384*t) = 5+81*t = T(3+54*t),
  0 < 3+54*t < 23+384*t.

At t=0 this yields 23→3 at clocks (7,1). V122 already has the
verified source-bound first join 27→23 at clocks (59,0), proved
in FirstResidualRefinement. The V123 verified consequence compositor
therefore yields a true positive earlier root3 for 27 at clocks (66,1),
and then root2 at clocks (70,1), without replaying the original
59-step 27 trajectory or inventing a new rank.

Nothing here asserts an all-offset source-27 family at clock 66;
the composed claim for n=27 is a *single exact source*. No Collatz QED.
-/

/-- A third concrete application of the V131 general chart-overlap
constructor. Both original source and earlier source stay positive,
and the earlier source is strictly smaller for every nonnegative t. -/
def root23ViaChart (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 7 23 = iter shortcut 1 3 := by decide
  have ho23 : SourceProduct.oddCount 23 7 = 3 := by decide
  have ho3 : SourceProduct.oddCount 3 1 = 1 := by decide
  have hslope :
      3 ^ SourceProduct.oddCount 23 7 * 3 =
      3 ^ SourceProduct.oddCount 3 1 * 27 := by
    rw [ho23, ho3]
  exact chartOverlapJoin 23 3 7 1 3 27
    (by decide) (by decide) (by decide) hbase hslope t

theorem root23_chart_source (t : Nat) :
    (root23ViaChart t).source = 23 + 384 * t := by
  change 23 + 2 ^ 7 * (3 * t) = 23 + 384 * t
  have hp : (2 : Nat) ^ 7 = 128 := by decide
  rw [hp]
  omega

theorem root23_chart_earlier (t : Nat) :
    (root23ViaChart t).earlier = 3 + 54 * t := by
  change 3 + 2 ^ 1 * (27 * t) = 3 + 54 * t
  have hp : (2 : Nat) ^ 1 = 2 := by decide
  rw [hp]
  omega

/-- Newly kernel-checked all-offset source23 to earlier odd-three-root3
coalescence. The endpoints coincide at clocks (7,1) for all t. -/
theorem root23_all_offset_law (t : Nat) :
    0 < 3 + 54 * t ∧
    3 + 54 * t < 23 + 384 * t ∧
    (3 + 54 * t) % 6 = 3 ∧
    iter shortcut 7 (23 + 384 * t) =
      iter shortcut 1 (3 + 54 * t) := by
  let w := root23ViaChart t
  have hsource : w.source = 23 + 384 * t := root23_chart_source t
  have hearlier : w.earlier = 3 + 54 * t := root23_chart_earlier t
  have hm : iter shortcut 7 (23 + 384 * t) =
      iter shortcut 1 (3 + 54 * t) := by
    have h := w.common
    rw [hsource, hearlier] at h
    exact h
  exact ⟨by omega, by omega, by omega, hm⟩

/-- V122's exact source, protected first clock, and *later* endpoint.
No new shortcut calculation here: this is a typed preservation map. -/
def source27To23 : LawfulFutureJoin :=
  { source := 27
    earlier := 23
    sourceClock := 59
    earlierClock := 0
    positive := by decide
    smaller := by decide
    common := by
      simpa [iter] using SourceProduct.source27_first_below_at_59 }

/-- Compose the already warranted exact source27→23 witness with one
new root23 chart instance, retaining the two genuinely different clocks.
This is a NORMALIZED class join, not a new time-59 direct descent. -/
def source27To3ByReclosure : LawfulFutureJoin :=
  LawfulFutureJoin.compose source27To23
    (root23ViaChart 0) (by decide)

/-- The first root-normalized earlier-source3 meeting is at a LATER
clock than the independently verified source27 first lower-source
meeting at clock 59. -/
theorem source27_real_root3_meeting :
    iter shortcut 66 27 = iter shortcut 1 3 := by
  exact source27To3ByReclosure.common

/-- Compounding one additional already-certified source3→2 witness
gives a second future-class merger without searching a fresh path. -/
def source27To2ByReclosure : LawfulFutureJoin :=
  LawfulFutureJoin.compose source27To3ByReclosure
    LawfulFutureJoin.source3_to2 (by decide)

theorem source27_real_root2_meeting :
    iter shortcut 70 27 = iter shortcut 1 2 := by
  exact source27To2ByReclosure.common

theorem source27_has_certified_smaller_odd_root :
    LowerMerge shortcut 27 3 :=
  source27To3ByReclosure.toLowerMerge

theorem root23_family_not_minimal_bad
    (t : Nat)
    (hbad : MinimalBad (fun n => ¬ CollatzGood n) (23 + 384 * t)) :
    False := by
  let w := root23ViaChart t
  have hsource : w.source = 23 + 384 * t := root23_chart_source t
  have hmin : MinimalBad (fun n => ¬ CollatzGood n) w.source := by
    rw [hsource]
    exact hbad
  exact w.refutes_minimal_bad hmin

#print axioms root23ViaChart
#print axioms root23_chart_source
#print axioms root23_chart_earlier
#print axioms root23_all_offset_law
#print axioms source27To23
#print axioms source27To3ByReclosure
#print axioms source27_real_root3_meeting
#print axioms source27To2ByReclosure
#print axioms source27_real_root2_meeting
#print axioms source27_has_certified_smaller_odd_root
#print axioms root23_family_not_minimal_bad

end CollatzFinal
