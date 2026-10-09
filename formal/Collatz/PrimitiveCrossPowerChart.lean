import Collatz.CanonicalCrossPowerChart

namespace CollatzFinal

/-!
V136 — primitive two-clock chart saturation and the exact boundary of
the chart-orientation test. This is a conditional, source-attached
theorem family. No universal event producer is assumed or proved.
-/

/-- A positive common integer multiplier reflects, not only preserves,
    the order of nonnegative source slopes. -/
theorem positive_multiplier_order_reflection (x y q : Nat) (hq : 0 < q) :
    (x * q ≤ y * q) ↔ x ≤ y := by
  constructor
  · intro h
    exact Nat.le_of_mul_le_mul_right h hq
  · intro h
    exact Nat.mul_le_mul_right q h

/-- Factoring off a common power of three does not change a power. -/
theorem split_three_power (e m : Nat) (hm : m ≤ e) :
    3 ^ e = 3 ^ (e - m) * 3 ^ m := by
  have he : e - m + m = e := Nat.sub_add_cancel hm
  calc
    3 ^ e = 3 ^ (e - m + m) := by rw [he]
    _ = 3 ^ (e - m) * 3 ^ m := Nat.pow_add _ _ _

/-- The *primitive* coefficients are the cross-powers with their
    common factor 3^min(alpha,beta) removed. -/
theorem primitive_endpoint_slopes_match (alpha beta : Nat) :
    3 ^ alpha * 3 ^ (beta - min alpha beta) =
    3 ^ beta * 3 ^ (alpha - min alpha beta) := by
  have h : alpha + (beta - min alpha beta) =
      beta + (alpha - min alpha beta) := by omega
  simpa only [Nat.pow_add] using
    congrArg (fun k : Nat => (3 : Nat) ^ k) h

/-- At least one primitive multiplier is 1; no extra common
    factor of three remains. -/
