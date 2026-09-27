import Collatz.OrdinaryExitReduction

namespace CollatzFinal
namespace SourceProduct

/-- Every value y ≡ 2 (mod 3) has the exact odd shortcut predecessor
    p = (2*y - 1)/3. -/
theorem inverse_odd_predecessor_of_mod3_two
    {y : Nat}
    (hy : y % 3 = 2) :
    let p := (2 * y - 1) / 3
    0 < p ∧ p % 2 = 1 ∧ shortcut p = y := by
  let a := y / 3
  have hy' : y = 3 * a + 2 := by
    dsimp [a]
    omega
  have hp : (2 * y - 1) / 3 = 2 * a + 1 := by
    rw [hy']
    omega
  refine ⟨?_, ?_, ?_⟩
  · rw [hp]
    omega
  · rw [hp]
    omega
  · rw [hp, hy']
    unfold shortcut
    have hpar : (2 * a + 1) % 2 ≠ 0 := by omega
    simp only [hpar, ite_false]
    omega

/-- A 2 mod 3 orbit value whose inverse odd predecessor lies below the source
    is already an ordinary lower-merge exit. -/
theorem ordinary_exit_of_inverse_odd_predecessor_lt
    {n y : Nat}
    (hy : y % 3 = 2)
    (hlt : (2 * y - 1) / 3 < n) :
    OrdinaryExit n y := by
  have hp := inverse_odd_predecessor_of_mod3_two hy
  let p := (2 * y - 1) / 3
  have hpos : 0 < p := by
    simpa [p] using hp.1
  have hstep : shortcut p = y := by
    simpa [p] using hp.2.2
  exact Or.inr (Or.inr ⟨p, 1, hpos, by simpa [p] using hlt, by
    simp [iter, hstep]⟩)

/-- Therefore a no-ordinary-exit state at residue 2 mod 3 must have its
    inverse odd predecessor at or above the original source. -/
theorem no_ordinary_exit_inverse_odd_predecessor_ge
    {n y : Nat}
    (hno : ¬ OrdinaryExit n y)
    (hy : y % 3 = 2) :
    n ≤ (2 * y - 1) / 3 := by
  apply Nat.le_of_not_gt
  intro hlt
  exact hno (ordinary_exit_of_inverse_odd_predecessor_lt hy hlt)

/-- First forbidden-window law for a minimal/no-exit orbit:
    whenever y ≡ 2 mod 3, no lower merge forces 3*n + 1 ≤ 2*y,
    i.e. y is at least the integer version of 1.5*n. -/
theorem no_ordinary_exit_mod3_two_growth
    {n y : Nat}
    (hno : ¬ OrdinaryExit n y)
    (hy : y % 3 = 2) :
    3 * n + 1 ≤ 2 * y := by
  let a := y / 3
  have hy' : y = 3 * a + 2 := by
    dsimp [a]
    omega
  have hp :
      (2 * y - 1) / 3 = 2 * a + 1 := by
    rw [hy']
    omega
  have hpn := no_ordinary_exit_inverse_odd_predecessor_ge hno hy
  rw [hp] at hpn
  rw [hy']
  omega

/-- Along a hypothetical minimal positive bad orbit the same forbidden window
    holds at every depth. -/
theorem minimal_bad_mod3_two_growth
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hy : iter shortcut k n % 3 = 2) :
    3 * n + 1 ≤ 2 * iter shortcut k n := by
  exact no_ordinary_exit_mod3_two_growth
    (minimal_bad_has_no_ordinary_exit hmin k) hy

#print axioms inverse_odd_predecessor_of_mod3_two
#print axioms ordinary_exit_of_inverse_odd_predecessor_lt
#print axioms no_ordinary_exit_inverse_odd_predecessor_ge
#print axioms no_ordinary_exit_mod3_two_growth
#print axioms minimal_bad_mod3_two_growth

end SourceProduct
end CollatzFinal
