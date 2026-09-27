import Collatz.FirstCrossingBias
import Collatz.ThreeAdicReverseBarrier

namespace CollatzFinal
namespace SourceProduct

/-- Before a first coefficient crossing, every earlier depth still survives. -/
theorem first_crossing_previous_survival_bound
    {n d : Nat}
    (hfirst : FirstCoefficientCrossingAt n d) :
    ∀ i, i < d → 2 ^ i ≤ 3 ^ oddCount n i := by
  intro i hi
  have hnot := hfirst.2 i hi
  unfold CoefficientCrossingAt at hnot
  omega

/-- Universal additive endpoint bound at first coefficient crossing:
3*T^d(n) < 3*n + q_d. -/
theorem first_crossing_endpoint_additive_bound
    {n d : Nat}
    (hn : 0 < n)
    (hfirst : FirstCoefficientCrossingAt n d) :
    3 * iter shortcut d n < 3 * n + oddCount n d := by
  have hpre := first_crossing_previous_survival_bound hfirst
  have hb := elementary_bias_bound_of_no_earlier_crossing n d hpre
  have ha := exact_affine n d
  have hscaled_eq :
      2 ^ d * (3 * iter shortcut d n) =
        3 ^ oddCount n d * (3 * n) + 3 * bias n d := by
    calc
      2 ^ d * (3 * iter shortcut d n) =
          3 * (2 ^ d * iter shortcut d n) := by
        simp [Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
      _ = 3 * (3 ^ oddCount n d * n + bias n d) := by rw [ha]
      _ = 3 ^ oddCount n d * (3 * n) + 3 * bias n d := by
        simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hb' :
      3 * bias n d ≤ 3 ^ oddCount n d * oddCount n d := by
    simpa [Nat.mul_comm] using hb
  have hle :
      2 ^ d * (3 * iter shortcut d n) ≤
        3 ^ oddCount n d * (3 * n + oddCount n d) := by
    rw [hscaled_eq]
    calc
      3 ^ oddCount n d * (3 * n) + 3 * bias n d ≤
          3 ^ oddCount n d * (3 * n) +
            3 ^ oddCount n d * oddCount n d :=
        Nat.add_le_add_left hb' _
      _ = 3 ^ oddCount n d * (3 * n + oddCount n d) := by
        simp [Nat.mul_add]
  have hfactor : 0 < 3 * n + oddCount n d := by omega
  have hstrict :
      3 ^ oddCount n d * (3 * n + oddCount n d) <
        2 ^ d * (3 * n + oddCount n d) := by
    rw [Nat.mul_lt_mul_right hfactor]
    exact hfirst.1
  have hscaled :
      2 ^ d * (3 * iter shortcut d n) <
        2 ^ d * (3 * n + oddCount n d) :=
    Nat.lt_of_le_of_lt hle hstrict
  exact Nat.lt_of_mul_lt_mul_left hscaled

/-- Therefore a hard first-crossing endpoint is only additively above its
source: three times the overshoot is strictly below the critical odd count. -/
theorem hard_first_crossing_additive_gap
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k) :
    3 * (iter shortcut (k + 1) n - n) <
      oddCount n (k + 1) := by
  have hu := first_crossing_endpoint_additive_bound hn hhard.1
  have hge := hard_first_crossing_endpoint_ge_source hn hhard
  omega

/-- Joining additive closeness with the depth-one inverse-odd barrier:
if the critical odd count is no larger than the source, a hard endpoint
cannot be 2 mod 3. -/
theorem hard_first_crossing_not_mod3_two_of_q_le_source
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hq : oddCount n (k + 1) ≤ n) :
    iter shortcut (k + 1) n % 3 ≠ 2 := by
  intro hy
  have hgrowth := hard_first_crossing_mod3_two_growth hhard hy
  have hu := first_crossing_endpoint_additive_bound hn hhard.1
  omega

/-- More generally, any exact 3-adic all-odd reverse depth m must fit inside
the same first-crossing additive window while paying the reverse growth cost. -/
theorem hard_first_crossing_additive_threeAdic_squeeze
    {n k a m : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hy : iter shortcut (k + 1) n + 1 = 3 ^ m * a)
    (ha : 0 < a)
    (hp : 0 < 2 ^ m * a - 1) :
    (n + 1) * 3 ^ m ≤
      2 ^ m * (iter shortcut (k + 1) n + 1) ∧
    3 * (iter shortcut (k + 1) n - n) <
      oddCount n (k + 1) := by
  exact ⟨hard_first_crossing_threeAdic_growth hhard hy ha hp,
    hard_first_crossing_additive_gap hn hhard⟩

#print axioms first_crossing_previous_survival_bound
#print axioms first_crossing_endpoint_additive_bound
#print axioms hard_first_crossing_additive_gap
#print axioms hard_first_crossing_not_mod3_two_of_q_le_source
#print axioms hard_first_crossing_additive_threeAdic_squeeze

end SourceProduct
end CollatzFinal
