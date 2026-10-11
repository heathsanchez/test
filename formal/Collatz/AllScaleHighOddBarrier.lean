import Collatz.UniversalAffineBiasOddBarrier

namespace CollatzFinal
namespace SourceProduct

/-!
V181 — ALL-SCALE HIGH-ODD PREFIX NECESSITY FOR A LEAST BAD SOURCE.

The exact V180 bias theorem forces true descent when the all-source
affine 3^odd coefficient is smaller than the 2^k clock denominator,
and the original source is large enough.

At k=5*m and oddCount<=3*m, 3^(3*m)=27^m <32^m=2^(5*m)
for every positive m.

Therefore any hypothetical least bad natural source n >=2^(10*m)
would have MORE than 3*m odd shortcut steps in the first 5*m
true clocks. The permitted parity-word fraction decays
exponentially as m grows, but a fixed n only meets the height
premise for FINITELY MANY m: no global Collatz proof follows.
-/

theorem v181_twentyseven_pow_le_thirtytwo_pow (m : Nat) :
    27^m <= 32^m := by
  induction m with
  | zero => decide
  | succ m ih =>
      have hMul : 27^m*27 <= 32^m*27 :=
        Nat.mul_le_mul_right 27 ih
      have hLarger : 32^m*27 <= 32^m*32 :=
        Nat.mul_le_mul_left _ (by decide)
      calc
        27^(m+1) = 27^m*27 := by simp [Nat.pow_succ]
        _ <= 32^m*27 := hMul
        _ <= 32^m*32 := hLarger
        _ = 32^(m+1) := by simp [Nat.pow_succ]

theorem v181_twentyseven_pow_lt_thirtytwo_pow
    (m : Nat) (hm : 0<m) :
    27^m < 32^m := by
  cases m with
  | zero => omega
  | succ m =>
      have hLe := v181_twentyseven_pow_le_thirtytwo_pow m
      have hp : 0<32^m := Nat.pow_pos (by decide)
      have hLeft : 27^m*27 <= 32^m*27 :=
        Nat.mul_le_mul_right 27 hLe
      have hBound : 32^m*27 < 32^m*32 := by
        have hLT : 27+1 <= 32 := by decide
        have hmule := Nat.mul_le_mul_left (32^m) hLT
        simp only [Nat.mul_add, mul_one] at hmule
        omega
      calc
        27^(m+1) = 27^m*27 := by simp [Nat.pow_succ]
        _ <= 32^m*27 := hLeft
        _ < 32^m*32 := hBound
        _ = 32^(m+1) := by simp [Nat.pow_succ]

theorem v181_three_fifths_power_crossing
    (m : Nat) (hm : 0<m) :
    3^(3*m) < 2^(5*m) := by
  have h27 := v181_twentyseven_pow_lt_thirtytwo_pow m hm
  have h3 : 3^(3*m)=27^m := by
    simp [Nat.pow_mul]
  have h2 : 2^(5*m)=32^m := by
    simp [Nat.pow_mul]
  rw [h3,h2]
  exact h27

/-- Unbounded source/clock family, independent of parity statistics.
The threshold in ORIGINAL source height is explicitly 2^(10*m). -/
theorem v181_three_fifths_odd_prefix_forces_descent
    (n m : Nat) (hm : 0<m)
    (hHeight : 2^(10*m) <= n)
    (hOdd : oddCount n (5*m) <= 3*m) :
    iter shortcut (5*m) n < n := by
  have hPower : 3^(oddCount n (5*m)) <= 3^(3*m) :=
    v180_three_power_monotone _ _ hOdd
  have hCross : 3^(oddCount n (5*m)) < 2^(5*m) :=
    Nat.lt_of_le_of_lt hPower
      (v181_three_fifths_power_crossing m hm)
  have hHeight' : 2^(2*(5*m)) <= n := by
    have hEq : 2*(5*m)=10*m := by omega
    rw [hEq]
    exact hHeight
  exact v180_large_source_crossing_descends
    n (5*m) hHeight' hCross

/-- For every positive clock-scale m separately, the hypothetical
LEAST bad source has a strictly high-odd original-source prefix,
provided the source meets this scale's height threshold. -/
theorem v181_least_bad_high_odd_all_scales
    (n m : Nat) (hm : 0<m)
    (hHeight : 2^(10*m) <= n)
    (hBad : MinimalBad PositiveBad n) :
    3*m+1 <= oddCount n (5*m) := by
  apply Classical.byContradiction
  intro hNot
  have hLow : oddCount n (5*m) <=3*m := by omega
  have hDesc :=
    v181_three_fifths_odd_prefix_forces_descent
      n m hm hHeight hLow
  have hPos : 0<n := by
    have hpow : 0<2^(10*m) := Nat.pow_pos (by decide)
    omega
  have hOutPos : 0<iter shortcut (5*m) n :=
    v180_positive_iter n (5*m) hPos
  have hMeet :
      iter shortcut (5*m) n =
        iter shortcut 0 (iter shortcut (5*m) n) := by
    simp [iter]
  exact (minimal_positive_bad_no_earlier_source_meeting
    hBad (iter shortcut (5*m) n) (5*m) 0 hOutPos hDesc) hMeet

#print axioms v181_twentyseven_pow_le_thirtytwo_pow
#print axioms v181_twentyseven_pow_lt_thirtytwo_pow
#print axioms v181_three_fifths_power_crossing
#print axioms v181_three_fifths_odd_prefix_forces_descent
#print axioms v181_least_bad_high_odd_all_scales

end SourceProduct
end CollatzFinal
