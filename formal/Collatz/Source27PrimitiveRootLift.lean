import Collatz.ChartMultiplierCompleteness

set_option maxRecDepth 16384
set_option maxHeartbeats 2000000

namespace CollatzFinal

/-!
V138 — lift the TRUE, previously qualified SOURCE-27 delayed root3 join
into a new infinite all-offset TWO-CLOCK source-relative root chart.

V122: T^59(27)=23, and 59 is the first original-source clock
      reaching ANY earlier positive natural future.
V133: T^66(27)=T(3)=5 by formally checked composition of
      27->23 @ (59,0), 23->3 @ (7,1).

The V136/137 reduced and complete integer multiplier calculus now
proves the 66-step source27/1-step root3 chart has weighted source
domination. It therefore produces, for ALL natural t:
  n(t) = 27 + 2^66*t,
  p(t) =  3 + 2*3^39*t,
  0<p(t)<n(t),
  T^66(n(t)) = T(p(t)).
The earlier source p(t) remains an odd positive multiple of 3.
The original source n(t) need NOT remain in that root residue.

Important: this is a NEW ROOT-NORMALISED witness, NOT new source
coverage: n(t) belongs to V120's already formally certified
larger cylinder 27+2^59*q (with q=128*t). The V120 certificate first
merges at clock59 into a possibly nonroot predecessor; the new
certified ROOT-3 family joins at clock66.

Nothing proves an earlier-source event exists for every positive natural.
GLOBAL COLLATZ remains UNKNOWN.
-/

/-- Reuse the qualified V133 V122->V131 two-clock meeting and
the V137 reduced power constructor. No trajectory search needed. -/
def source27ReducedRoot3 (t : Nat) : LawfulFutureJoin := by
  have hbase : iter shortcut 66 27 = iter shortcut 1 3 :=
    source27_real_root3_meeting
  have hweighted :
      2 ^ 1 * 3 ^ (SourceProduct.oddCount 27 66 -
                    SourceProduct.oddCount 3 1) <=
      2 ^ 66 * 3 ^ (SourceProduct.oddCount 3 1 -
                     SourceProduct.oddCount 27 66) := by decide
  exact reducedCrossPowerJoin 27 3 66 1
    (by decide) (by decide) hbase hweighted t

theorem source27_reduced_root3_source (t : Nat) :
    (source27ReducedRoot3 t).source = 27 + 2 ^ 66 * t := by
  change 27 + 2 ^ 66 *
      (3 ^ (SourceProduct.oddCount 3 1 -
             SourceProduct.oddCount 27 66) * t) =
      27 + 2 ^ 66 * t
  have hu : 3 ^ (SourceProduct.oddCount 3 1 -
                   SourceProduct.oddCount 27 66) = 1 := by decide
  rw [hu]
  simp

theorem source27_reduced_root3_earlier (t : Nat) :
    (source27ReducedRoot3 t).earlier = 3 + 2 * 3 ^ 39 * t := by
  change 3 + 2 ^ 1 *
      (3 ^ (SourceProduct.oddCount 27 66 -
             SourceProduct.oddCount 3 1) * t) =
      3 + 2 * 3 ^ 39 * t
  have hv :
      SourceProduct.oddCount 27 66 -
        SourceProduct.oddCount 3 1 = 39 := by decide
  have hp : (2 : Nat) ^ 1 = 2 := by decide
  rw [hv, hp]
  rw [← Nat.mul_assoc]

/-- For every nonnegative parameter, this is a TRUE two-clock
earlier-positive-source meeting, in precisely the V124 protected
semantic type. It does not claim first-occurrence optimality at 66. -/
theorem source27_reduced_root3_law (t : Nat) :
    0 < 3 + 2 * 3 ^ 39 * t ∧
    3 + 2 * 3 ^ 39 * t < 27 + 2 ^ 66 * t ∧
    iter shortcut 66 (27 + 2 ^ 66 * t) =
      iter shortcut 1 (3 + 2 * 3 ^ 39 * t) := by
  let w := source27ReducedRoot3 t
  have hs : w.source = 27 + 2 ^ 66 * t :=
    source27_reduced_root3_source t
  have he : w.earlier = 3 + 2 * 3 ^ 39 * t :=
    source27_reduced_root3_earlier t
  have hsame : iter shortcut 66 (27 + 2 ^ 66 * t) =
      iter shortcut 1 (3 + 2 * 3 ^ 39 * t) := by
    have h := w.common
    rw [hs, he] at h
    exact h
  have hp : 0 < 3 + 2 * 3 ^ 39 * t := by
    have h := w.positive
    rw [he] at h
    exact h
  have hlt : 3 + 2 * 3 ^ 39 * t < 27 + 2 ^ 66 * t := by
    have h := w.smaller
    rw [hs, he] at h
    exact h
  exact ⟨hp,hlt,hsame⟩

/-- The earlier witness remains an odd multiple of three: an
additional ROOT normal-form guarantee, not an exit requirement. -/
theorem source27_reduced_root3_earlier_is_three_root (t : Nat) :
    (3 + 2 * 3 ^ 39 * t) % 6 = 3 := by
  have hpow : (3 : Nat) ^ 39 = 3 * 3 ^ 38 := by decide
  have heq : 3 + 2 * 3 ^ 39 * t =
      3 + 6 * (3 ^ 38 * t) := by
    rw [hpow]
    have h6 : (2 : Nat) * 3 = 6 := by decide
    rw [← h6]
    simp [Nat.mul_assoc]
  rw [heq]
  omega

theorem source27_reduced_root3_lower_merge (t : Nat) :
    LowerMerge shortcut (27 + 2 ^ 66 * t)
      (3 + 2 * 3 ^ 39 * t) := by
  have h := (source27ReducedRoot3 t).toLowerMerge
  rw [source27_reduced_root3_source, source27_reduced_root3_earlier] at h
  exact h

/-- Crucial HONESTY BOUNDARY: the source-27 family here is only
one subfamily of V120's already-qualified broader source cylinder.
This is a NEW ROOT CAPABILITY, NOT additional coverage. -/
theorem source27_reduced_root3_is_old_dyadic_subfamily (t : Nat) :
    27 + 2 ^ 66 * t = 27 + 2 ^ 59 * (128 * t) := by
  have hp : (2 : Nat) ^ 66 = 2 ^ 59 * 128 := by decide
  rw [hp]
  simp [Nat.mul_assoc]

theorem source27_root_and_previous_direct_descent_coexist (t : Nat) :
    LowerMerge shortcut (27 + 2 ^ 66 * t)
      (iter shortcut 59 (27 + 2 ^ 66 * t)) ∧
    LowerMerge shortcut (27 + 2 ^ 66 * t)
      (3 + 2 * 3 ^ 39 * t) := by
  constructor
  · have h := SourceProduct.source27_refined_all_offsets (128 * t)
    have hs := source27_reduced_root3_is_old_dyadic_subfamily t
    rw [hs]
    exact h
  · exact source27_reduced_root3_lower_merge t

#print axioms source27ReducedRoot3
#print axioms source27_reduced_root3_source
#print axioms source27_reduced_root3_earlier
#print axioms source27_reduced_root3_law
#print axioms source27_reduced_root3_earlier_is_three_root
#print axioms source27_reduced_root3_lower_merge
#print axioms source27_reduced_root3_is_old_dyadic_subfamily
#print axioms source27_root_and_previous_direct_descent_coexist

end CollatzFinal
