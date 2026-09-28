import Collatz.DoubleDepthCorridor

namespace CollatzFinal
namespace SourceProduct

theorem qmin_le_of_pow_le
    {k Q : Nat}
    (hpow : 2 ^ k ≤ 3 ^ Q) :
    qmin k ≤ Q := by
  apply Nat.le_of_not_gt
  intro hlt
  have hf := lt_qmin_fails (by omega : Q < qmin k)
  omega

theorem sixteen_pow_le_twentyseven_pow (m : Nat) :
    16 ^ m ≤ 27 ^ m := by
  induction m with
  | zero => simp
  | succ m ih =>
      calc
        16 ^ (m + 1) = 16 ^ m * 16 := by rw [Nat.pow_succ]
        _ ≤ 27 ^ m * 16 := Nat.mul_le_mul_right 16 ih
        _ ≤ 27 ^ m * 27 := Nat.mul_le_mul_left (27 ^ m) (by decide)
        _ = 27 ^ (m + 1) := by rw [Nat.pow_succ]

/-- For an odd source n=2m+1, the deterministic coefficient threshold at
ordinary depth 2n is at most 3m+2. -/
theorem qmin_double_odd_upper
    {n : Nat}
    (hodd : n % 2 = 1) :
    qmin (2 * n) ≤ 3 * (n / 2) + 2 := by
  let m := n / 2
  have hnform : n = 2 * m + 1 := by
    have hd := Nat.mod_add_div n 2
    dsimp [m]
    omega
  have h16 := sixteen_pow_le_twentyseven_pow m
  have hpow : 2 ^ (2 * n) ≤ 3 ^ (3 * m + 2) := by
    rw [hnform]
    calc
      2 ^ (2 * (2 * m + 1)) = 16 ^ m * 4 := by
        rw [show 2 * (2 * m + 1) = 4 * m + 2 by omega, Nat.pow_add]
        have hfour : 2 ^ (4 * m) = 16 ^ m := by
          calc
            2 ^ (4 * m) = (2 ^ 4) ^ m := by rw [Nat.pow_mul]
            _ = 16 ^ m := by rfl
        rw [hfour]
      _ ≤ 27 ^ m * 9 := Nat.mul_le_mul h16 (by decide)
      _ = 3 ^ (3 * m + 2) := by
        rw [Nat.pow_add]
        have hthree : 3 ^ (3 * m) = 27 ^ m := by
          calc
            3 ^ (3 * m) = (3 ^ 3) ^ m := by rw [Nat.pow_mul]
            _ = 27 ^ m := by rfl
        rw [hthree]
  simpa [m] using qmin_le_of_pow_le hpow

