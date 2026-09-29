import Collatz.FourThirdsAdmission

namespace CollatzFinal
namespace SourceProduct

def FourThirdsOddConstructorCoverage : Prop :=
  ∀ n k, 1 < n →
    n % 2 = 1 →
    oddCount n k = (4 * n) / 3 →
    iter shortcut k n % 2 = 1 →
    OrdinaryExit n (iter shortcut k n) ∨
      (iter shortcut k n % 8 = 5 ∧
        iter shortcut k n ≤ 4 * n)

theorem oddCount_boundary_step_odd
    {n k Q : Nat}
    (hq : oddCount n k = Q)
    (hqs : oddCount n (k + 1) = Q + 1) :
    iter shortcut k n % 2 = 1 := by
  have hmodlt : iter shortcut k n % 2 < 2 :=
    Nat.mod_lt _ (by decide)
  by_cases he : iter shortcut k n % 2 = 0
  · have hsame :
        oddCount n (k + 1) = oddCount n k := by
      simp [oddCount, he]
    omega
  · omega

theorem reaches_one_of_four_thirds_odd_constructor_coverage
    (hCov : FourThirdsOddConstructorCoverage) :
    ∀ n, 0 < n → ∃ t, iter shortcut t n = 1 := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := by
      have hn : 0 < n := hmin.1.1
      have hne : n ≠ 1 := by
        intro heq
        apply hmin.1.2
        subst n
        exact ⟨0, by simp [iter, Terminal]⟩
      omega
    have hoddSource : n % 2 = 1 :=
      positive_minimal_bad_odd hmin
    let Q := (4 * n) / 3
    have hQlt2 : Q < 2 * n := by
      dsimp [Q]
      exact four_thirds_floor_lt_double hgt
    have hstrict :
        2 * n < oddCount n (4 * n) :=
      minimal_bad_quadruple_depth_strict_double_diagonal hmin
    have hQlt :
        Q < oddCount n (4 * n) := by
      omega
    obtain ⟨k, _hklt, hq, hqs⟩ :=
      oddCount_exact_boundary
        (n := n) (Q := Q) (K := 4 * n) hQlt
    have hxodd :
        iter shortcut k n % 2 = 1 :=
      oddCount_boundary_step_odd hq hqs
    rcases hCov n k hgt hoddSource
        (by simpa [Q] using hq) hxodd with hexit | hsplice
    · exact minimal_bad_has_no_ordinary_exit hmin k hexit
    · have hexit3 :
          OrdinaryExit n (iter shortcut (k + 3) n) := by
        rw [iter_add]
        exact ordinary_exit_after_quarter_splice
          hsplice.1 hsplice.2
      exact minimal_bad_has_no_ordinary_exit hmin (k + 3) hexit3
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms oddCount_boundary_step_odd
#print axioms reaches_one_of_four_thirds_odd_constructor_coverage

end SourceProduct
end CollatzFinal
