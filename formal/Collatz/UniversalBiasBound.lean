import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-- A coarse but completely unconditional affine-bias bound.

It deliberately uses no coefficient-survival hypothesis.  The only state
needed is the number of odd shortcut steps already taken. -/
theorem bias_le_dyadic_ternary_envelope (n k : Nat) :
    bias n k ≤ 2 ^ k * 3 ^ oddCount n k := by
  induction k with
  | zero =>
      simp [bias, oddCount]
  | succ k ih =>
      by_cases h : iter shortcut k n % 2 = 0
      · simp only [bias, oddCount, h, ite_true]
        let A := 2 ^ k * 3 ^ oddCount n k
        have hApos : 0 < A := by
          dsimp [A]
          exact Nat.mul_pos (Nat.pow_pos (by decide)) (Nat.pow_pos (by decide))
        have hdouble : A ≤ 2 * A := by omega
        calc
          bias n k ≤ A := by simpa [A] using ih
          _ ≤ 2 ^ (k + 1) * 3 ^ oddCount n k := by
            simpa [A, Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm,
              Nat.mul_left_comm] using hdouble
      · simp only [bias, oddCount, h, ite_false]
        let A := 2 ^ k * 3 ^ oddCount n k
        have h3pos : 0 < 3 ^ oddCount n k :=
          Nat.pow_pos (by decide)
        have h3one : 1 ≤ 3 ^ oddCount n k := by omega
        have hk_le_A : 2 ^ k ≤ A := by
          have hm := Nat.mul_le_mul_left (2 ^ k) h3one
          simpa [A] using hm
        have h3ih : 3 * bias n k ≤ 3 * A := by
          exact Nat.mul_le_mul_left 3 (by simpa [A] using ih)
        have hfour : 3 * bias n k + 2 ^ k ≤ 4 * A := by
          omega
        have hApos : 0 < A := by
          dsimp [A]
          exact Nat.mul_pos (Nat.pow_pos (by decide)) h3pos
        have hsix : 4 * A ≤ (2 * 3) * A := by omega
        calc
          3 * bias n k + 2 ^ k ≤ 4 * A := hfour
          _ ≤ (2 * 3) * A := hsix
          _ = 2 ^ (k + 1) * 3 ^ (oddCount n k + 1) := by
            dsimp [A]
            simp only [Nat.pow_succ]
            ac_rfl

/-- Any shortcut block with exactly twelve odd steps and length at least twenty
strictly contracts every starting value above the tiny absolute threshold
4*3^12.  This is the source-independent contraction law used by the V27
blocked 12/19 chamber.

The constants are intentionally loose: the exact sharp threshold is 262, but
the coarse bound is enough for the V23 source floor by thirteen orders of
magnitude and has a much smaller proof surface. -/
theorem twelve_odd_long_block_contracts
    {x k : Nat}
    (hk : 20 ≤ k)
    (hq : oddCount x k = 12)
    (hx : 4 * 3 ^ 12 < x) :
    iter shortcut k x < x := by
  have ha := exact_affine x k
  have hb := bias_le_dyadic_ternary_envelope x k
  rw [hq] at ha hb
  have hp20 : 2 ^ 20 ≤ 2 ^ k := by
    exact Nat.pow_le_pow_right (by decide) hk
  have hcoef0 : 4 * 3 ^ 12 < 3 * 2 ^ 20 := by decide
  have hcoef : 4 * 3 ^ 12 < 3 * 2 ^ k := by
    have hmul : 3 * 2 ^ 20 ≤ 3 * 2 ^ k :=
      Nat.mul_le_mul_left 3 hp20
    exact Nat.lt_of_lt_of_le hcoef0 hmul
  have hxpos : 0 < x := by omega
  have hkpos : 0 < 2 ^ k := Nat.pow_pos (by decide)
  have h1 :
      (4 * 3 ^ 12) * x < (3 * 2 ^ k) * x :=
    Nat.mul_lt_mul_of_pos_right hcoef hxpos
  have h2 :
      (4 * 3 ^ 12) * (2 ^ k) < x * (2 ^ k) :=
    Nat.mul_lt_mul_of_pos_right hx hkpos
  have hscaled :
      2 ^ k * iter shortcut k x ≤
        3 ^ 12 * x + 2 ^ k * 3 ^ 12 := by
    omega
  let A := 3 ^ 12 * x
  let B := 2 ^ k * 3 ^ 12
  let C := 2 ^ k * x
  have h1' : 4 * A < 3 * C := by
    dsimp [A, C]
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using h1
  have h2' : 4 * B < C := by
    dsimp [B, C]
    simpa [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using h2
  have htargetABC : A + B < C := by omega
  have htarget :
      3 ^ 12 * x + 2 ^ k * 3 ^ 12 < 2 ^ k * x := by
    simpa [A, B, C] using htargetABC
  have hstrict :
      2 ^ k * iter shortcut k x < 2 ^ k * x :=
    Nat.lt_of_le_of_lt hscaled htarget
  by_cases hlt : iter shortcut k x < x
  · exact hlt
  · have hge : x ≤ iter shortcut k x := by omega
    have hmul := Nat.mul_le_mul_left (2 ^ k) hge
    omega

/-- The sole V23 affine cell starts far above the universal blocked-block
threshold. -/
theorem v23_source_floor_above_block_threshold :
    4 * 3 ^ 12 < 38_911_100_780_481_085_467 := by
  decide

#print axioms bias_le_dyadic_ternary_envelope
#print axioms twelve_odd_long_block_contracts
#print axioms v23_source_floor_above_block_threshold

end SourceProduct
end CollatzFinal
