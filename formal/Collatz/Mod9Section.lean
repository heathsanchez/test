import Collatz.BiadicRankedNormalization

namespace CollatzFinal
namespace SourceProduct

/-- The canonical odd predecessor attached to the forced section y ≡ 2 (mod 9).
For y = 9q+2 this is p = 6q+1, and one shortcut step from p lands at y. -/
def mod9TwoPred (y : Nat) : Nat :=
  6 * (y / 9) + 1

theorem mod9_two_decomposition
    {y : Nat} (hy : y % 9 = 2) :
    y = 9 * (y / 9) + 2 := by
  have h := Nat.mod_add_div y 9
  omega

theorem mod9_two_pred_positive (y : Nat) :
    0 < mod9TwoPred y := by
  simp [mod9TwoPred]

theorem mod9_two_pred_shortcut
    {y : Nat} (hy : y % 9 = 2) :
    shortcut (mod9TwoPred y) = y := by
  have hdecomp : y = 9 * (y / 9) + 2 :=
    mod9_two_decomposition hy
  have hodd : (6 * (y / 9) + 1) % 2 ≠ 0 := by
    omega
  have hnum :
      3 * (6 * (y / 9) + 1) + 1 =
        2 * (9 * (y / 9) + 2) := by
    omega
  simp [mod9TwoPred, shortcut, hodd, hnum, hdecomp]

/-- A forced-section hit below the exact 3/2 source threshold has a smaller
positive odd predecessor whose next shortcut value is the hit. -/
theorem mod9_two_pred_lt_source
    {n y : Nat}
    (hy : y % 9 = 2)
    (hheight : 2 * y < 3 * n + 1) :
    mod9TwoPred y < n := by
  have hdecomp : y = 9 * (y / 9) + 2 :=
    mod9_two_decomposition hy
  unfold mod9TwoPred
  omega

/-- Exact SourceProduct exit bridge for the public 2 mod 9 Poincare section.
No sufficiency theorem is assumed here: this only says that a low enough
section hit is already a lower-source merge. -/
theorem low_mod9_two_is_exit
    {s : State}
    (hy : endpoint s % 9 = 2)
    (hheight : 2 * endpoint s < 3 * s.source + 1) :
    Exit s := by
  right
  right
  let p := mod9TwoPred (endpoint s)
  refine ⟨p, 1, ?_, ?_, ?_⟩
  · exact mod9_two_pred_positive (endpoint s)
  · exact mod9_two_pred_lt_source hy hheight
  · simp [iter, p, mod9_two_pred_shortcut hy]

/-- Every 2 mod 9 hit on a minimal positive bad path must stay at or above the
exact source-relative 3/2 threshold.  Thus the remaining theorem is a height
statement on a compulsory section, not merely a residue-hitting statement. -/
theorem minimal_bad_mod9_two_height
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hy : iter shortcut k n % 9 = 2) :
    3 * n + 1 ≤ 2 * iter shortcut k n := by
  apply Nat.le_of_not_gt
  intro hheight
  have hyState : endpoint (stateAt n k) % 9 = 2 := by
    simpa [at_endpoint] using hy
  have hheightState :
      2 * endpoint (stateAt n k) <
        3 * (stateAt n k).source + 1 := by
    simpa [at_endpoint, at_source] using hheight
  exact minimal_path_no_exit hmin k
    (low_mod9_two_is_exit hyState hheightState)

/-- The exact missing bridge.  If every positive source has one 2 mod 9 hit
strictly below the 3/2 source threshold, positive Collatz follows. -/
def LowMod9TwoHit (n : Nat) : Prop :=
  ∃ k,
    iter shortcut k n % 9 = 2 ∧
    2 * iter shortcut k n < 3 * n + 1

theorem collatz_of_low_mod9_two_hit
    (hhit : ∀ n, 0 < n → LowMod9TwoHit n) :
    ∀ n, 0 < n → CollatzGood n := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    obtain ⟨k, hy, hheight⟩ := hhit n hmin.1.1
    have hbarrier := minimal_bad_mod9_two_height hmin hy
    omega
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hnone n ⟨hn, hbad⟩

#print axioms mod9_two_pred_shortcut
#print axioms low_mod9_two_is_exit
#print axioms minimal_bad_mod9_two_height
#print axioms collatz_of_low_mod9_two_hit

end SourceProduct
end CollatzFinal
