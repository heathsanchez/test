import Collatz.FirstCrossingGap

namespace CollatzFinal
namespace SourceProduct

/-- In the large-source regime, the first-crossing endpoint lies strictly
below four thirds of the original source. -/
theorem first_crossing_three_y_lt_four_n
    {n d : Nat} (hn : 0 < n)
    (hfirst : FirstCoefficientCrossingAt n d)
    (hq : oddCount n d < n) :
    3 * iter shortcut d n < 4 * n := by
  have h := first_crossing_endpoint_additive_bound hn hfirst
  omega

/-- The target is below the original source, not merely below the endpoint.
A positive exact predecessor at most three quarters of y suffices here. -/
theorem ordinary_exit_of_three_quarter_predecessor
    {n y p b : Nat}
    (hwindow : 3 * y < 4 * n)
    (hp : 0 < p)
    (hreach : iter shortcut b p = y)
    (htarget : 4 * p ≤ 3 * y) :
    OrdinaryExit n y := by
  have hlt : p < n := by omega
  exact Or.inr (Or.inr ⟨p, b, hp, hlt, hreach⟩)

/-- This supplies the actual first-crossing exit consumed by the final
ordinary-exit theorem. The existence of the predecessor is explicit. -/
theorem first_crossing_exit_of_three_quarter_predecessor
    {n d p b : Nat} (hn : 0 < n)
    (hfirst : FirstCoefficientCrossingAt n d)
    (hq : oddCount n d < n)
    (hp : 0 < p)
    (hreach : iter shortcut b p = iter shortcut d n)
    (htarget : 4 * p ≤ 3 * iter shortcut d n) :
    OrdinaryExit n (iter shortcut d n) := by
  exact ordinary_exit_of_three_quarter_predecessor
    (first_crossing_three_y_lt_four_n hn hfirst hq) hp hreach htarget

/-- An unconditional sound periodic lower-predecessor sieve cannot mark the
residue class of 1. This is a limit on this sieve interface, not on schemes
with magnitude guards, finite exceptions, or additional source/forward state. -/
theorem periodic_lower_sieve_excludes_one_class
    (modulus : Nat) (covered : Nat → Prop)
    (hperiodic : ∀ a b, a % modulus = b % modulus →
      (covered a ↔ covered b))
    (hsound : ∀ y, 0 < y → covered y →
      ∃ p : Nat, 0 < p ∧ p < y)
    {y : Nat} (hy : y % modulus = 1 % modulus) :
    ¬ covered y := by
  intro hc
  have hc1 : covered 1 := (hperiodic y 1 hy).1 hc
  obtain ⟨p, hp, hlt⟩ := hsound 1 (by decide) hc1
  omega

/-- The forced scalar signature determines a class modulo 12, not one class
modulo 24. Both 7 and 19 modulo 24 satisfy it. -/
theorem scalar_large_signature_iff_mod12 (y : Nat) :
    (y % 3 = 1 ∧ y % 2 = 1 ∧ shortcut y % 2 = 1) ↔
    y % 12 = 7 := by
  constructor
  · intro h
    obtain ⟨h3, h2, ht⟩ := h
    have ho : ¬ y % 2 = 0 := by omega
    simp only [shortcut, ho, ite_false] at ht
    omega
  · intro h
    have h3 : y % 3 = 1 := by omega
    have h2 : y % 2 = 1 := by omega
    have ho : ¬ y % 2 = 0 := by omega
    refine ⟨h3, h2, ?_⟩
    simp only [shortcut, ho, ite_false]
    omega

-- Concrete semantic separators, not candidate Collatz counterexamples.
example : iter shortcut 3 11 = 13 ∧ iter shortcut 4 7 = 13 := by decide
example : 19 % 3 = 1 ∧ 19 % 2 = 1 ∧ shortcut 19 % 2 = 1 ∧
    19 % 24 ≠ 7 := by decide

#print axioms first_crossing_three_y_lt_four_n
#print axioms ordinary_exit_of_three_quarter_predecessor
#print axioms first_crossing_exit_of_three_quarter_predecessor
#print axioms periodic_lower_sieve_excludes_one_class
#print axioms scalar_large_signature_iff_mod12

end SourceProduct
end CollatzFinal
