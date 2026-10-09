import Collatz.RelationalRootMerger

namespace CollatzFinal

/-!
V131: the exact *semantic compiler* behind root-chart overlaps.

A backward chart is an actual forward-parity cylinder with:
  (base, clock, integer source-offset slope u)
  T^clock(base + 2^clock*u*t)
    = T^clock(base) + 3^(oddCount(base,clock))*u*t.

Two independent charts can be joined for ALL natural offsets when:
  - their concrete base endpoints agree;
  - their exact endpoint affine slopes agree;
  - the second original-source intercept is smaller and positive;
  - the second original-source slope is <= the first slope.

This constructs an entire certified LawfulFutureJoin family without
enumerating any trajectories at fresh offsets. Both actual clocks,
the original source, the positive smaller source and exact proof premises
are protected.

V129's 21+72t -> 3+12t is one instance.
The next smallest root n=9 has another instance:
  T^9(9+1536t)=5+729t=T(3+486t).
Both roots are odd and divisible by 3. Neither family proves a universal
source-admitted event-production theorem or Collatz QED.
-/

/-- Protected two-clock class-merger compiler for overlapping
    source-affine parity charts, independent of any root selector. -/
def chartOverlapJoin (a p i j u v : Nat)
    (hp : 0 < p) (hbase : p < a)
    (hsourceSlope : 2 ^ j * v <= 2 ^ i * u)
    (hbaseMeet : iter shortcut i a = iter shortcut j p)
    (hendpointSlope :
       3 ^ SourceProduct.oddCount a i * u =
       3 ^ SourceProduct.oddCount p j * v)
    (t : Nat) : LawfulFutureJoin := {
  source := a + 2 ^ i * (u * t)
  earlier := p + 2 ^ j * (v * t)
  sourceClock := i
  earlierClock := j
  positive := by omega
  smaller := by
    have hscaled := Nat.mul_le_mul_right t hsourceSlope
    have hlt : p + (2 ^ j * v) * t <
        a + (2 ^ i * u) * t := by omega
    simpa [Nat.mul_assoc] using hlt
  common := by
    have hstepSource :=
      SourceProduct.parity_cylinder_shift a i (u * t)
    have hstepEarlier :=
      SourceProduct.parity_cylinder_shift p j (v * t)
    have hslope :
        (3 ^ SourceProduct.oddCount a i) * (u * t) =
        (3 ^ SourceProduct.oddCount p j) * (v * t) := by
      simpa only [Nat.mul_assoc] using
        congrArg (fun x : Nat => x * t) hendpointSlope
    calc
      iter shortcut i (a + 2 ^ i * (u * t)) =
          iter shortcut i a +
            3 ^ SourceProduct.oddCount a i * (u * t) := hstepSource
      _ = iter shortcut j p +
            3 ^ SourceProduct.oddCount p j * (v * t) := by
              rw [hbaseMeet, hslope]
      _ = iter shortcut j (p + 2 ^ j * (v * t)) :=
            hstepEarlier.symm
}

/-- The reusable constructor produces the pre-existing protected
    source-relative LowerMerge, not a new semantic exit kind. -/
theorem chart_overlap_compiles_lower_source
    (a p i j u v : Nat)
    (hp : 0 < p) (hbase : p < a)
    (hsourceSlope : 2 ^ j * v <= 2 ^ i * u)
    (hbaseMeet : iter shortcut i a = iter shortcut j p)
    (hendpointSlope :
       3 ^ SourceProduct.oddCount a i * u =
       3 ^ SourceProduct.oddCount p j * v)
    (t : Nat) :
    LowerMerge shortcut
       (a + 2 ^ i * (u * t))
       (p + 2 ^ j * (v * t)) :=
  (chartOverlapJoin a p i j u v hp hbase
       hsourceSlope hbaseMeet hendpointSlope t).toLowerMerge

/-- The V129 source21 all-offset root merger is a specialisation of
    the generic chart overlap constructor, not a separate proof grammar. -/
def root21ViaChart (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 3 21 = iter shortcut 2 3 := by decide
  have ho21 : SourceProduct.oddCount 21 3 = 1 := by decide
  have ho3 : SourceProduct.oddCount 3 2 = 2 := by decide
  have hcoef :
      3 ^ SourceProduct.oddCount 21 3 * 9 =
      3 ^ SourceProduct.oddCount 3 2 * 3 := by
    rw [ho21, ho3]
    decide
  exact chartOverlapJoin 21 3 3 2 9 3
    (by decide) (by decide) (by decide) hbase hcoef t

/-- New root9 affine chart: genuine all-offset merger at clocks 9 and 1.
    The original source and earlier root remain odd multiples of 3. -/
def root9ViaChart (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 9 9 = iter shortcut 1 3 := by decide
  have ho9 : SourceProduct.oddCount 9 9 = 5 := by decide
  have ho3 : SourceProduct.oddCount 3 1 = 1 := by decide
  have hcoef :
      3 ^ SourceProduct.oddCount 9 9 * 3 =
      3 ^ SourceProduct.oddCount 3 1 * 243 := by
    rw [ho9, ho3]
    decide
  exact chartOverlapJoin 9 3 9 1 3 243
    (by decide) (by decide) (by decide) hbase hcoef t

/-- The NEW root9 family is a true V124 typed two-clock consequence,
    with source9+1536*t and smaller root3+486*t, for ALL offsets. -/
theorem root9_chart_source (t : Nat) :
    (root9ViaChart t).source = 9 + 1536 * t := by
  change 9 + 2 ^ 9 * (3 * t) = 9 + 1536 * t
  have hp : (2 : Nat) ^ 9 = 512 := by decide
  rw [hp]
  omega

theorem root9_chart_earlier (t : Nat) :
    (root9ViaChart t).earlier = 3 + 486 * t := by
  change 3 + 2 ^ 1 * (243 * t) = 3 + 486 * t
  have hp : (2 : Nat) ^ 1 = 2 := by decide
  rw [hp]
  omega

theorem root9_all_offset_odd_three_merger (t : Nat) :
    0 < 3 + 486 * t ∧
    (3 + 486 * t) < 9 + 1536 * t ∧
    (9 + 1536 * t) % 6 = 3 ∧
    (3 + 486 * t) % 6 = 3 ∧
    LowerMerge shortcut (9 + 1536 * t) (3 + 486 * t) := by
  have w := root9ViaChart t
  have hsource := root9_chart_source t
  have hearlier := root9_chart_earlier t
  have hm : LowerMerge shortcut (9 + 1536 * t) (3 + 486 * t) := by
    simpa only [hsource, hearlier] using w.toLowerMerge
  exact ⟨by omega, by omega, by omega, by omega, hm⟩

/-- The second family also excludes a least positive bad source
    on its exactly claimed residue family. Not a global Collatz result. -/
theorem root9_family_not_minimal_bad
    (t : Nat)
    (hbad : MinimalBad (fun n => ¬ CollatzGood n) (9 + 1536 * t)) :
    False := by
  have w := root9ViaChart t
  have hsource := root9_chart_source t
  apply w.refutes_minimal_bad
  simpa only [hsource] using hbad

#print axioms chartOverlapJoin
#print axioms chart_overlap_compiles_lower_source
#print axioms root21ViaChart
#print axioms root9ViaChart
#print axioms root9_chart_source
#print axioms root9_chart_earlier
#print axioms root9_all_offset_odd_three_merger
#print axioms root9_family_not_minimal_bad

end CollatzFinal
