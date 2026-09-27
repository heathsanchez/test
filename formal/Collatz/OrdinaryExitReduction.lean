import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/-- The complete ordinary-orbit exit interface. It retains direct descent and
the lower-merge exits already exploited by the certificate machinery. -/
def OrdinaryExit (n y : Nat) : Prop :=
  Terminal y ∨
  (0 < y ∧ y < n) ∨
  ∃ p b, 0 < p ∧ p < n ∧ iter shortcut b p = y

/-- The source-product Exit predicate is exactly the ordinary-orbit exit
predicate along an actual normalized source path. -/
theorem exit_stateAt_iff_ordinary (n k : Nat) :
    Exit (stateAt n k) ↔ OrdinaryExit n (iter shortcut k n) := by
  simp [Exit, OrdinaryExit, at_endpoint, at_source]

/-- A hypothetical minimal positive bad source has no ordinary exit at any
depth: no terminal hit, no strict descent, and no merge with a smaller source. -/
theorem minimal_bad_has_no_ordinary_exit
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    ∀ k, ¬ OrdinaryExit n (iter shortcut k n) := by
  intro k hx
  exact minimal_path_no_exit hmin k
    ((exit_stateAt_iff_ordinary n k).2 hx)

/-- If every positive source eventually has an ordinary exit, every positive
source reaches 1. -/
theorem reaches_one_of_eventual_ordinary_exit
    (hexit :
      ∀ n, 0 < n → ∃ k, OrdinaryExit n (iter shortcut k n)) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    obtain ⟨k, hx⟩ := hexit n hmin.1.1
    exact minimal_bad_has_no_ordinary_exit hmin k hx
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

/-- Equivalent campaign-friendly form: it is enough to prove eventual ordinary
exit only for n>1, since n=1 is already terminal. -/
theorem reaches_one_of_eventual_ordinary_exit_gt_one
    (hexit :
      ∀ n, 1 < n → ∃ k, OrdinaryExit n (iter shortcut k n)) :
    ∀ n, 0 < n → ∃ k, iter shortcut k n = 1 := by
  apply reaches_one_of_eventual_ordinary_exit
  intro n hn
  by_cases h1 : n = 1
  · subst n
    refine ⟨0, ?_⟩
    left
    simp [iter, Terminal]
  · have hgt : 1 < n := by omega
    exact hexit n hgt

#print axioms exit_stateAt_iff_ordinary
#print axioms minimal_bad_has_no_ordinary_exit
#print axioms reaches_one_of_eventual_ordinary_exit
#print axioms reaches_one_of_eventual_ordinary_exit_gt_one

end SourceProduct
end CollatzFinal
