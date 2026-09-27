import Collatz.FirstCrossingGap

namespace CollatzFinal
namespace SourceProduct

/-- Exact three-step reverse certificate on the 4 mod 9 endpoint class.
The reverse word is EOO: y <- 2y <- (4y-1)/3 <- (8y-5)/9. -/
theorem eoo_predecessor_of_mod9_four
    {y : Nat}
    (hy : y % 9 = 4) :
    0 < (8 * y - 5) / 9 ∧
    iter shortcut 3 ((8 * y - 5) / 9) = y := by
  let a := y / 9
  have hy' : y = 9 * a + 4 := by
    dsimp [a]
    omega
  have hp : (8 * y - 5) / 9 = 8 * a + 3 := by
    rw [hy']
    omega
  rw [hp, hy']
  constructor
  · omega
  · have h1 : shortcut (8 * a + 3) = 12 * a + 5 := by
      unfold shortcut
      have ho : (8 * a + 3) % 2 ≠ 0 := by omega
      simp only [ho, ite_false]
      omega
    have h2 : shortcut (12 * a + 5) = 18 * a + 8 := by
      unfold shortcut
      have ho : (12 * a + 5) % 2 ≠ 0 := by omega
      simp only [ho, ite_false]
      omega
    have h3 : shortcut (18 * a + 8) = 9 * a + 4 := by
      unfold shortcut
      have he : (18 * a + 8) % 2 = 0 := by omega
      simp only [he, ite_true]
      omega
    simp [iter, h1, h2, h3]

/-- If the EOO predecessor lies below the source, it is an ordinary lower merge. -/
theorem ordinary_exit_of_eoo_predecessor_lt
    {n y : Nat}
    (hy : y % 9 = 4)
    (hlt : (8 * y - 5) / 9 < n) :
    OrdinaryExit n y := by
  have hp := eoo_predecessor_of_mod9_four hy
  exact Or.inr (Or.inr
    ⟨(8 * y - 5) / 9, 3, hp.1, hlt, hp.2⟩)

/-- Hence a no-exit endpoint in the 4 mod 9 class obeys the exact EOO
forbidden-window inequality 9*n+5 <= 8*y. -/
theorem no_ordinary_exit_mod9_four_growth
    {n y : Nat}
    (hno : ¬ OrdinaryExit n y)
    (hy : y % 9 = 4) :
    9 * n + 5 ≤ 8 * y := by
  have hge : n ≤ (8 * y - 5) / 9 := by
    apply Nat.le_of_not_gt
    intro hlt
    exact hno (ordinary_exit_of_eoo_predecessor_lt hy hlt)
  let a := y / 9
  have hy' : y = 9 * a + 4 := by
    dsimp [a]
    omega
  have hp : (8 * y - 5) / 9 = 8 * a + 3 := by
    rw [hy']
    omega
  rw [hp] at hge
  rw [hy']
  omega

/-- Joining the additive first-crossing gap with the depth-one odd inverse:
a hard endpoint in residue 2 mod 3 can occur only if its critical odd count
is already more than three-halves of the source. -/
theorem hard_first_crossing_mod3_two_forces_large_q
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hy : iter shortcut (k + 1) n % 3 = 2) :
    3 * n + 3 < 2 * oddCount n (k + 1) := by
  have hge := hard_first_crossing_endpoint_ge_source hn hhard
  have hgrowth := hard_first_crossing_mod3_two_growth hhard hy
  have hgap := hard_first_crossing_additive_gap hn hhard
  omega

/-- The EOO residue class gives a second quantitative forbidden window. -/
theorem hard_first_crossing_mod9_four_forces_large_q
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hy : iter shortcut (k + 1) n % 9 = 4) :
    3 * n + 15 < 8 * oddCount n (k + 1) := by
  have hge := hard_first_crossing_endpoint_ge_source hn hhard
  have hgrowth := no_ordinary_exit_mod9_four_growth hhard.2 hy
  have hgap := hard_first_crossing_additive_gap hn hhard
  omega

/-- Small-q hard crossings therefore cannot terminate in the strongest
contractive reverse residue class. -/
theorem hard_first_crossing_not_mod3_two_of_q_bound
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hq : 2 * oddCount n (k + 1) ≤ 3 * n + 3) :
    iter shortcut (k + 1) n % 3 ≠ 2 := by
  intro hy
  have hlarge :=
    hard_first_crossing_mod3_two_forces_large_q hn hhard hy
  omega

/-- Likewise the 4 mod 9 EOO class is impossible below its exact q/source
threshold. -/
theorem hard_first_crossing_not_mod9_four_of_q_bound
    {n k : Nat}
    (hn : 0 < n)
    (hhard : HardFirstCrossing n k)
    (hq : 8 * oddCount n (k + 1) ≤ 3 * n + 15) :
    iter shortcut (k + 1) n % 9 ≠ 4 := by
  intro hy
  have hlarge :=
    hard_first_crossing_mod9_four_forces_large_q hn hhard hy
  omega

#print axioms eoo_predecessor_of_mod9_four
#print axioms ordinary_exit_of_eoo_predecessor_lt
#print axioms no_ordinary_exit_mod9_four_growth
#print axioms hard_first_crossing_mod3_two_forces_large_q
#print axioms hard_first_crossing_mod9_four_forces_large_q
#print axioms hard_first_crossing_not_mod3_two_of_q_bound
#print axioms hard_first_crossing_not_mod9_four_of_q_bound

end SourceProduct
end CollatzFinal