theorem primitive_has_unit_multiplier (alpha beta : Nat) :
    3 ^ (beta - min alpha beta) = 1 ∨
      3 ^ (alpha - min alpha beta) = 1 := by
  by_cases h : alpha ≤ beta
  · right
    simp [Nat.min_eq_left h]
  · left
    have h' : beta ≤ alpha := by omega
    simp [Nat.min_eq_right h']

/-- The original weighted clock inequality is equivalent to its
    reduced primitive-coefficient version, not merely implied by it. -/
theorem primitive_weighted_guard_iff (alpha beta i j : Nat) :
    (2 ^ j * 3 ^ (alpha - min alpha beta) ≤
       2 ^ i * 3 ^ (beta - min alpha beta)) ↔
    (2 ^ j * 3 ^ alpha ≤ 2 ^ i * 3 ^ beta) := by
  let m := min alpha beta
  have ha : m ≤ alpha := Nat.min_le_left alpha beta
  have hb : m ≤ beta := Nat.min_le_right alpha beta
  have hl :
      2 ^ j * 3 ^ alpha =
        (2 ^ j * 3 ^ (alpha - m)) * 3 ^ m := by
    rw [split_three_power alpha m ha]
    simp only [Nat.mul_assoc]
  have hr :
      2 ^ i * 3 ^ beta =
        (2 ^ i * 3 ^ (beta - m)) * 3 ^ m := by
    rw [split_three_power beta m hb]
    simp only [Nat.mul_assoc]
  have hp : 0 < (3 : Nat) ^ m := Nat.pow_pos (by decide)
  rw [hl, hr]
  exact (positive_multiplier_order_reflection _ _ _ hp).symm

/-- All-offset strict lower-source charts need no coefficient search
    and use the smallest cross-powers of three. -/
def primitiveCrossPowerJoin (a p i j : Nat)
    (hp : 0 < p)
    (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p)
    (hweighted :
       2 ^ j * 3 ^ SourceProduct.oddCount a i ≤
       2 ^ i * 3 ^ SourceProduct.oddCount p j)
    (t : Nat) : LawfulFutureJoin :=
  chartOverlapJoin a p i j
    (3 ^ (SourceProduct.oddCount p j -
      min (SourceProduct.oddCount a i) (SourceProduct.oddCount p j)))
    (3 ^ (SourceProduct.oddCount a i -
      min (SourceProduct.oddCount a i) (SourceProduct.oddCount p j)))
    hp hearlier
    ((primitive_weighted_guard_iff
      (SourceProduct.oddCount a i) (SourceProduct.oddCount p j) i j).mpr hweighted)
    hmeet
    (primitive_endpoint_slopes_match
      (SourceProduct.oddCount a i) (SourceProduct.oddCount p j))
    t

theorem primitive_cross_power_compiles_lower_source
    (a p i j : Nat)
    (hp : 0 < p) (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p)
    (hweighted :
       2 ^ j * 3 ^ SourceProduct.oddCount a i ≤
       2 ^ i * 3 ^ SourceProduct.oddCount p j)
    (t : Nat) :
    LowerMerge shortcut
      (a + 2 ^ i *
         (3 ^ (SourceProduct.oddCount p j -
           min (SourceProduct.oddCount a i)
               (SourceProduct.oddCount p j)) * t))
      (p + 2 ^ j *
         (3 ^ (SourceProduct.oddCount a i -
           min (SourceProduct.oddCount a i)
               (SourceProduct.oddCount p j)) * t)) :=
  (primitiveCrossPowerJoin a p i j hp hearlier hmeet hweighted t).toLowerMerge

/-- A slope orientation is necessary if the predecessor remains smaller
    at *every* natural offset. A hypothetical universal family cannot
    evade an adverse orientation by testing more t. -/
theorem all_offsets_strict_smaller_forces_slope
    (a p A B : Nat)
    (h : ∀ t : Nat, p + B * t < a + A * t) :
    B ≤ A := by
  by_cases hguard : B ≤ A
  · exact hguard
  · have hg : A + 1 ≤ B := by omega
    have hm : A * (a + 1) + (a + 1) ≤ B * (a + 1) := by
      simpa only [Nat.add_mul, one_mul] using
        (Nat.mul_le_mul_right (a + 1) hg)
    have hs := h (a + 1)
    omega

/-- Given the strict base source guard, the slope inequality is
    exactly equivalent to being smaller at every offset. -/
theorem slope_iff_all_offsets_strict_smaller
    (a p A B : Nat) (hbase : p < a) :
    (B ≤ A) ↔ (∀ t : Nat, p + B * t < a + A * t) := by
  constructor
  · intro hs t
    have hm := Nat.mul_le_mul_right t hs
    omega
  · exact all_offsets_strict_smaller_forces_slope a p A B

/-- Odd visits obey an additive cocycle under actual forward suffixes. -/
theorem odd_count_append (n i k : Nat) :
    SourceProduct.oddCount n (i + k) =
      SourceProduct.oddCount n i +
        SourceProduct.oddCount (iter shortcut i n) k := by
  induction k with
  | zero =>
      simp [SourceProduct.oddCount]
  | succ k ih =>
      have horbit :
          iter shortcut (i + k) n =
            iter shortcut k (iter shortcut i n) :=
        iter_add shortcut i k n
      rw [Nat.add_succ]
      simp only [SourceProduct.oddCount]
      rw [ih, horbit]
      by_cases hpar : iter shortcut k (iter shortcut i n) % 2 = 0
      · simp [hpar]
      · simp [hpar, Nat.add_assoc]

/-- Appending the same actual trajectory suffix multiplies both
    weighted slopes by the same strictly positive 2^k 3^c.
    Thus a hostile clock orientation stays hostile. -/
theorem common_suffix_preserves_weighted_orientation
    (a p i j k : Nat)
    (hmeet : iter shortcut i a = iter shortcut j p) :
    (2 ^ (j + k) * 3 ^ SourceProduct.oddCount a (i + k) ≤
      2 ^ (i + k) * 3 ^ SourceProduct.oddCount p (j + k)) ↔
    (2 ^ j * 3 ^ SourceProduct.oddCount a i ≤
      2 ^ i * 3 ^ SourceProduct.oddCount p j) := by
  let c := SourceProduct.oddCount (iter shortcut i a) k
  have ha :
      SourceProduct.oddCount a (i + k) =
      SourceProduct.oddCount a i + c :=
    odd_count_append a i k
  have hb :
      SourceProduct.oddCount p (j + k) =
      SourceProduct.oddCount p j + c := by
    simpa only [c, hmeet] using odd_count_append p j k
  have hl :
      2 ^ (j + k) * 3 ^ SourceProduct.oddCount a (i + k) =
      (2 ^ j * 3 ^ SourceProduct.oddCount a i) *
        (2 ^ k * 3 ^ c) := by
    rw [ha]
    simp [Nat.pow_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hr :
      2 ^ (i + k) * 3 ^ SourceProduct.oddCount p (j + k) =
      (2 ^ i * 3 ^ SourceProduct.oddCount p j) *
        (2 ^ k * 3 ^ c) := by
    rw [hb]
    simp [Nat.pow_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have h2 : 0 < (2 : Nat) ^ k := Nat.pow_pos (by decide)
  have h3 : 0 < (3 : Nat) ^ c := Nat.pow_pos (by decide)
  have hq : 0 < 2 ^ k * 3 ^ c := Nat.mul_pos h2 h3
  rw [hl, hr]
  exact positive_multiplier_order_reflection _ _ _ hq

/-- Universal event-existence remains the missing premise:
    *any* genuine earlier-source meeting defeats a least bad source,
    independently of clock orientation or chart construction. -/
theorem base_meeting_refutes_minimal_positive_bad
    (a p i j : Nat)
    (hmin : MinimalBad SourceProduct.PositiveBad a)
    (hp : 0 < p) (hearlier : p < a)
    (hmeet : iter shortcut i a = iter shortcut j p) : False := by
  exact (SourceProduct.positive_minimal_no_lower_merge hmin p hp)
    ⟨hearlier, i, j, hmeet⟩

def primitiveRoot23 (t : Nat) : LawfulFutureJoin := by
  have hm : iter shortcut 7 23 = iter shortcut 1 3 := by decide
  have hw :
      2 ^ 1 * 3 ^ SourceProduct.oddCount 23 7 ≤
      2 ^ 7 * 3 ^ SourceProduct.oddCount 3 1 := by decide
  exact primitiveCrossPowerJoin 23 3 7 1
    (by decide) (by decide) hm hw t

theorem primitiveRoot23_all_offsets (t : Nat) :
    0 < 3 + 18 * t ∧
    3 + 18 * t < 23 + 128 * t ∧
    iter shortcut 7 (23 + 128 * t) =
      iter shortcut 1 (3 + 18 * t) := by
  let w := primitiveRoot23 t
  have hs : w.source = 23 + 128 * t := by
    change 23 + 2 ^ 7 *
      (3 ^ (SourceProduct.oddCount 3 1 -
       min (SourceProduct.oddCount 23 7) (SourceProduct.oddCount 3 1)) * t)
       = 23 + 128 * t
    have hc :
        3 ^ (SourceProduct.oddCount 3 1 -
         min (SourceProduct.oddCount 23 7) (SourceProduct.oddCount 3 1)) =
        1 := by decide
    have h2 : (2 : Nat) ^ 7 = 128 := by decide
    rw [hc, h2]
    omega
  have he : w.earlier = 3 + 18 * t := by
    change 3 + 2 ^ 1 *
      (3 ^ (SourceProduct.oddCount 23 7 -
       min (SourceProduct.oddCount 23 7) (SourceProduct.oddCount 3 1)) * t)
       = 3 + 18 * t
    have hc :
        3 ^ (SourceProduct.oddCount 23 7 -
         min (SourceProduct.oddCount 23 7) (SourceProduct.oddCount 3 1)) =
        9 := by decide
    rw [hc]
    omega
  have h := w.common
  rw [hs, he] at h
  exact ⟨by omega, by omega, h⟩

def primitiveRoot5 (t : Nat) : LawfulFutureJoin := by
  have hm : iter shortcut 1 5 = iter shortcut 2 3 := by decide
  have hw :
      2 ^ 2 * 3 ^ SourceProduct.oddCount 5 1 ≤
      2 ^ 1 * 3 ^ SourceProduct.oddCount 3 2 := by decide
  exact primitiveCrossPowerJoin 5 3 1 2
    (by decide) (by decide) hm hw t

theorem primitiveRoot5_all_offsets (t : Nat) :
    0 < 3 + 4 * t ∧
    3 + 4 * t < 5 + 6 * t ∧
    iter shortcut 1 (5 + 6 * t) =
      iter shortcut 2 (3 + 4 * t) := by
  let w := primitiveRoot5 t
  have hs : w.source = 5 + 6 * t := by
    change 5 + 2 ^ 1 *
      (3 ^ (SourceProduct.oddCount 3 2 -
       min (SourceProduct.oddCount 5 1) (SourceProduct.oddCount 3 2)) * t)
       = 5 + 6 * t
    have hc :
        3 ^ (SourceProduct.oddCount 3 2 -
         min (SourceProduct.oddCount 5 1) (SourceProduct.oddCount 3 2)) =
        3 := by decide
    rw [hc]
    omega
  have he : w.earlier = 3 + 4 * t := by
    change 3 + 2 ^ 2 *
      (3 ^ (SourceProduct.oddCount 5 1 -
       min (SourceProduct.oddCount 5 1) (SourceProduct.oddCount 3 2)) * t)
       = 3 + 4 * t
    have hc :
        3 ^ (SourceProduct.oddCount 5 1 -
         min (SourceProduct.oddCount 5 1) (SourceProduct.oddCount 3 2)) =
        1 := by decide
    rw [hc]
    omega
  have h := w.common
  rw [hs, he] at h
  exact ⟨by omega, by omega, h⟩

#print axioms positive_multiplier_order_reflection
#print axioms split_three_power
#print axioms primitive_endpoint_slopes_match
#print axioms primitive_has_unit_multiplier
#print axioms primitive_weighted_guard_iff
#print axioms primitiveCrossPowerJoin
#print axioms primitive_cross_power_compiles_lower_source
#print axioms all_offsets_strict_smaller_forces_slope
#print axioms slope_iff_all_offsets_strict_smaller
#print axioms odd_count_append
#print axioms common_suffix_preserves_weighted_orientation
#print axioms base_meeting_refutes_minimal_positive_bad
#print axioms primitiveRoot23
#print axioms primitiveRoot23_all_offsets
#print axioms primitiveRoot5
#print axioms primitiveRoot5_all_offsets

end CollatzFinal
