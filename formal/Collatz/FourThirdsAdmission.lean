import Collatz.OwnerBoundarySplit

namespace CollatzFinal
namespace SourceProduct

/-- Elementary base comparison used by the exact affine-bias envelope. -/
theorem two_pow_le_three_pow (q : Nat) :
    2 ^ q ≤ 3 ^ q := by
  induction q with
  | zero => simp
  | succ q ih =>
      calc
        2 ^ (q + 1) = 2 ^ q * 2 := by rw [Nat.pow_succ]
        _ ≤ 3 ^ q * 2 := Nat.mul_le_mul_right 2 ih
        _ ≤ 3 ^ q * 3 := Nat.mul_le_mul_left (3 ^ q) (by decide)
        _ = 3 ^ (q + 1) := by rw [Nat.pow_succ]

/-- Exact lower affine-bias envelope.

For q odd steps in k shortcut steps, the intercept is at least the intercept
of the earliest possible q odd positions.  The subtraction-free form is
  3^q <= B + 2^q.
This is proved directly from the orbit recurrence, not from a parity-word
enumeration. -/
theorem three_pow_le_bias_add_two_pow (n : Nat) :
    ∀ k,
      3 ^ oddCount n k ≤
        bias n k + 2 ^ oddCount n k := by
  intro k
  induction k with
  | zero =>
      simp [oddCount, bias]
  | succ k ih =>
      by_cases h : iter shortcut k n % 2 = 0
      · simpa [oddCount, bias, h] using ih
      · let q := oddCount n k
        let B := bias n k
        have hqk : q ≤ k := by
          simpa [q] using oddCount_le_depth n k
        have hpow : 2 ^ q ≤ 2 ^ k :=
          Nat.pow_le_pow_right (by decide) hqk
        have h3 :
            3 * 3 ^ q ≤ 3 * (B + 2 ^ q) :=
          Nat.mul_le_mul_left 3 (by simpa [q, B] using ih)
        simp only [oddCount, bias, h, ite_false]
        change 3 ^ (q + 1) ≤ 3 * B + 2 ^ k + 2 ^ (q + 1)
        rw [Nat.pow_succ, Nat.pow_succ]
        have hrewrite :
            3 ^ q * 3 = 3 * 3 ^ q := by omega
        rw [hrewrite]
        have hB :
            3 * (B + 2 ^ q) =
              3 * B + 3 * 2 ^ q := by
          omega
        rw [hB] at h3
        omega

/-- Exact upper affine-bias envelope.

For q odd steps in k shortcut steps, the intercept is at most that of the
latest possible q odd positions.  Multiplying by 2^q avoids subtraction:
  2^q * (B + 2^k) <= 2^k * 3^q.
Again this is an all-depth recurrence theorem. -/
theorem two_pow_odds_mul_bias_add_depth_le
    (n : Nat) :
    ∀ k,
      2 ^ oddCount n k * (bias n k + 2 ^ k) ≤
        2 ^ k * 3 ^ oddCount n k := by
  intro k
  induction k with
  | zero =>
      simp [oddCount, bias]
  | succ k ih =>
      by_cases h : iter shortcut k n % 2 = 0
      · let q := oddCount n k
        let B := bias n k
        have hp : 2 ^ q ≤ 3 ^ q := two_pow_le_three_pow q
        have hextra :
            2 ^ q * 2 ^ k ≤ 2 ^ k * 3 ^ q := by
          have hm := Nat.mul_le_mul_left (2 ^ k) hp
          simpa [Nat.mul_comm, Nat.mul_left_comm, Nat.mul_assoc] using hm
        have hbase :
            2 ^ q * (B + 2 ^ k) ≤ 2 ^ k * 3 ^ q := by
          simpa [q, B] using ih
        simp only [oddCount, bias, h, ite_true]
        change 2 ^ q * (B + 2 ^ (k + 1)) ≤
          2 ^ (k + 1) * 3 ^ q
        have hpowadd :
            2 ^ (k + 1) = 2 ^ k + 2 ^ k := by
          rw [Nat.pow_succ, Nat.mul_two]
        calc
          2 ^ q * (B + 2 ^ (k + 1)) =
              2 ^ q * (B + 2 ^ k) + 2 ^ q * 2 ^ k := by
                rw [hpowadd]
                simp only [Nat.mul_add]
                omega
          _ ≤ 2 ^ k * 3 ^ q + 2 ^ k * 3 ^ q :=
                Nat.add_le_add hbase hextra
          _ = 2 ^ (k + 1) * 3 ^ q := by
                rw [hpowadd, Nat.add_mul]
      · let q := oddCount n k
        let B := bias n k
        have hbase :
            2 ^ q * (B + 2 ^ k) ≤ 2 ^ k * 3 ^ q := by
          simpa [q, B] using ih
        have hmul := Nat.mul_le_mul_left 6 hbase
        simp only [oddCount, bias, h, ite_false]
        change
          2 ^ (q + 1) * (3 * B + 2 ^ k + 2 ^ (k + 1)) ≤
            2 ^ (k + 1) * 3 ^ (q + 1)
        have hinner :
            3 * B + 2 ^ k + 2 ^ (k + 1) =
              3 * (B + 2 ^ k) := by
          rw [Nat.pow_succ, Nat.mul_two]
          omega
        calc
          2 ^ (q + 1) * (3 * B + 2 ^ k + 2 ^ (k + 1)) =
              6 * (2 ^ q * (B + 2 ^ k)) := by
                rw [hinner, Nat.pow_succ]
                simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
                omega
          _ ≤ 6 * (2 ^ k * 3 ^ q) := hmul
          _ = 2 ^ (k + 1) * 3 ^ (q + 1) := by
                rw [Nat.pow_succ, Nat.pow_succ]
                let C := 2 ^ k
                let D := 3 ^ q
                change 6 * (C * D) = (C * 2) * (D * 3)
                calc
                  6 * (C * D) = (2 * 3) * (C * D) := by rfl
                  _ = 2 * (3 * (C * D)) := by
                    exact Nat.mul_assoc 2 3 (C * D)
                  _ = 2 * ((3 * C) * D) := by
                    congr 1
                    exact (Nat.mul_assoc 3 C D).symm
                  _ = 2 * ((C * 3) * D) := by
                    congr 1
                    rw [Nat.mul_comm 3 C]
                  _ = 2 * (C * (3 * D)) := by
                    congr 1
                    exact Nat.mul_assoc C 3 D
                  _ = (2 * C) * (3 * D) := by
                    exact (Nat.mul_assoc 2 C (3 * D)).symm
                  _ = (C * 2) * (3 * D) := by
                    rw [Nat.mul_comm 2 C]
                  _ = (C * 2) * (D * 3) := by
                    congr 1
                    rw [Nat.mul_comm 3 D]

