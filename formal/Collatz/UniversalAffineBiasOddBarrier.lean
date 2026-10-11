import Collatz.SourceProductAffine
import Collatz.UniversalFutureClassFrontier

namespace CollatzFinal
namespace SourceProduct

/-!
V180 — UNCONDITIONAL ALL-DEPTH TRUE +1 AFFINE BIAS BOUND.

For every genuine natural source and every genuine shortcut clock k:
bias(n,k)+2^k <= 2^k*3^oddCount(n,k).

A large source with 3^oddCount < 2^k must descend.
At clock12, every n>=8192 with <=7 odd shortcut steps descends.
This isolates a necessary high-odd parity corridor for an alleged
least bad integer, but DOES NOT establish Collatz convergence.
-/

theorem v180_bias_plus_power_le (n k : Nat) :
    bias n k + 2^k <= 2^k * 3^(oddCount n k) := by
  induction k with
  | zero =>
      simp [bias, oddCount]
  | succ k ih =>
      by_cases h : iter shortcut k n % 2 = 0
      · have hthree : 0 < 3^(oddCount n k) :=
          Nat.pow_pos (by decide)
        have hOne : 1 <= 3^(oddCount n k) := by omega
        have hp : 2^k <= 2^k * 3^(oddCount n k) := by
          calc
            2^k = 2^k*1 := by simp
            _ <= 2^k*3^(oddCount n k) :=
              Nat.mul_le_mul_left _ hOne
        have hh :
            (bias n k + 2^k) + 2^k <=
              2^k*3^(oddCount n k) +
              2^k*3^(oddCount n k) :=
          Nat.add_le_add ih hp
        simpa [bias, oddCount, h, Nat.pow_succ,
          Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm,
          Nat.add_assoc] using hh
      · have hthree :
            3*(bias n k+2^k) <=
              3*(2^k*3^(oddCount n k)) :=
          Nat.mul_le_mul_left 3 ih
        have hBias : bias n (k+1) + 2^(k+1) =
            3*(bias n k+2^k) := by
          simp [bias, oddCount, h, Nat.pow_succ,
            Nat.mul_add, Nat.add_mul, Nat.mul_assoc]
        rw [hBias]
        calc
          3*(bias n k+2^k) <=
              3*(2^k*3^(oddCount n k)) := hthree
          _ <= 2^(k+1)*3^(oddCount n (k+1)) := by
            simp [oddCount, h, Nat.pow_succ,
              Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
            omega

theorem v180_bias_strict (n k : Nat) :
    bias n k < 2^k * 3^(oddCount n k) := by
  have hh := v180_bias_plus_power_le n k
  have hp : 0 < 2^k := Nat.pow_pos (by decide)
  omega

theorem v180_descent_of_source_height_and_coefficient
    (n k : Nat)
    (hHeight : 2^k*3^(oddCount n k) <= n)
    (hCoeff : 3^(oddCount n k) < 2^k) :
    iter shortcut k n < n := by
  let A := 3^(oddCount n k)
  let P := 2^k
  have hBias : bias n k < n := by
    have hh := v180_bias_strict n k
    dsimp [A,P] at *
    omega
  have hSlope : A+1 <= P := by
    dsimp [A,P]
    omega
  have hMult : (A+1)*n <= P*n :=
    Nat.mul_le_mul_right n hSlope
  have hAffine : P*iter shortcut k n =
      A*n + bias n k := by
    simpa [A,P] using exact_affine n k
  have hStrict : A*n + bias n k < P*n := by
    calc
      A*n + bias n k < A*n + n :=
        Nat.add_lt_add_left hBias _
      _ = (A+1)*n := by simp [Nat.add_mul]
      _ <= P*n := hMult
  by_contra hnot
  have hnond : n <= iter shortcut k n :=
    Nat.le_of_not_lt hnot
  have hScale : P*n <= P*iter shortcut k n :=
    Nat.mul_le_mul_left P hnond
  rw [hAffine] at hScale
  omega

theorem v180_large_source_crossing_descends
    (n k : Nat) (hHeight : 2^(2*k) <= n)
    (hCoeff : 3^(oddCount n k) < 2^k) :
    iter shortcut k n < n := by
  have hSquare : 2^k*2^k = 2^(2*k) := by
    rw [← pow_add]
    congr 1
    omega
  have hMult : 2^k*3^(oddCount n k) <= 2^k*2^k :=
    Nat.mul_le_mul_left _ (Nat.le_of_lt hCoeff)
  apply v180_descent_of_source_height_and_coefficient n k
  · omega
  · exact hCoeff

theorem v180_three_power_monotone (a b : Nat)
    (h : a<=b) : 3^a <= 3^b := by
  induction b with
  | zero =>
      have hz : a=0 := by omega
      subst a
      exact Nat.le_refl _
  | succ b ih =>
      by_cases hle : a<=b
      · calc
          3^a <= 3^b := ih hle
          _ <= 3^(b+1) := by
            rw [Nat.pow_succ]
            have hp : 0<3^b := Nat.pow_pos (by decide)
            omega
      · have heq : a=b+1 := by omega
        rw [heq]

theorem v180_twelve_clock_low_odd_descends (n : Nat)
    (hn : 8192<=n) (hodd : oddCount n 12<=7) :
    iter shortcut 12 n < n := by
  let A := 3^(oddCount n 12)
  have hA : A<=2187 := by
    have h := v180_three_power_monotone
      (oddCount n 12) 7 hodd
    simpa [A] using h
  have hBias : bias n 12 < 4096*A := by
    simpa [A] using v180_bias_strict n 12
  have hAlo : A+1909 <=4096 := by omega
  have hscaled : (A+1909)*n <=4096*n :=
    Nat.mul_le_mul_right n hAlo
  have hAupper : 4096*A <=4096*2187 :=
    Nat.mul_le_mul_left _ hA
  have hNlower : 1909*8192 <=1909*n :=
    Nat.mul_le_mul_left 1909 hn
  have hBiasSmall : bias n 12 <1909*n := by omega
  have hStrict : A*n + bias n 12 <4096*n := by
    calc
      A*n + bias n 12 < A*n + 1909*n :=
        Nat.add_lt_add_left hBiasSmall _
      _ = (A+1909)*n := by simp [Nat.add_mul]
      _ <=4096*n := hscaled
  have hEq : 4096*iter shortcut 12 n =
      A*n + bias n 12 := by
    simpa [A] using exact_affine n 12
  by_contra hnot
  have hnond : n<=iter shortcut 12 n :=
    Nat.le_of_not_lt hnot
  have hScale : 4096*n <=4096*iter shortcut 12 n :=
    Nat.mul_le_mul_left 4096 hnond
  rw [hEq] at hScale
  omega

theorem v180_positive_shortcut (n : Nat) (hn : 0<n) :
    0<shortcut n := by
  unfold shortcut
  by_cases he : n%2=0
  · simp only [he,ite_true]
    omega
  · simp only [he,ite_false]
    omega

theorem v180_positive_iter (n k : Nat) (hn : 0<n) :
    0<iter shortcut k n := by
  induction k with
  | zero => simpa [iter] using hn
  | succ k ih =>
      rw [iter_succ_last]
      exact v180_positive_shortcut _ ih

theorem v180_least_bad_high_odd_twelve
    (n : Nat) (hn : 8192<=n)
    (hbad : MinimalBad PositiveBad n) :
    8<=oddCount n 12 := by
  by_contra hnot
  have hlow : oddCount n 12<=7 := by omega
  have hd := v180_twelve_clock_low_odd_descends n hn hlow
  have hp : 0<iter shortcut 12 n :=
    v180_positive_iter n 12 (by omega)
  have hmeet :
      iter shortcut 12 n = iter shortcut 0 (iter shortcut 12 n) :=
    by simp [iter]
  exact (minimal_positive_bad_no_earlier_source_meeting
    hbad (iter shortcut 12 n) 12 0 hp hd) hmeet

#print axioms v180_bias_plus_power_le
#print axioms v180_bias_strict
#print axioms v180_descent_of_source_height_and_coefficient
#print axioms v180_large_source_crossing_descends
#print axioms v180_three_power_monotone
#print axioms v180_twelve_clock_low_odd_descends
#print axioms v180_least_bad_high_odd_twelve

end SourceProduct
end CollatzFinal
