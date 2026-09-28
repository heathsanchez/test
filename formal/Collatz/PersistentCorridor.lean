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


/-- Any nondescending prefix has at least half as many odd steps as ordinary
steps.  This is the arbitrary-depth form of the V9 double-depth diagonal. -/
theorem nondescending_depth_le_twice_oddCount
    {n k : Nat}
    (hn : 0 < n)
    (hnd : n ≤ iter shortcut k n) :
    k ≤ 2 * oddCount n k := by
  have henv := scaled_orbit_le_four_pow_odds hn k
  have hscaled :
      2 ^ k * n ≤ 4 ^ oddCount n k * n := by
    exact Nat.le_trans (Nat.mul_le_mul_left (2 ^ k) hnd) henv
  apply Nat.le_of_not_gt
  intro hbad
  have hexp : 2 * oddCount n k < k := by omega
  have hp2 :
      2 ^ (2 * oddCount n k) < 2 ^ k :=
    Nat.pow_lt_pow_right (by decide : 1 < 2) hexp
  have hfour :
      4 ^ oddCount n k =
        2 ^ (2 * oddCount n k) := by
    rw [show 4 = 2 ^ 2 by decide, ← Nat.pow_mul]
  have hp :
      4 ^ oddCount n k < 2 ^ k := by
    simpa [hfour] using hp2
  have hm :=
    (Nat.mul_lt_mul_right hn).2 hp
  omega

/-- Elementary separation at the second deterministic diagonal. -/
theorem three_pow_double_succ_lt_two_pow_quadruple
    (n : Nat) (hn : 3 ≤ n) :
    3 ^ (2 * n + 1) < 2 ^ (4 * n) := by
  obtain ⟨m, rfl⟩ : ∃ m, n = m + 3 := by
    exact ⟨n - 3, by omega⟩
  induction m with
  | zero => decide
  | succ m ih =>
      have ih' :
          3 ^ (2 * (m + 3) + 1) <
            2 ^ (4 * (m + 3)) :=
        ih (by omega)
      have h3 : 0 < 3 ^ (2 * (m + 3) + 1) :=
        Nat.pow_pos (by decide)
      have hleft :
          9 * 3 ^ (2 * (m + 3) + 1) <
            16 * 3 ^ (2 * (m + 3) + 1) :=
        Nat.mul_lt_mul_of_pos_right (by decide : 9 < 16) h3
      have hright :
          16 * 3 ^ (2 * (m + 3) + 1) <
            16 * 2 ^ (4 * (m + 3)) :=
        Nat.mul_lt_mul_of_pos_left ih' (by decide : 0 < 16)
      calc
        3 ^ (2 * (m + 1 + 3) + 1) =
            9 * 3 ^ (2 * (m + 3) + 1) := by
              rw [show 2 * (m + 1 + 3) + 1 =
                2 + (2 * (m + 3) + 1) by omega, Nat.pow_add]
              norm_num
        _ < 16 * 3 ^ (2 * (m + 3) + 1) := hleft
        _ < 16 * 2 ^ (4 * (m + 3)) := hright
        _ = 2 ^ (4 * (m + 1 + 3)) := by
              rw [show 4 * (m + 1 + 3) =
                4 + 4 * (m + 3) by omega, Nat.pow_add]
              norm_num

/-- By depth 4*n a hypothetical minimal bad source has accumulated strictly
more than 2*n odd steps.  Equality would put the path inside the persistent
one-bit corridor while qmin(4*n) is already strictly above 2*n+1. -/
theorem minimal_bad_quadruple_depth_strict_double_diagonal
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    2 * n < oddCount n (4 * n) := by
  have hn : 0 < n := hmin.1.1
  have hgt : 1 < n := by
    have hne : n ≠ 1 := by
      intro heq
      apply hmin.1.2
      subst n
      exact ⟨0, by simp [iter, Terminal]⟩
    omega
  have hn3 : 3 ≤ n := by
    have hodd := positive_minimal_bad_odd hmin
    omega
  have hhalf :=
    nondescending_depth_le_twice_oddCount hn
      (minimal_bad_nondescending_all_depths hmin (4 * n))
  have hge : 2 * n ≤ oddCount n (4 * n) := by omega
  apply Nat.lt_of_le_of_ne hge
  intro heq
  have hqeq : oddCount n (4 * n) = 2 * n := by omega
  have hcorr :=
    minimal_bad_persistent_qmin_corridor
      (k := 4 * n) hmin
      (by rw [hqeq]; omega)
      (by rw [hqeq]; omega)
  have hspec := qmin_spec (4 * n)
  have hcorr' : qmin (4 * n) ≤ 2 * n + 1 := by
    simpa [hqeq] using hcorr
  have hpowle :
      3 ^ qmin (4 * n) ≤ 3 ^ (2 * n + 1) :=
    Nat.pow_le_pow_right (by decide) hcorr'
  have hsep :=
    three_pow_double_succ_lt_two_pow_quadruple n hn3
  omega

#print axioms nondescending_q_le_double_source_qmin_corridor
#print axioms minimal_bad_persistent_qmin_corridor
#print axioms minimal_bad_persistent_survival_or_deficit_one

end SourceProduct
end CollatzFinal
