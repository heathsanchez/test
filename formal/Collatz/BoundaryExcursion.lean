import Collatz.FirstCrossingRigidity

namespace CollatzFinal
namespace SourceProduct

/-- If the deterministic coefficient boundary does not rise at depth k,
then the current coefficient reserve is at least a factor two above the
dyadic denominator. -/
theorem boundaryBit_zero_gives_double_cover
    {k : Nat} (hzero : boundaryBit k = 0) :
    2 ^ (k + 1) ≤ 3 ^ qmin k := by
  have hs := qmin_succ_eq k
  rw [hzero, Nat.add_zero] at hs
  by_cases h : 2 ^ (k + 1) ≤ 3 ^ qmin k
  · exact h
  · have hq : qmin (k + 1) = qmin k + 1 := by
      simp [qmin, h]
    rw [hs] at hq
    omega

/-- If the deterministic coefficient boundary rises at depth k,
the current coefficient reserve is strictly below a factor two. -/
theorem boundaryBit_one_gives_below_double
    {k : Nat} (hone : boundaryBit k = 1) :
    3 ^ qmin k < 2 ^ (k + 1) := by
  have hs := qmin_succ_eq k
  rw [hone] at hs
  by_cases h : 2 ^ (k + 1) ≤ 3 ^ qmin k
  · have hq : qmin (k + 1) = qmin k := by
      simp [qmin, h]
    rw [hs] at hq
    omega
  · omega

/-- Deterministic phase contraction.

A zero-boundary phase has normalized coefficient ratio at least 2; a
one-boundary phase has normalized coefficient ratio strictly below 2.
Therefore moving from the former phase to the latter strictly contracts the
cross-multiplied coefficient ratio. No orbit or stopping-time hypothesis is
used. -/
theorem threshold_ratio_contracts_zero_to_one
    {i j : Nat}
    (hi : boundaryBit i = 0)
    (hj : boundaryBit j = 1) :
    3 ^ qmin j * 2 ^ i < 3 ^ qmin i * 2 ^ j := by
  have hlo := boundaryBit_zero_gives_double_cover hi
  have hhi := boundaryBit_one_gives_below_double hj
  have hpowi : 0 < 2 ^ i := Nat.pow_pos (by decide)
  have h1 :
      3 ^ qmin j * 2 ^ i < 2 ^ (j + 1) * 2 ^ i :=
    Nat.mul_lt_mul_of_pos_right hhi hpowi
  have h2 :
      2 ^ (j + 1) * 2 ^ i ≤ 3 ^ qmin i * 2 ^ j := by
    have hm := Nat.mul_le_mul_right (2 ^ j) hlo
    simpa [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm] using hm
  exact Nat.lt_of_lt_of_le h1 h2

/-- Zero signed surplus identifies the actual orbit odd count with qmin. -/
theorem oddCount_eq_qmin_of_zero_surplus
    {n k : Nat}
    (hz : signedSurplus n k = 0) :
    oddCount n k = qmin k := by
  unfold signedSurplus at hz
  omega

/-- Orbit-facing form of the phase contraction.  Between two zero-surplus
boundary states, if the start is a no-carry threshold phase and the end is a
carry threshold phase, the multiplicative coefficient part strictly
contracts.  This is exactly the structural law observed on the protected
record-setter residuals; it is now universal. -/
theorem zero_surplus_excursion_coefficient_contracts
    {n i j : Nat}
    (hzi : signedSurplus n i = 0)
    (hzj : signedSurplus n j = 0)
    (hi : boundaryBit i = 0)
    (hj : boundaryBit j = 1) :
    3 ^ oddCount n j * 2 ^ i <
      3 ^ oddCount n i * 2 ^ j := by
  have hqi := oddCount_eq_qmin_of_zero_surplus hzi
  have hqj := oddCount_eq_qmin_of_zero_surplus hzj
  simpa [hqi, hqj] using threshold_ratio_contracts_zero_to_one hi hj

/-- At a first coefficient crossing, the final parent is a zero-surplus carry
phase. Thus any earlier zero-surplus no-carry phase has strictly larger
normalized multiplicative coefficient. -/
theorem earlier_zero_nocarry_to_first_crossing_parent_contracts
    {n i k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hzi : signedSurplus n i = 0)
    (hi : boundaryBit i = 0) :
    3 ^ oddCount n k * 2 ^ i <
      3 ^ oddCount n i * 2 ^ k := by
  have hzj := (first_crossing_rigidity hfirst).1
  have hj := (first_crossing_rigidity hfirst).2.1
  exact zero_surplus_excursion_coefficient_contracts hzi hzj hi hj

#print axioms boundaryBit_zero_gives_double_cover
#print axioms boundaryBit_one_gives_below_double
#print axioms threshold_ratio_contracts_zero_to_one
#print axioms oddCount_eq_qmin_of_zero_surplus
#print axioms zero_surplus_excursion_coefficient_contracts
#print axioms earlier_zero_nocarry_to_first_crossing_parent_contracts

end SourceProduct
end CollatzFinal
