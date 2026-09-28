import Collatz.QuarterSplice

namespace CollatzFinal
namespace SourceProduct

/-- A source-relative multiplicative envelope that does not assume coefficient
survival.  Every even shortcut step contributes an exact factor 1/2; every odd
shortcut step is at most a factor 2 on a positive orbit. -/
theorem scaled_orbit_le_four_pow_odds
    {n : Nat} (hn : 0 < n) :
    ∀ k, 2 ^ k * iter shortcut k n ≤
      4 ^ oddCount n k * n := by
  intro k
  induction k with
  | zero =>
      simp [iter, oddCount]
  | succ k ih =>
      let x := iter shortcut k n
      have hx : 0 < x := by
        dsimp [x]
        exact iter_positive shortcut shortcut_positive k n hn
      have hd := double_shortcut x
      rw [iter_succ_last]
      by_cases he : x % 2 = 0
      · have hd' : 2 * shortcut x = x := by
          simpa [he] using hd
        simp only [oddCount, x, he, ite_true]
        calc
          2 ^ (k + 1) * shortcut x =
              2 ^ k * (2 * shortcut x) := by
                simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                  Nat.mul_left_comm]
          _ = 2 ^ k * x := by rw [hd']
          _ ≤ 4 ^ oddCount n k * n := ih
      · have hd' : 2 * shortcut x = 3 * x + 1 := by
          simpa [he] using hd
        have hfour : 3 * x + 1 ≤ 4 * x := by
          omega
        simp only [oddCount, x, he, ite_false]
        calc
          2 ^ (k + 1) * shortcut x =
              2 ^ k * (2 * shortcut x) := by
                simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                  Nat.mul_left_comm]
          _ = 2 ^ k * (3 * x + 1) := by rw [hd']
          _ ≤ 2 ^ k * (4 * x) := Nat.mul_le_mul_left _ hfour
          _ = 4 * (2 ^ k * x) := by
                simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
          _ ≤ 4 * (4 ^ oddCount n k * n) :=
                Nat.mul_le_mul_left 4 ih
          _ = 4 ^ (oddCount n k + 1) * n := by
                simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                  Nat.mul_left_comm]

/-- Any hypothetical minimal bad source has accumulated at least n odd shortcut
steps by ordinary depth 2*n.  Unlike the older high-odd bridge, this needs no
coefficient-survival premise. -/
theorem minimal_bad_enters_post_diagonal_by_double
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    n ≤ oddCount n (2 * n) := by
  have hn : 0 < n := hmin.1.1
  have henv := scaled_orbit_le_four_pow_odds hn (2 * n)
  have hnd := minimal_bad_nondescending_all_depths hmin (2 * n)
  have hscaled :
      2 ^ (2 * n) * n ≤
        4 ^ oddCount n (2 * n) * n := by
    exact Nat.le_trans (Nat.mul_le_mul_left (2 ^ (2 * n)) hnd) henv
  have hcancel :
      2 ^ (2 * n) ≤ 4 ^ oddCount n (2 * n) := by
    exact (Nat.mul_le_mul_right hn).1
      (by simpa [Nat.mul_comm, Nat.mul_left_comm, Nat.mul_assoc] using hscaled)
  apply Nat.le_of_not_gt
  intro hq
  have hexp :
      2 * oddCount n (2 * n) < 2 * n := by omega
  have hp :
      2 ^ (2 * oddCount n (2 * n)) < 2 ^ (2 * n) := by
    exact Nat.pow_lt_pow_right (by decide : 1 < 2) hexp
  have hfour :
      4 ^ oddCount n (2 * n) =
        2 ^ (2 * oddCount n (2 * n)) := by
    rw [show 4 = 2 ^ 2 by decide, ← Nat.pow_mul]
  rw [hfour] at hcancel
  omega

/-- Consequently the exact V8 post-diagonal source fiber is not merely a
possible late regime: every minimal bad source enters it by depth 2*n. -/
theorem minimal_bad_double_depth_is_canonical
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    let k := 2 * n
    let q := oddCount n k
    n ≤ q := by
  simpa using minimal_bad_enters_post_diagonal_by_double hmin

#print axioms scaled_orbit_le_four_pow_odds
#print axioms minimal_bad_enters_post_diagonal_by_double
#print axioms minimal_bad_double_depth_is_canonical

end SourceProduct
end CollatzFinal
