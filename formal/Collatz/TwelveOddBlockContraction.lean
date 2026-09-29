import Collatz.FourThirdsAdmission

namespace CollatzFinal
namespace SourceProduct

/-- Universal scaled upper bound specialized to a 12-odd shortcut block.

This is the exact all-depth recurrence envelope already proved in
`two_pow_odds_mul_bias_add_depth_le`, specialized without enumerating parity
words. -/
theorem twelve_odd_scaled_bias_bound
    {n k : Nat}
    (hq : oddCount n k = 12) :
    4096 * bias n k ≤ 527345 * 2 ^ k := by
  have h := two_pow_odds_mul_bias_add_depth_le n k
  rw [hq] at h
  have h2 : (2 : Nat) ^ 12 = 4096 := by decide
  have h3 : (3 : Nat) ^ 12 = 531441 := by decide
  rw [h2, h3] at h
  rw [Nat.mul_add] at h
  omega

/-- Any shortcut block containing exactly 12 odd steps and taking at least
20 ordinary steps strictly contracts every start value n >= 262.

The constants are exact:
* 3^12 = 531441,
* 2^12 = 4096,
* 3^12 - 2^12 = 527345,
* at k=20 the worst universal affine-bias envelope is already smaller than
  (2^k-3^12)*262; the gap only increases for larger k.

No parity-word census is used. -/
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
    have h20 : (2 : Nat) ^ 20 = 1048576 := by decide
    rw [h20] at hp
    have hconst : 128 * 531441 ≤ 65 * 1048576 := by decide
    have h65 : 65 * 1048576 ≤ 65 * 2 ^ k :=
      Nat.mul_le_mul_left 65 hp
    have hbound : 128 * 531441 ≤ 65 * 2 ^ k :=
      Nat.le_trans hconst h65
    have hx531 : 531441 ≤ 2 ^ k := by omega
    have hratio : 63 * 2 ^ k ≤ 128 * (2 ^ k - 531441) := by
      omega
    have hxpos : 0 < 2 ^ k := Nat.pow_pos (by decide)
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
  have h3 : (3 : Nat) ^ 12 = 531441 := by decide
  rw [h3] at ha
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
  have hb' :
      4096 * bias n k ≤ 527345 * 2 ^ k := hb
  omega

#print axioms twelve_odd_scaled_bias_bound
#print axioms twelve_odd_long_block_strict_descent

end SourceProduct
end CollatzFinal
