import Collatz.PersistentCorridor

namespace CollatzFinal
namespace SourceProduct

/-- The odd counter changes by either zero or one at each ordinary shortcut
step. -/
theorem oddCount_succ_bounds (n k : Nat) :
    oddCount n k ≤ oddCount n (k + 1) ∧
    oddCount n (k + 1) ≤ oddCount n k + 1 := by
  simp only [oddCount]
  split <;> omega

/-- Discrete intermediate-value principle for the odd counter. If by depth K
the counter has passed Q, then some previous step crosses exactly Q -> Q+1. -/
theorem oddCount_exact_boundary
    {n Q K : Nat}
    (hK : Q < oddCount n K) :
    ∃ k, k < K ∧
      oddCount n k = Q ∧
      oddCount n (k + 1) = Q + 1 := by
  induction K with
  | zero =>
      simp [oddCount] at hK
  | succ K ih =>
      by_cases hprev : Q < oddCount n K
      · obtain ⟨k, hk, hq, hqs⟩ := ih hprev
        exact ⟨k, by omega, hq, hqs⟩
      · have hle : oddCount n K ≤ Q := by omega
        have hb := oddCount_succ_bounds n K
        have hq : oddCount n K = Q := by omega
        have hqs : oddCount n (K + 1) = Q + 1 := by omega
        exact ⟨K, Nat.lt_succ_self K, hq, hqs⟩

/-- The exact one-step Crystal target left by V13. Only the first transition
from 2*n odd steps to 2*n+1 odd steps is exposed.

This is deliberately source-relative and local: no all-depth high-odd
coverage, global rank, or arbitrary post-diagonal premise is assumed. -/
def FirstSuperHighOddExitCoverage : Prop :=
  ∀ n k, 1 < n → n % 2 = 1 →
    oddCount n k = 2 * n →
    oddCount n (k + 1) = 2 * n + 1 →
    ¬ OrdinaryExit n (iter shortcut k n) →
    OrdinaryExit n (iter shortcut (k + 1) n)

/-- V13 guarantees that every hypothetical minimal bad source reaches the
2*n -> 2*n+1 odd-count boundary by depth 4*n. Therefore exit at that single
boundary is sufficient for the full positive Collatz theorem. -/
theorem reaches_one_of_first_superhigh_odd_exit
    (hBoundary : FirstSuperHighOddExitCoverage) :
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
    have hodd : n % 2 = 1 := positive_minimal_bad_odd hmin
    have hstrict :
        2 * n < oddCount n (4 * n) :=
      minimal_bad_quadruple_depth_strict_double_diagonal hmin
    obtain ⟨k, _hklt, hq, hqs⟩ :=
      oddCount_exact_boundary (n := n) (Q := 2 * n)
        (K := 4 * n) hstrict
    have hno : ¬ OrdinaryExit n (iter shortcut k n) :=
      minimal_bad_has_no_ordinary_exit hmin k
    have hexit :=
      hBoundary n k hgt hodd hq hqs hno
    exact minimal_bad_has_no_ordinary_exit hmin (k + 1) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

/-- At the predecessor of the first super-high-odd boundary, V13's persistent
corridor leaves only coefficient survival or exact deficit one. -/
theorem minimal_bad_first_superhigh_predecessor_corridor
    {n k : Nat}
    (hmin : MinimalBad PositiveBad n)
    (hq : oddCount n k = 2 * n) :
    qmin k ≤ oddCount n k ∨
      oddCount n k + 1 = qmin k := by
  have hn : 0 < n := hmin.1.1
  have hqpos : 0 < oddCount n k := by rw [hq]; omega
  have hq2 : oddCount n k ≤ 2 * n := by
    simpa [hq]
  exact minimal_bad_persistent_survival_or_deficit_one
    hmin hqpos hq2

/-- Crossing 2*n -> 2*n+1 means the boundary step itself is odd. -/
theorem first_superhigh_boundary_step_odd
    {n k : Nat}
    (hq : oddCount n k = 2 * n)
    (hqs : oddCount n (k + 1) = 2 * n + 1) :
    iter shortcut k n % 2 ≠ 0 := by
  intro he
  have hs : oddCount n (k + 1) = oddCount n k := by
    change (if iter shortcut k n % 2 = 0
      then oddCount n k else oddCount n k + 1) = oddCount n k
    rw [if_pos he]
  omega


/-- Crystal's stronger bounded separator, stated only as an explicit premise.
No-exit states never accumulate more than four-thirds as many odd steps as the
source value. This is NOT proved here; the theorem below records exactly why
proving it would close Collatz. -/
def FourThirdsNoExitOddCap : Prop :=
  ∀ n k, 1 < n →
    ¬ OrdinaryExit n (iter shortcut k n) →
    3 * oddCount n k ≤ 4 * n

/-- The four-thirds cap contradicts V13's strict second diagonal at depth 4*n,
so it is by itself sufficient for full positive Collatz termination. -/
theorem reaches_one_of_four_thirds_no_exit_cap
    (hCap : FourThirdsNoExitOddCap) :
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
    have hno :
        ¬ OrdinaryExit n (iter shortcut (4 * n) n) :=
      minimal_bad_has_no_ordinary_exit hmin (4 * n)
    have hcap :
        3 * oddCount n (4 * n) ≤ 4 * n :=
      hCap n (4 * n) hgt hno
    have hstrict :
        2 * n < oddCount n (4 * n) :=
      minimal_bad_quadruple_depth_strict_double_diagonal hmin
    omega
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms oddCount_exact_boundary
#print axioms reaches_one_of_first_superhigh_odd_exit
#print axioms minimal_bad_first_superhigh_predecessor_corridor
#print axioms first_superhigh_boundary_step_odd
#print axioms reaches_one_of_four_thirds_no_exit_cap

end SourceProduct
end CollatzFinal
