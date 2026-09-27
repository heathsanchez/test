import Collatz.CoalescenceDescent
import Collatz.FirstCrossingRigidity

namespace CollatzFinal
namespace SourceProduct

/-- A zero threshold bit means the existing qmin exponent already covers the
next dyadic scale. -/
theorem boundaryBit_zero_next_covered
    {k : Nat} (hzero : boundaryBit k = 0) :
    2 ^ (k + 1) ≤ 3 ^ qmin k := by
  by_cases hcover : 2 ^ (k + 1) ≤ 3 ^ qmin k
  · exact hcover
  · have hsucc : qmin (k + 1) = qmin k + 1 := by
      simp [qmin, hcover]
    unfold boundaryBit at hzero
    rw [hsucc] at hzero
    omega

/-- A unit threshold bit means the existing qmin exponent fails at the next
dyadic scale. -/
theorem boundaryBit_one_next_fails
    {k : Nat} (hone : boundaryBit k = 1) :
    3 ^ qmin k < 2 ^ (k + 1) := by
  have hfail : ¬ 2 ^ (k + 1) ≤ 3 ^ qmin k := by
    intro hcover
    have hsucc : qmin (k + 1) = qmin k := by
      simp [qmin, hcover]
    unfold boundaryBit at hone
    rw [hsucc] at hone
    omega
  omega

/-- Pure threshold-phase contraction.

If the boundary immediately after i is flat (bit 0) while the boundary
immediately after j rises (bit 1), then the qmin coefficient ratio at j is
strictly smaller than at i.  This is the integer, logarithm-free form of the
contractive final excursion observed by Crystal. -/
theorem boundary_phase_strictly_contracts
    {i j : Nat}
    (hi : boundaryBit i = 0)
    (hj : boundaryBit j = 1) :
    3 ^ qmin j * 2 ^ i < 3 ^ qmin i * 2 ^ j := by
  have hstart := boundaryBit_zero_next_covered hi
  have hend := boundaryBit_one_next_fails hj
  have hpowi : 0 < 2 ^ i := Nat.pow_pos (by decide)
  have hleft :
      3 ^ qmin j * 2 ^ i < 2 ^ (j + 1) * 2 ^ i := by
    rw [Nat.mul_lt_mul_right hpowi]
    exact hend
  have hmiddle :
      2 ^ (j + 1) * 2 ^ i = 2 ^ j * 2 ^ (i + 1) := by
    simp [Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
  have hright :
      2 ^ j * 2 ^ (i + 1) ≤ 2 ^ j * 3 ^ qmin i :=
    Nat.mul_le_mul_left (2 ^ j) hstart
  calc
    3 ^ qmin j * 2 ^ i
        < 2 ^ (j + 1) * 2 ^ i := hleft
    _ = 2 ^ j * 2 ^ (i + 1) := hmiddle
    _ ≤ 2 ^ j * 3 ^ qmin i := hright
    _ = 3 ^ qmin i * 2 ^ j := by
      simp [Nat.mul_comm]

/-- On actual orbit boundary states, the same phase law says that the
multiplicative coefficient of the whole intervening orbit word is strictly
contractive.  No finite-source or bounded-depth assumption is used. -/
theorem zero_surplus_excursion_strictly_contracts
    {n i j : Nat}
    (hsi : signedSurplus n i = 0)
    (hi : boundaryBit i = 0)
    (hsj : signedSurplus n j = 0)
    (hj : boundaryBit j = 1) :
    3 ^ oddCount n j * 2 ^ i <
      3 ^ oddCount n i * 2 ^ j := by
  have hqi : oddCount n i = qmin i := by
    unfold signedSurplus at hsi
    omega
  have hqj : oddCount n j = qmin j := by
    unfold signedSurplus at hsj
    omega
  simpa [hqi, hqj] using
    (boundary_phase_strictly_contracts (i := i) (j := j) hi hj)

/-- Every first coefficient crossing ends at exactly the contracting phase
boundary needed above: immediately before the forced even crossing step the
surplus is zero and the deterministic boundary bit is one. -/
theorem first_crossing_previous_is_contracting_boundary
    {n k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1)) :
    signedSurplus n k = 0 ∧ boundaryBit k = 1 := by
  exact ⟨(first_crossing_rigidity hfirst).1,
    (first_crossing_rigidity hfirst).2.1⟩

/-- Consequently, any earlier zero-surplus state that genuinely leaves through
a flat boundary lies above a strictly contractive coefficient block ending
immediately before the first crossing. -/
theorem first_crossing_final_zero_excursion_contracts
    {n i k : Nat}
    (hfirst : FirstCoefficientCrossingAt n (k + 1))
    (hsi : signedSurplus n i = 0)
    (hi : boundaryBit i = 0) :
    3 ^ oddCount n k * 2 ^ i <
      3 ^ oddCount n i * 2 ^ k := by
  have hk := first_crossing_previous_is_contracting_boundary hfirst
  exact zero_surplus_excursion_strictly_contracts
    hsi hi hk.1 hk.2

#print axioms boundaryBit_zero_next_covered
#print axioms boundaryBit_one_next_fails
#print axioms boundary_phase_strictly_contracts
#print axioms zero_surplus_excursion_strictly_contracts
#print axioms first_crossing_previous_is_contracting_boundary
#print axioms first_crossing_final_zero_excursion_contracts

end SourceProduct
end CollatzFinal
