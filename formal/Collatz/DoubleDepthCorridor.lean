import Collatz.DoubleDepthCloseout

namespace CollatzFinal
namespace SourceProduct

theorem oddCount_le_depth (n k : Nat) :
    oddCount n k ≤ k := by
  induction k with
  | zero => simp [oddCount]
  | succ k ih =>
      by_cases h : iter shortcut k n % 2 = 0
      · simp [oddCount, h]
        omega
      · simp [oddCount, h]
        omega

/-- Elementary product control:
    (m+1)^q (m-q) <= m^(q+1) whenever q<=m. -/
theorem adjacent_power_ratio_le
    (m q : Nat) (hq : q ≤ m) :
    (m + 1) ^ q * (m - q) ≤ m ^ (q + 1) := by
  induction q with
  | zero =>
      simp
  | succ q ih =>
      have hqm : q ≤ m := by omega
      have hfac :
          (m + 1) * (m - (q + 1)) ≤ m * (m - q) := by
        have hsmall : m - (q + 1) ≤ m := Nat.sub_le _ _
        have hsub : m - q = (m - (q + 1)) + 1 := by omega
        calc
          (m + 1) * (m - (q + 1)) =
              m * (m - (q + 1)) + (m - (q + 1)) := by
                rw [Nat.add_mul]
                simp
          _ ≤ m * (m - (q + 1)) + m :=
                Nat.add_le_add_left hsmall _
          _ = m * ((m - (q + 1)) + 1) := by
                rw [Nat.mul_add]
                simp
          _ = m * (m - q) := by rw [hsub]
      calc
        (m + 1) ^ (q + 1) * (m - (q + 1)) =
            (m + 1) ^ q * ((m + 1) * (m - (q + 1))) := by
              simp [Nat.pow_succ, Nat.mul_assoc]
        _ ≤ (m + 1) ^ q * (m * (m - q)) :=
              Nat.mul_le_mul_left _ hfac
        _ = m * ((m + 1) ^ q * (m - q)) := by
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
        _ ≤ m * m ^ (q + 1) := Nat.mul_le_mul_left m (ih hqm)
        _ = m ^ ((q + 1) + 1) := by
              simp [Nat.pow_succ, Nat.mul_comm]

/-- Strict version for a positive exponent below m. -/
theorem adjacent_power_ratio_lt
    (m q : Nat) (hqpos : 0 < q) (hq : q < m) :
    (m + 1) ^ q * (m - q) < m ^ (q + 1) := by
  obtain ⟨r, rfl⟩ := Nat.exists_eq_succ_of_ne_zero (by omega : q ≠ 0)
  have hrm : r ≤ m := by omega
  have hfac :
      (m + 1) * (m - (r + 1)) < m * (m - r) := by
    have hsmall : m - (r + 1) < m := by omega
    have hsub : m - r = (m - (r + 1)) + 1 := by omega
    calc
      (m + 1) * (m - (r + 1)) =
          m * (m - (r + 1)) + (m - (r + 1)) := by
            rw [Nat.add_mul]
            simp
      _ < m * (m - (r + 1)) + m :=
            Nat.add_lt_add_left hsmall _
      _ = m * ((m - (r + 1)) + 1) := by
            rw [Nat.mul_add]
            simp
      _ = m * (m - r) := by rw [hsub]
  have hpowpos : 0 < (m + 1) ^ r := Nat.pow_pos (by omega)
  calc
    (m + 1) ^ (r + 1) * (m - (r + 1)) =
        (m + 1) ^ r * ((m + 1) * (m - (r + 1))) := by
          simp [Nat.pow_succ, Nat.mul_assoc]
    _ < (m + 1) ^ r * (m * (m - r)) :=
          (Nat.mul_lt_mul_left hpowpos).2 hfac
    _ = m * ((m + 1) ^ r * (m - r)) := by
          simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    _ ≤ m * m ^ (r + 1) :=
          Nat.mul_le_mul_left m (adjacent_power_ratio_le m r hrm)
    _ = m ^ ((r + 1) + 1) := by
          simp [Nat.pow_succ, Nat.mul_comm]