/-- Exact deficit-one checkpoint consequence.
If the minimal bad source is one odd step below coefficient survival at 2n,
then its endpoint is forced into the narrow interval [n,2n). -/
theorem minimal_bad_double_depth_deficit_one_lt_double
    {n : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hdef :
      oddCount n (2 * n) + 1 = qmin (2 * n)) :
    iter shortcut (2 * n) n < 2 * n := by
  let q := oddCount n (2 * n)
  let y := iter shortcut (2 * n) n
  have hn : 0 < n := hmin.1.1
  have hgt : 1 < n := by
    have hne : n ≠ 1 := by
      intro heq
      apply hmin.1.2
      subst n
      exact ⟨0, by simp [iter, Terminal]⟩
    omega
  have hodd : n % 2 = 1 := positive_minimal_bad_odd hmin
  let m := n / 2
  have hnform : n = 2 * m + 1 := by
    have hd := Nat.mod_add_div n 2
    dsimp [m]
    omega
  have hqupper : q + 1 ≤ 3 * m + 2 := by
    have hqm := qmin_double_odd_upper hodd
    rw [← hdef] at hqm
    simpa [m, q] using hqm
  have htwq : 2 * q < 3 * n := by
    rw [hnform]
    omega
  have hqpos : 0 < q := by
    have hdiag := minimal_bad_enters_post_diagonal_by_double hmin
    simpa [q] using (Nat.lt_of_lt_of_le hn hdiag)
  have hq3 : q < 3 * n := by omega
  have hrel :
      2 ^ (2 * n) * n ^ q * y ≤
        (3 * n + 1) ^ q * n := by
    simpa [q, y] using
      source_relative_scaled_orbit_le hn
        (fun i _ => minimal_bad_nondescending_all_depths hmin i)
  have hratio :
      (3 * n + 1) ^ q * (3 * n - q) <
        (3 * n) ^ (q + 1) :=
    adjacent_power_ratio_lt (3 * n) q hqpos hq3
  have hrelScaled :
      2 ^ (2 * n) * n ^ q * y * (3 * n - q) ≤
        ((3 * n + 1) ^ q * n) * (3 * n - q) := by
    exact Nat.mul_le_mul_right (3 * n - q) hrel
  have hratioN :
      ((3 * n + 1) ^ q * n) * (3 * n - q) <
        (3 * n) ^ (q + 1) * n := by
    have hm := (Nat.mul_lt_mul_right hn).2 hratio
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hm
  have hqfail : 3 ^ q < 2 ^ (2 * n) := by
    apply lt_qmin_fails
    rw [← hdef]
    omega
  have h3q :
      3 ^ (q + 1) < 3 * 2 ^ (2 * n) := by
    have hm := (Nat.mul_lt_mul_right (by decide : 0 < 3)).2 hqfail
    simpa [Nat.pow_succ, Nat.mul_comm] using hm
  have hpowN :
      (3 * n) ^ (q + 1) * n =
        3 ^ (q + 1) * n ^ (q + 2) := by
    rw [Nat.mul_pow]
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hratioUpper :
      (3 * n) ^ (q + 1) * n <
        3 * 2 ^ (2 * n) * n ^ (q + 2) := by
    rw [hpowN]
    have hp : 0 < n ^ (q + 2) := Nat.pow_pos hn
    have hm := (Nat.mul_lt_mul_right hp).2 h3q
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hm
  have hupper :
      2 ^ (2 * n) * n ^ q * y * (3 * n - q) <
        3 * 2 ^ (2 * n) * n ^ (q + 2) :=
    Nat.lt_of_le_of_lt hrelScaled
      (Nat.lt_trans hratioN hratioUpper)
  apply Classical.byContradiction
  intro hnot
  have hyge : 2 * n ≤ y := by
    dsimp [y] at hnot ⊢
    omega
  have hlin : 3 * n < 2 * (3 * n - q) := by
    omega
  have hlinN :
      3 * n * n < 2 * (3 * n - q) * n :=
    (Nat.mul_lt_mul_right hn).2 hlin
  have hyprod :
      3 * n * n < y * (3 * n - q) := by
    have hmono :
        (2 * n) * (3 * n - q) ≤ y * (3 * n - q) :=
      Nat.mul_le_mul_right (3 * n - q) hyge
    have hreorder :
        2 * (3 * n - q) * n =
          (2 * n) * (3 * n - q) := by
      simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    rw [hreorder] at hlinN
    exact Nat.lt_of_lt_of_le hlinN hmono
  have hfactor :
      0 < 2 ^ (2 * n) * n ^ q :=
    Nat.mul_pos (Nat.pow_pos (by decide)) (Nat.pow_pos hn)
  have hlower0 :=
    (Nat.mul_lt_mul_left hfactor).2 hyprod
  have hlower :
      3 * 2 ^ (2 * n) * n ^ (q + 2) <
        2 ^ (2 * n) * n ^ q * y * (3 * n - q) := by
    have heq :
        (2 ^ (2 * n) * n ^ q) * (3 * n * n) =
          3 * 2 ^ (2 * n) * n ^ (q + 2) := by
      simp [Nat.pow_add, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    rw [heq] at hlower0
    simpa [Nat.mul_assoc] using hlower0
  exact (Nat.lt_asymm hupper hlower)

/-- The deficit-one checkpoint endpoint is therefore odd and genuinely
source-relative: it lies in [n,2n). -/
theorem minimal_bad_double_depth_deficit_one_interval
    {n : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hdef :
      oddCount n (2 * n) + 1 = qmin (2 * n)) :
    n ≤ iter shortcut (2 * n) n ∧
    iter shortcut (2 * n) n < 2 * n ∧
    iter shortcut (2 * n) n % 2 = 1 := by
  have hlow := minimal_bad_nondescending_all_depths hmin (2 * n)
  have hhi := minimal_bad_double_depth_deficit_one_lt_double hmin hdef
  have hoddne :=
    minimal_bad_below_double_forces_odd hmin hhi
  have hodd : iter shortcut (2 * n) n % 2 = 1 := by
    have hm := Nat.mod_lt (iter shortcut (2 * n) n) (by omega : 0 < 2)
    omega
  exact ⟨hlow, hhi, hodd⟩

#print axioms qmin_le_of_pow_le
#print axioms sixteen_pow_le_twentyseven_pow
#print axioms qmin_double_odd_upper
#print axioms minimal_bad_double_depth_deficit_one_lt_double
#print axioms minimal_bad_double_depth_deficit_one_interval

end SourceProduct
end CollatzFinal
