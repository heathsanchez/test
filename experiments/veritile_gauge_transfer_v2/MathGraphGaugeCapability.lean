import Mathlib

namespace MathGraphGaugeCapability

/--
A consequence-sized capability compiled from the successful V1 normalized
exponential quotient transfer.

If the same nonzero factor relates a scaled numerator/denominator pair to an
unscaled pair, normalization erases that factor. The theorem is agnostic to
where the factor came from: natural exponential, base-2 exponential, a unit
conversion, or another lawful representation change.
-/
theorem common_factor_ratio
    (c scaledNum scaledDen num den : ℝ)
    (hc : c ≠ 0)
    (hnum : c * scaledNum = num)
    (hden : c * scaledDen = den) :
    scaledNum / scaledDen = num / den := by
  calc
    scaledNum / scaledDen = (c * scaledNum) / (c * scaledDen) := by
      symm
      exact mul_div_mul_left scaledNum scaledDen hc
    _ = num / den := by rw [hnum, hden]

end MathGraphGaugeCapability