/-- Source-relative growth bound on a prefix that never drops below its source.
The +1 in each odd shortcut is charged against the fixed source n. -/
theorem source_relative_scaled_orbit_le
    {n k : Nat}
    (hn : 0 < n)
    (hnd : ∀ i, i ≤ k → n ≤ iter shortcut i n) :
    2 ^ k * n ^ oddCount n k * iter shortcut k n ≤
      (3 * n + 1) ^ oddCount n k * n := by
  induction k with
  | zero =>
      simp [iter, oddCount]
  | succ k ih =>
      have hprefix : ∀ i, i ≤ k → n ≤ iter shortcut i n := by
        intro i hi
        exact hnd i (by omega)
      have hi := ih hprefix
      let x := iter shortcut k n
      have hx : 0 < x := by
        dsimp [x]
        exact iter_positive shortcut shortcut_positive k n hn
      have hnx : n ≤ x := by
        dsimp [x]
        exact hnd k (by omega)
      have hd := double_shortcut x
      rw [iter_succ_last]
      by_cases he : x % 2 = 0
      · have hd' : 2 * shortcut x = x := by
          simpa [he] using hd
        simp only [oddCount, x, he, ite_true]
        calc
          2 ^ (k + 1) * n ^ oddCount n k * shortcut x =
              2 ^ k * n ^ oddCount n k * (2 * shortcut x) := by
                simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                  Nat.mul_left_comm]
          _ = 2 ^ k * n ^ oddCount n k * x := by rw [hd']
          _ ≤ (3 * n + 1) ^ oddCount n k * n := hi
      · have hd' : 2 * shortcut x = 3 * x + 1 := by
          simpa [he] using hd
        have hlocal : n * (3 * x + 1) ≤ (3 * n + 1) * x := by
          calc
            n * (3 * x + 1) = 3 * n * x + n := by
              simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm,
                Nat.mul_left_comm]
            _ ≤ 3 * n * x + x := Nat.add_le_add_left hnx _
            _ = x * (3 * n) + x := by
              simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
            _ = x * (3 * n + 1) := by
              rw [Nat.mul_add]
              simp
            _ = (3 * n + 1) * x := Nat.mul_comm _ _
        simp only [oddCount, x, he, ite_false]
        calc
          2 ^ (k + 1) * n ^ (oddCount n k + 1) * shortcut x =
              (2 ^ k * n ^ oddCount n k) *
                (n * (2 * shortcut x)) := by
                  simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                    Nat.mul_left_comm]
          _ = (2 ^ k * n ^ oddCount n k) * (n * (3 * x + 1)) := by
                rw [hd']
          _ ≤ (2 ^ k * n ^ oddCount n k) * ((3 * n + 1) * x) :=
                Nat.mul_le_mul_left _ hlocal
          _ = (3 * n + 1) *
                (2 ^ k * n ^ oddCount n k * x) := by
                  simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
          _ ≤ (3 * n + 1) * ((3 * n + 1) ^ oddCount n k * n) :=
                Nat.mul_le_mul_left (3 * n + 1) hi
          _ = (3 * n + 1) ^ (oddCount n k + 1) * n := by
                simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
                  Nat.mul_left_comm]

/-- At the deterministic checkpoint 2*n, a minimal bad source can sit at most
one odd step below the deterministic coefficient threshold. -/
theorem minimal_bad_double_depth_qmin_corridor
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    qmin (2 * n) ≤ oddCount n (2 * n) + 1 := by
  let q := oddCount n (2 * n)
  have hn : 0 < n := hmin.1.1
  have hgt : 1 < n := by
    have hne : n ≠ 1 := by
      intro heq
      apply hmin.1.2
      subst n
      exact ⟨0, by simp [iter, Terminal]⟩
    omega
  have hqdepth : q ≤ 2 * n := by
    dsimp [q]
    exact oddCount_le_depth n (2 * n)
  have hqpos : 0 < q := by
    have hdiag := minimal_bad_enters_post_diagonal_by_double hmin
    dsimp [q]
    omega
  have hrel :
      2 ^ (2 * n) * n ^ q * iter shortcut (2 * n) n ≤
        (3 * n + 1) ^ q * n := by
    dsimp [q]
    exact source_relative_scaled_orbit_le hn
      (fun i _ => minimal_bad_nondescending_all_depths hmin i)
  have hnd := minimal_bad_nondescending_all_depths hmin (2 * n)
  have hleft :
      2 ^ (2 * n) * n ^ (q + 1) ≤
        (3 * n + 1) ^ q * n := by
    have hm := Nat.mul_le_mul_left (2 ^ (2 * n) * n ^ q) hnd
    have hpow : n ^ (q + 1) = n ^ q * n := by
      rw [Nat.pow_succ]
    rw [hpow]
    exact Nat.le_trans
      (by simpa [Nat.mul_assoc] using hm) hrel
  have hratio :
      (3 * n + 1) ^ q * n <
        (3 * n) ^ (q + 1) := by
    have hq3 : q < 3 * n := by omega
    have hbase :=
      adjacent_power_ratio_lt (3 * n) q hqpos hq3
    have hnle : n ≤ 3 * n - q := by omega
    have hmul :
        (3 * n + 1) ^ q * n ≤
          (3 * n + 1) ^ q * (3 * n - q) :=
      Nat.mul_le_mul_left _ hnle
    exact Nat.lt_of_le_of_lt hmul (by simpa [Nat.add_assoc] using hbase)
  apply Nat.le_of_not_gt
  intro hbad
  have hfail :
      3 ^ (q + 1) < 2 ^ (2 * n) :=
    lt_qmin_fails (by omega)
  have hpowmul :
      (3 * n) ^ (q + 1) =
        3 ^ (q + 1) * n ^ (q + 1) := by
    rw [Nat.mul_pow]
  have hright :
      (3 * n) ^ (q + 1) <
        2 ^ (2 * n) * n ^ (q + 1) := by
    rw [hpowmul]
    exact Nat.mul_lt_mul_of_pos_right hfail (Nat.pow_pos hn)
  omega

#print axioms oddCount_le_depth
#print axioms adjacent_power_ratio_le
#print axioms adjacent_power_ratio_lt
#print axioms source_relative_scaled_orbit_le
#print axioms minimal_bad_double_depth_qmin_corridor

end SourceProduct
end CollatzFinal
