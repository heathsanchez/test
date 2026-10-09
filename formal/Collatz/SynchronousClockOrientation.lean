import Collatz.ChartMultiplierCompleteness

namespace CollatzFinal
namespace SourceProduct

/-!
V139 source-attached odd-step count obeys the actual shortcut
cocycle law. It is NOT a formal "independent random parity" assumption.
-/

theorem oddCount_add (n a b : Nat) :
    oddCount n (a + b) =
      oddCount n a + oddCount (iter shortcut a n) b := by
  induction b with
  | zero =>
      simp [oddCount]
  | succ b ih =>
      have hsum : a + (b+1) = (a+b)+1 := by omega
      rw [hsum]
      simp only [oddCount]
      rw [ih, iter_add]
      by_cases he : iter shortcut b (iter shortcut a n) % 2 = 0
      · simp [he]
      · simp [he, Nat.add_assoc]

#print axioms oddCount_add

end SourceProduct

/-!
V139 — SYNCHRONOUS FUTURE CLOCK EXTENSIONS CANNOT REPAIR
A FAILED FIXED-CLOCK CHART ORIENTATION.

Two actual base source trajectories meet at clocks (i,j).
If both are extended by the SAME future clock t, the shared suffix
adds the same number gamma of odd steps to both, and the same
number t of total shortcut steps to both.

Therefore the weighted V137 admissibility comparison
  2^j * 3^alpha <= 2^i * 3^beta
is EXACTLY equivalent to the comparison after (i+t,j+t).
There is NO new affine-multiplier admission information to be
gained by this kind of synchronous waiting.

For source5 versus earlier3, the ACTUAL clock pair (3,8)
is a permanently invalid oriented uniform affine chart, for ANY
common future suffix and ANY positive integer multipliers.
Yet another true pair (1,2) is admitted, so this is a grammar
clock-relative separator, NEVER a Collatz counterexample.

The complete live residual is asymmetric phase changes / different
meeting endpoints / different earlier-source representatives.
GLOBAL COLLATZ UNKNOWN.
-/

private theorem pow_two_positive (k : Nat) : 0 < (2 : Nat) ^ k := by
  induction k with
  | zero => decide
  | succ k ih =>
      rw [Nat.pow_succ]
      exact Nat.mul_pos ih (by decide)

private theorem pow_three_positive (k : Nat) : 0 < (3 : Nat) ^ k := by
  induction k with
  | zero => decide
  | succ k ih =>
      rw [Nat.pow_succ]
      exact Nat.mul_pos ih (by decide)

/-- Source-indexed exact clock-gauge invariance of the coefficient
admissibility inequality, conditional on a TRUE actual base collision.
The multiplier semantics remains precisely V137; no new orbit claim. -/
theorem weighted_chart_guard_synchronous_suffix_iff
    (a p i j t : Nat)
    (hmeet : iter shortcut i a = iter shortcut j p) :
    (2 ^ (j+t) * 3 ^ SourceProduct.oddCount a (i+t) <=
       2 ^ (i+t) * 3 ^ SourceProduct.oddCount p (j+t)) ↔
    (2 ^ j * 3 ^ SourceProduct.oddCount a i <=
       2 ^ i * 3 ^ SourceProduct.oddCount p j) := by
  have ha := SourceProduct.oddCount_add a i t
  have hb := SourceProduct.oddCount_add p j t
  rw [ha,hb]
  have hs :
      SourceProduct.oddCount (iter shortcut i a) t =
      SourceProduct.oddCount (iter shortcut j p) t := by
    rw [hmeet]
  rw [hs]
  let gamma := SourceProduct.oddCount (iter shortcut j p) t
  have hpos :
      0 < ((2 : Nat) ^ t) * ((3 : Nat) ^ gamma) :=
    Nat.mul_pos (pow_two_positive t) (pow_three_positive gamma)
  constructor
  · intro h
    have hscaled :
      (2 ^ j * 3 ^ SourceProduct.oddCount a i) *
          (2 ^ t * 3 ^ gamma) <=
      (2 ^ i * 3 ^ SourceProduct.oddCount p j) *
          (2 ^ t * 3 ^ gamma) := by
      simpa [Nat.pow_add,Nat.mul_assoc,Nat.mul_comm,
             Nat.mul_left_comm] using h
    exact Nat.le_of_mul_le_mul_right hscaled hpos
  · intro h
    have hscaled :=
      Nat.mul_le_mul_right (2 ^ t * 3 ^ gamma) h
    simpa [Nat.pow_add,Nat.mul_assoc,Nat.mul_comm,
           Nat.mul_left_comm] using hscaled

/-- A permanent, mathematically exhaustive negative chart-grammar
certificate: common future waiting will NEVER make clocks (3,8)
admissible for source5/earlier3. -/
theorem source5_bad_clocks_stay_bad_after_any_common_suffix
    (t : Nat) :
    ¬ (2 ^ (8+t) * 3 ^ SourceProduct.oddCount 5 (3+t) <=
       2 ^ (3+t) * 3 ^ SourceProduct.oddCount 3 (8+t)) := by
  intro hfuture
  have hmeeting : iter shortcut 3 5 = iter shortcut 8 3 := by decide
  have hcurrent :=
    (weighted_chart_guard_synchronous_suffix_iff
      5 3 3 8 t hmeeting).mp hfuture
  have hbad :
      ¬ (2 ^ 8 * 3 ^ SourceProduct.oddCount 5 3 <=
         2 ^ 3 * 3 ^ SourceProduct.oddCount 3 8) := by decide
  exact hbad hcurrent

/-- Combine V137's integer coefficient COMPLETENESS with the
synchronous clock law. Neither larger coefficients nor common
future waiting can rescue this fixed grammar branch. -/
theorem source5_no_synchronous_repair_by_any_multiplier
    (t : Nat) :
    ¬ ∃ u v : Nat,
       0 < u ∧ 0 < v ∧
       3 ^ SourceProduct.oddCount 5 (3+t) * u =
         3 ^ SourceProduct.oddCount 3 (8+t) * v ∧
       2 ^ (8+t) * v <= 2 ^ (3+t) * u := by
  intro hmatched
  have hguard :=
    (actual_chart_coefficients_iff_weighted_clock
       5 3 (3+t) (8+t)).mp hmatched
  exact source5_bad_clocks_stay_bad_after_any_common_suffix t hguard

#print axioms weighted_chart_guard_synchronous_suffix_iff
#print axioms source5_bad_clocks_stay_bad_after_any_common_suffix
#print axioms source5_no_synchronous_repair_by_any_multiplier

end CollatzFinal
