import Collatz.FirstCrossingGap

namespace CollatzFinal
namespace SourceProduct

/-- Moving one odd step one place earlier strictly decreases the two-step
affine bias, before any common suffix is applied. This is the local exchange
underlying the mechanical-boundary bias majorization. -/
theorem bias_adjacent_odd_earlier_lt (B t : Nat) :
    3 * B + 2 ^ t < 3 * B + 2 ^ (t + 1) := by
  have hp : 0 < 2 ^ t := Nat.pow_pos (by decide)
  rw [Nat.pow_succ]
  omega

/-- The same strict bias advantage survives an arbitrary common suffix with
r later odd steps and any common additive suffix term C. -/
theorem bias_adjacent_odd_earlier_suffix_lt
    (B t r C : Nat) :
    3 ^ r * (3 * B + 2 ^ t) + C <
      3 ^ r * (3 * B + 2 ^ (t + 1)) + C := by
  have h := bias_adjacent_odd_earlier_lt B t
  have hp : 0 < 3 ^ r := Nat.pow_pos (by decide)
  have hm := Nat.mul_lt_mul_of_pos_left h hp
  exact Nat.add_lt_add_right hm C

/-- Every proper prefix of an actual first-crossing word has at least the
deterministic qmin odd count. This is the orbit half of the majorization
argument; the endpoint equality is supplied by first-crossing rigidity. -/
theorem first_crossing_prefix_qmin_dominance
    {n d : Nat}
    (hfirst : FirstCoefficientCrossingAt n d) :
    ∀ i, i < d → qmin i ≤ oddCount n i := by
  intro i hi
  have hs : CoefficientSurvives n i := by
    unfold CoefficientSurvives coefficientDenominator coefficientNumerator
    exact first_crossing_previous_survival_bound hfirst i hi
  exact (coefficientSurvives_iff_qmin_le n i).1 hs

#print axioms bias_adjacent_odd_earlier_lt
#print axioms bias_adjacent_odd_earlier_suffix_lt
#print axioms first_crossing_prefix_qmin_dominance

end SourceProduct
end CollatzFinal
