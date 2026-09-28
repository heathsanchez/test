import Collatz.DeficitOneCheckpoint

namespace CollatzFinal
namespace SourceProduct

/-- The V11 one-bit coefficient corridor is not special to depth 2*n.
On any source-relative nondescending prefix, as long as the accumulated odd
count has not exceeded 2*n, the coefficient threshold can be at most one odd
step ahead of the actual odd count.

This is the reusable recursive form needed by Crystal: a hypothetical minimal
bad path cannot accumulate an arbitrarily deep coefficient deficit while
q <= 2*n. -/
theorem nondescending_q_le_double_source_qmin_corridor
    {n k : Nat}
    (hn : 0 < n)
    (hnd : ∀ i, i ≤ k → n ≤ iter shortcut i n)
    (hqpos : 0 < oddCount n k)
    (hq2 : oddCount n k ≤ 2 * n) :
    qmin k ≤ oddCount n k + 1 := by
  let q := oddCount n k
  have hqpos' : 0 < q := by simpa [q] using hqpos
  have hq2' : q ≤ 2 * n := by simpa [q] using hq2
  have hq3 : q < 3 * n := by omega
  have hrel :
      2 ^ k * n ^ q * iter shortcut k n ≤
        (3 * n + 1) ^ q * n := by
    simpa [q] using source_relative_scaled_orbit_le hn hnd
  have hend : n ≤ iter shortcut k n := hnd k (by omega)
  have hleft :
      2 ^ k * n ^ (q + 1) ≤
        (3 * n + 1) ^ q * n := by
    have hm :=
      Nat.mul_le_mul_left (2 ^ k * n ^ q) hend
    have hpow : n ^ (q + 1) = n ^ q * n := by
      rw [Nat.pow_succ]
    rw [hpow]
    exact Nat.le_trans
      (by simpa [Nat.mul_assoc] using hm) hrel
  have hnle : n ≤ 3 * n - q := by omega
  have hratio0 :=
    adjacent_power_ratio_lt (3 * n) q hqpos' hq3
  have hratio :
      (3 * n + 1) ^ q * n <
        (3 * n) ^ (q + 1) := by
    have hmul :
        (3 * n + 1) ^ q * n ≤
          (3 * n + 1) ^ q * (3 * n - q) :=
      Nat.mul_le_mul_left _ hnle
    exact Nat.lt_of_le_of_lt hmul
      (by simpa [Nat.add_assoc] using hratio0)
  apply Nat.le_of_not_gt
  intro hbad
  have hfail :
      3 ^ (q + 1) < 2 ^ k :=
    lt_qmin_fails (by omega)
  have hpowmul :
      (3 * n) ^ (q + 1) =
        3 ^ (q + 1) * n ^ (q + 1) := by
    rw [Nat.mul_pow]
  have hright :
      (3 * n) ^ (q + 1) <
        2 ^ k * n ^ (q + 1) := by
    rw [hpowmul]
    exact Nat.mul_lt_mul_of_pos_right hfail (Nat.pow_pos hn)
  omega

/-- Minimal-bad wrapper: the corridor holds at every depth whose odd count is
positive and at most twice the source. -/
theorem minimal_bad_persistent_qmin_corridor
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hqpos : 0 < oddCount n k)
    (hq2 : oddCount n k ≤ 2 * n) :
    qmin k ≤ oddCount n k + 1 := by
  exact nondescending_q_le_double_source_qmin_corridor
    hmin.1.1
    (fun i _ => minimal_bad_nondescending_all_depths hmin i)
    hqpos hq2

/-- At every depth in the persistent corridor there are only two coefficient
possibilities: either the coefficient survives, or the state is exactly one
odd step below qmin. -/
theorem minimal_bad_persistent_survival_or_deficit_one
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hqpos : 0 < oddCount n k)
    (hq2 : oddCount n k ≤ 2 * n) :
    qmin k ≤ oddCount n k ∨
      oddCount n k + 1 = qmin k := by
  have hcorr :=
    minimal_bad_persistent_qmin_corridor hmin hqpos hq2
  omega

#print axioms nondescending_q_le_double_source_qmin_corridor
#print axioms minimal_bad_persistent_qmin_corridor
#print axioms minimal_bad_persistent_survival_or_deficit_one

end SourceProduct
end CollatzFinal
