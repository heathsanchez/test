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
        simp only [oddCount, bias, h, if_false]
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
        have hadd := Nat.add_le_add
          (by simpa [q, B] using ih) hextra
        simp only [oddCount, bias, h, if_true]
        change 2 ^ q * (B + 2 ^ (k + 1)) ≤
          2 ^ (k + 1) * 3 ^ q
        simpa [Nat.pow_succ, Nat.mul_add, Nat.add_mul,
          Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hadd
      · let q := oddCount n k
        let B := bias n k
        have hmul :=
          Nat.mul_le_mul_left 6 (by simpa [q, B] using ih)
        simp only [oddCount, bias, h, if_false]
        change
          2 ^ (q + 1) * (3 * B + 2 ^ k + 2 ^ (k + 1)) ≤
            2 ^ (k + 1) * 3 ^ (q + 1)
        simpa [Nat.pow_succ, Nat.mul_add, Nat.add_mul,
          Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hmul

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

end SourceProduct
end CollatzFinal
