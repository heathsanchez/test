import Collatz.Root23LateJoinReclosure

namespace CollatzFinal

/-!
V135 — CROSS-POWER CANONICALIZATION OF THE VERIFIED V131 CHART COMPILER.

V131 accepted two arbitrary positive integer chart multipliers u,v.
But its endpoint-slope equality can ALWAYS be fulfilled without
searching for u,v:

  alpha = oddCount(a,i), beta = oddCount(p,j)
  u = 3^beta,    v = 3^alpha.

Their endpoint slopes are both 3^(alpha+beta) by commutativity.
Thus a single oriented integer inequality
       2^j * 3^alpha <= 2^i * 3^beta
plus one true base two-clock coalescence and 0<p<a
suffices to construct an INFINITE source-relative LowerMerge family.

This is an elimination of search coordinates, NOT a proof that a
suitable pair (p,i,j) exists for every positive natural source.
The chart-clock orientation is phase-sensitive: (5,3) has a favourable
clock pair (1,2) but an unfavourable pair (3,8), despite real
coalescence at both pairs. A frozen clock is consequential information.

All V129 (21), V131 (9), V132 (15), V133 (23) discovered multipliers
are exactly these cross-odd-power coefficients. The V120 source27
depth-59 direct descent also admits the canonical formula.
GLOBAL COLLATZ remains UNKNOWN.
-/

/-- No search is required to obtain a compatible pair of positive
integer endpoint-slope multipliers for any two real parity charts. -/
theorem canonical_chart_endpoint_coefficients_equal
    (a p i j : Nat) :
    3 ^ SourceProduct.oddCount a i *
       3 ^ SourceProduct.oddCount p j =
    3 ^ SourceProduct.oddCount p j *
       3 ^ SourceProduct.oddCount a i :=
  Nat.mul_comm _ _

/-- Semantic cross-power lift of one REAL two-clock base coalescence.

Only additional admissibility requirement is the original-source
weighted slope orientation, rather than user-selected multipliers.
The generated original positive source and strictly earlier positive
source remain valid for EVERY t>=0. -/
def canonicalCrossPowerJoin (a p i j : Nat)
    (hp : 0 < p)
    (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p)
    (hweighted :
       2 ^ j * 3 ^ SourceProduct.oddCount a i <=
       2 ^ i * 3 ^ SourceProduct.oddCount p j)
    (t : Nat) : LawfulFutureJoin :=
  chartOverlapJoin a p i j
    (3 ^ SourceProduct.oddCount p j)
    (3 ^ SourceProduct.oddCount a i)
    hp hearlier hweighted hmeet
    (canonical_chart_endpoint_coefficients_equal a p i j)
    t

theorem canonical_cross_power_compiles_lower_source
    (a p i j : Nat)
    (hp : 0 < p) (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p)
    (hweighted :
       2 ^ j * 3 ^ SourceProduct.oddCount a i <=
       2 ^ i * 3 ^ SourceProduct.oddCount p j)
    (t : Nat) :
    LowerMerge shortcut
        (a + 2 ^ i * (3 ^ SourceProduct.oddCount p j * t))
        (p + 2 ^ j * (3 ^ SourceProduct.oddCount a i * t)) :=
  (canonicalCrossPowerJoin a p i j hp hearlier hmeet hweighted t).toLowerMerge

/-- V129's source21 chart coefficients are forced by
the cross-power rule (3^2,3^1)=(9,3). -/
theorem root21_cross_power_parameters :
    3 ^ SourceProduct.oddCount 3 2 = 9 ∧
    3 ^ SourceProduct.oddCount 21 3 = 3 := by decide

/-- V131 root9 uses (3^1,3^5)=(3,243). -/
theorem root9_cross_power_parameters :
    3 ^ SourceProduct.oddCount 3 1 = 3 ∧
    3 ^ SourceProduct.oddCount 9 9 = 243 := by decide

/-- V132's exact-symbolic source15 instance uses (3,81). -/
theorem root15_cross_power_parameters :
    3 ^ SourceProduct.oddCount 3 1 = 3 ∧
    3 ^ SourceProduct.oddCount 15 8 = 81 := by decide

/-- V133's source23 chart uses (3,27). -/
theorem root23_cross_power_parameters :
    3 ^ SourceProduct.oddCount 3 1 = 3 ∧
    3 ^ SourceProduct.oddCount 23 7 = 27 := by decide