/-- The V17 synthetic local tuple (27,53,36,451) is excluded already by the
universal lower bias envelope.  This is a regression theorem documenting that
the first scalar countermodel was not source-admissible. -/
theorem v17_synthetic_27_53_36_451_bias_too_small :
    9691710869211125 <
      3 ^ 36 - 2 ^ 36 := by
  decide

#print axioms three_pow_le_bias_add_two_pow
#print axioms two_pow_odds_mul_bias_add_depth_le
#print axioms v17_synthetic_27_53_36_451_bias_too_small


/-- Universal scaled upper bound specialized to a 12-odd shortcut block. -/
theorem twelve_odd_scaled_bias_bound
    {n k : Nat}
    (hq : oddCount n k = 12) :
    4096 * bias n k ≤ 527345 * 2 ^ k := by
  have h := two_pow_odds_mul_bias_add_depth_le n k
  rw [hq] at h
  norm_num at h ⊢
  rw [Nat.mul_add] at h
  omega

/-- Any shortcut block containing exactly 12 odd steps and taking at least
20 ordinary steps strictly contracts every start value n >= 262. -/
theorem twelve_odd_long_block_strict_descent
    {n k : Nat}
    (hn : 262 ≤ n)
    (hk : 20 ≤ k)
    (hq : oddCount n k = 12) :
    iter shortcut k n < n := by
  have hb := twelve_odd_scaled_bias_bound (n := n) (k := k) hq
  have hp : 2 ^ 20 ≤ 2 ^ k := by
    exact Nat.pow_le_pow_right (by decide) hk
  have hgap262 :
      527345 * 2 ^ k <
        4096 * (2 ^ k - 531441) * 262 := by
    norm_num at hp ⊢
    omega
  have hgap :
      527345 * 2 ^ k <
        4096 * (2 ^ k - 531441) * n := by
    have hm :
        4096 * (2 ^ k - 531441) * 262 ≤
          4096 * (2 ^ k - 531441) * n := by
      exact Nat.mul_le_mul_left (4096 * (2 ^ k - 531441)) hn
    exact Nat.lt_of_lt_of_le hgap262 hm
  have ha := exact_affine n k
  rw [hq] at ha
  norm_num at ha
  apply Classical.byContradiction
  intro hnot
  have hnd : n ≤ iter shortcut k n := by omega
  have hdef :
      (2 ^ k - 531441) * n ≤ bias n k := by
    rw [Nat.sub_mul]
    have hm := Nat.mul_le_mul_left (2 ^ k) hnd
    rw [ha] at hm
    omega
  have hdefScaled :
      4096 * (2 ^ k - 531441) * n ≤
        4096 * bias n k := by
    have hm := Nat.mul_le_mul_left 4096 hdef
    simpa [Nat.mul_assoc] using hm
  omega

#print axioms twelve_odd_scaled_bias_bound
#print axioms twelve_odd_long_block_strict_descent

end SourceProduct
end CollatzFinal
