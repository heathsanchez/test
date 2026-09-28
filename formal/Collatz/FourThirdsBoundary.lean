import Collatz.FirstSuperHighBoundary
import Collatz.OrdinaryInverseOdd

namespace CollatzFinal
namespace SourceProduct

/-- The source itself cannot be 2 modulo 3 on a minimal bad path: its exact
odd predecessor (2*n-1)/3 is positive, smaller, and reaches n in one shortcut
step. -/
theorem minimal_bad_source_not_mod3_two
    {n : Nat}
    (hmin : MinimalBad PositiveBad n) :
    n % 3 ≠ 2 := by
  intro hmod
  have hp := inverse_odd_predecessor_of_mod3_two hmod
  let p := (2 * n - 1) / 3
  have hpos : 0 < p := by
    simpa [p] using hp.1
  have hstep : shortcut p = n := by
    simpa [p] using hp.2.2
  have hlt : p < n := by
    let a := n / 3
    have hnform : n = 3 * a + 2 := by
      have hd := Nat.mod_add_div n 3
      dsimp [a]
      omega
    have hpform : p = 2 * a + 1 := by
      dsimp [p]
      rw [hnform]
      omega
    rw [hpform, hnform]
    omega
  apply positive_minimal_no_lower_merge hmin p hpos
  refine ⟨hlt, 0, 1, ?_⟩
  simp [iter, hstep]

/-- The floor Q=floor(4n/3) is the unique odd-count boundary immediately below
the four-thirds cap. -/
theorem four_thirds_floor_boundary (n : Nat) :
    3 * ((4 * n) / 3) ≤ 4 * n ∧
    4 * n < 3 * (((4 * n) / 3) + 1) := by
  have hdiv := Nat.mod_add_div (4 * n) 3
  have hmod := Nat.mod_lt (4 * n) (by decide : 0 < 3)
  omega

/-- Four is one modulo three, so the remainder at the four-thirds boundary is
exactly the source residue modulo three. -/
theorem four_mul_mod_three (n : Nat) :
    (4 * n) % 3 = n % 3 := by
  omega

/-- For every source above one, the four-thirds odd-count boundary lies
strictly below the V13 double-source diagonal. -/
theorem four_thirds_floor_lt_double
    {n : Nat} (hgt : 1 < n) :
    (4 * n) / 3 < 2 * n := by
  have hdiv := Nat.mod_add_div (4 * n) 3
  have hmod := Nat.mod_lt (4 * n) (by decide : 0 < 3)
  omega

/-- Crystal only needs to close the two source-primitive four-thirds boundary
classes left after the exact inverse-odd source elimination. -/
def FirstFourThirdsBoundaryExit01Coverage : Prop :=
  ∀ n k, 1 < n → n % 2 = 1 →
    (n % 3 = 0 ∨ n % 3 = 1) →
    oddCount n k = (4 * n) / 3 →
    oddCount n (k + 1) = (4 * n) / 3 + 1 →
    ¬ OrdinaryExit n (iter shortcut k n) →
    OrdinaryExit n (iter shortcut (k + 1) n)

/-- V13 forces every minimal bad path beyond the four-thirds floor by depth
4*n.  The source-2-mod-3 boundary is impossible by a direct lower predecessor,
so exit on only the remaining source residues 0 and 1 mod 3 already closes
positive Collatz. -/
theorem reaches_one_of_first_four_thirds_boundary_01_exit
    (hBoundary : FirstFourThirdsBoundaryExit01Coverage) :
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
    have hnot2 : n % 3 ≠ 2 := minimal_bad_source_not_mod3_two hmin
    have hmodlt : n % 3 < 3 := Nat.mod_lt n (by decide)
    have hclass : n % 3 = 0 ∨ n % 3 = 1 := by omega
    let Q := (4 * n) / 3
    have hQlt : Q < 2 * n := by
      dsimp [Q]
      exact four_thirds_floor_lt_double hgt
    have hstrict :
        2 * n < oddCount n (4 * n) :=
      minimal_bad_quadruple_depth_strict_double_diagonal hmin
    have hQfinal : Q < oddCount n (4 * n) := by omega
    obtain ⟨k, _hklt, hq, hqs⟩ :=
      oddCount_exact_boundary (n := n) (Q := Q)
        (K := 4 * n) hQfinal
    have hno : ¬ OrdinaryExit n (iter shortcut k n) :=
      minimal_bad_has_no_ordinary_exit hmin k
    have hexit :=
      hBoundary n k hgt hodd hclass
        (by simpa [Q] using hq)
        (by simpa [Q] using hqs)
        hno
    exact minimal_bad_has_no_ordinary_exit hmin (k + 1) hexit
  intro n hn
  have hgood : CollatzGood n := by
    apply Classical.byContradiction
    intro hbad
    exact hnone n ⟨hn, hbad⟩
  exact collatzGood_eventually_one hgood

#print axioms minimal_bad_source_not_mod3_two
#print axioms four_thirds_floor_boundary
#print axioms four_mul_mod_three
#print axioms four_thirds_floor_lt_double
#print axioms reaches_one_of_first_four_thirds_boundary_01_exit

end SourceProduct
end CollatzFinal