/-- The formerly heuristic source23 family is a direct application
of the generic canonically constructed cross-power chart, with no
user-selected coefficient parameter. -/
def canonicalRoot23 (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 7 23 = iter shortcut 1 3 := by decide
  have hweighted :
      2 ^ 1 * 3 ^ SourceProduct.oddCount 23 7 <=
      2 ^ 7 * 3 ^ SourceProduct.oddCount 3 1 := by decide
  exact canonicalCrossPowerJoin 23 3 7 1
    (by decide) (by decide) hbase hweighted t

theorem canonicalRoot23_source (t : Nat) :
    (canonicalRoot23 t).source = 23 + 384 * t := by
  change 23 + 2 ^ 7 * (3 ^ SourceProduct.oddCount 3 1 * t) =
      23 + 384 * t
  have hp : (2 : Nat) ^ 7 = 128 := by decide
  have ho : SourceProduct.oddCount 3 1 = 1 := by decide
  rw [hp, ho]
  omega

theorem canonicalRoot23_earlier (t : Nat) :
    (canonicalRoot23 t).earlier = 3 + 54 * t := by
  change 3 + 2 ^ 1 * (3 ^ SourceProduct.oddCount 23 7 * t) =
      3 + 54 * t
  have hp : (2 : Nat) ^ 1 = 2 := by decide
  have ho : SourceProduct.oddCount 23 7 = 3 := by decide
  rw [hp, ho]
  omega

/-- Opposite clock choices on the SAME actual source pair have
different weighted orientation, even though both have true coalescence.
The rejected orientation is a rejection of THIS canonical uniform
chart criterion, not of a source's Collatz convergence. -/
theorem two_clock_orientation_is_consequential :
    iter shortcut 1 5 = iter shortcut 2 3 ∧
    2 ^ 2 * 3 ^ SourceProduct.oddCount 5 1 <=
      2 ^ 1 * 3 ^ SourceProduct.oddCount 3 2 ∧
    iter shortcut 3 5 = iter shortcut 8 3 ∧
    2 ^ 3 * 3 ^ SourceProduct.oddCount 3 8 <
      2 ^ 8 * 3 ^ SourceProduct.oddCount 5 3 := by
  decide

/-- A new source5→3 family is generated automatically from the
favourable clock pair (1,2), unlike the unsuitable (3,8) pair. -/
def canonicalRoot5 (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 1 5 = iter shortcut 2 3 := by decide
  have hweighted :
      2 ^ 2 * 3 ^ SourceProduct.oddCount 5 1 <=
      2 ^ 1 * 3 ^ SourceProduct.oddCount 3 2 := by decide
  exact canonicalCrossPowerJoin 5 3 1 2
    (by decide) (by decide) hbase hweighted t

theorem canonicalRoot5_source (t : Nat) :
    (canonicalRoot5 t).source = 5 + 18 * t := by
  change 5 + 2 ^ 1 * (3 ^ SourceProduct.oddCount 3 2 * t) =
    5 + 18 * t
  have ho : SourceProduct.oddCount 3 2 = 2 := by decide
  rw [ho]
  omega

theorem canonicalRoot5_earlier (t : Nat) :
    (canonicalRoot5 t).earlier = 3 + 12 * t := by
  change 3 + 2 ^ 2 * (3 ^ SourceProduct.oddCount 5 1 * t) =
    3 + 12 * t
  have ho : SourceProduct.oddCount 5 1 = 1 := by decide
  rw [ho]
  omega

theorem canonicalRoot5_all_offsets (t : Nat) :
    0 < 3 + 12 * t ∧
    3 + 12 * t < 5 + 18 * t ∧
    iter shortcut 1 (5 + 18 * t) =
      iter shortcut 2 (3 + 12 * t) := by
  let w := canonicalRoot5 t
  have hn : w.source = 5 + 18 * t := canonicalRoot5_source t
  have hp : w.earlier = 3 + 12 * t := canonicalRoot5_earlier t
  have h : iter shortcut 1 (5 + 18 * t) =
      iter shortcut 2 (3 + 12 * t) := by
    have hc := w.common
    rw [hn, hp] at hc
    exact hc
  exact ⟨by omega, by omega, h⟩

/-- Reuse the V120 certified depth-59 negative control to derive an
automatic *source-relative* infinite affine lift with no arbitrary
multiplier choice: 27+2^59*t reaches 23+3^37*t at clock 59.

This remains one guarded dyadic source cylinder, not global Collatz. -/
def canonicalRoot27 (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 59 27 = iter shortcut 0 23 := by
    simpa [iter] using SourceProduct.source27_first_below_at_59
  have hweighted :
      2 ^ 0 * 3 ^ SourceProduct.oddCount 27 59 <=
      2 ^ 59 * 3 ^ SourceProduct.oddCount 23 0 := by
    have h0 : SourceProduct.oddCount 23 0 = 0 := by decide
    have h1 := SourceProduct.source27_slope_contracts
    rw [h0, SourceProduct.source27_odd_count_59] at *
    simpa using (Nat.le_of_lt h1)
  exact canonicalCrossPowerJoin 27 23 59 0
    (by decide) (by decide) hbase hweighted t

theorem canonicalRoot27_source (t : Nat) :
    (canonicalRoot27 t).source = 27 + 2 ^ 59 * t := by
  change 27 + 2 ^ 59 * (3 ^ SourceProduct.oddCount 23 0 * t) =
      27 + 2 ^ 59 * t
  have h : SourceProduct.oddCount 23 0 = 0 := by decide
  simp [h]

theorem canonicalRoot27_earlier (t : Nat) :
    (canonicalRoot27 t).earlier = 23 + 3 ^ 37 * t := by
  change 23 + 2 ^ 0 * (3 ^ SourceProduct.oddCount 27 59 * t) =
      23 + 3 ^ 37 * t
  rw [SourceProduct.source27_odd_count_59]
  simp

theorem canonicalRoot27_lower_merge (t : Nat) :
    LowerMerge shortcut (27 + 2 ^ 59 * t) (23 + 3 ^ 37 * t) := by
  have h := (canonicalRoot27 t).toLowerMerge
  have hn := canonicalRoot27_source t
  have hp := canonicalRoot27_earlier t
  rw [hn, hp] at h
  exact h

#print axioms canonical_chart_endpoint_coefficients_equal
#print axioms canonicalCrossPowerJoin
#print axioms canonical_cross_power_compiles_lower_source
#print axioms root21_cross_power_parameters
#print axioms root9_cross_power_parameters
#print axioms root15_cross_power_parameters
#print axioms root23_cross_power_parameters
#print axioms canonicalRoot23
#print axioms canonicalRoot23_source
#print axioms canonicalRoot23_earlier
#print axioms two_clock_orientation_is_consequential
#print axioms canonicalRoot5
#print axioms canonicalRoot5_source
#print axioms canonicalRoot5_earlier
#print axioms canonicalRoot5_all_offsets
#print axioms canonicalRoot27
#print axioms canonicalRoot27_source
#print axioms canonicalRoot27_earlier
#print axioms canonicalRoot27_lower_merge

end CollatzFinal
