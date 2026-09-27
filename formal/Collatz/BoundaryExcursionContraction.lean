import Collatz.SurvivalDeficit

namespace CollatzFinal
namespace SourceProduct

/-- If the deterministic coefficient threshold does not rise at depth i,
then the next dyadic scale is already covered by the current threshold power. -/
theorem boundaryBit_zero_pow_le
    {i : Nat} (h0 : boundaryBit i = 0) :
    2 ^ (i + 1) ≤ 3 ^ qmin i := by
  have hs := qmin_spec (i + 1)
  have hq := qmin_succ_eq i
  rw [h0, Nat.add_zero] at hq
  rw [hq] at hs
  exact hs

/-- If the deterministic coefficient threshold rises at depth j,
then the old threshold power is strictly below the next dyadic scale. -/
theorem boundaryBit_one_pow_lt
    {j : Nat} (h1 : boundaryBit j = 1) :
    3 ^ qmin j < 2 ^ (j + 1) := by
  by_cases h : 2 ^ (j + 1) ≤ 3 ^ qmin j
  · have hb : boundaryBit j = 0 := by
      simp [boundaryBit, qmin, h]
    omega
  · omega

/-- Universal coefficient contraction across a zero-boundary excursion.

A safe departure from a zero-surplus boundary uses a threshold bit 0.
A fatal return boundary uses threshold bit 1.  Those two deterministic
threshold facts alone force the intervening 3/2 coefficient ratio to be
strictly contractive.  No logarithm estimate or finite source bound is used.

The cross-multiplied form avoids division:
  3^qmin(j) / 2^(j+1) < 3^qmin(i) / 2^(i+1).
-/
theorem boundary_excursion_coefficient_contracts
    {i j : Nat}
    (hstart : boundaryBit i = 0)
    (hend : boundaryBit j = 1) :
    3 ^ qmin j * 2 ^ (i + 1) <
      3 ^ qmin i * 2 ^ (j + 1) := by
  have hi := boundaryBit_zero_pow_le hstart
  have hj := boundaryBit_one_pow_lt hend
  have hpow : 0 < 2 ^ (i + 1) := Nat.pow_pos (by decide)
  have hleft :
      3 ^ qmin j * 2 ^ (i + 1) <
        2 ^ (j + 1) * 2 ^ (i + 1) := by
    rw [Nat.mul_lt_mul_right hpow]
    exact hj
  have hright :
      2 ^ (j + 1) * 2 ^ (i + 1) ≤
        2 ^ (j + 1) * 3 ^ qmin i :=
    Nat.mul_le_mul_left (2 ^ (j + 1)) hi
  have h := Nat.lt_of_lt_of_le hleft hright
  simpa [Nat.mul_comm] using h

#print axioms boundaryBit_zero_pow_le
#print axioms boundaryBit_one_pow_lt
#print axioms boundary_excursion_coefficient_contracts

end SourceProduct
end CollatzFinal
