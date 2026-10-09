import Collatz.ParityCollisionBridge
import Collatz.OrdinaryExitReduction

namespace CollatzFinal
namespace SourceProduct

/-- Exact source-relative finish-line predicate.
For a fixed original source n, an actual shortcut endpoint y of its orbit
is 2 mod 3 and has an odd inverse predecessor p=(2*y-1)/3<n.
This is NOT assumed true for every n. -/
def SourceCappedTernaryReturn (n : Nat) : Prop :=
  ∃ k, (iter shortcut k n) % 3 = 2 ∧
    2 * iter shortcut k n - 1 < 3 * n

/-- An admissible capped ternary return provides an actual smaller
positive source that merges after one odd shortcut step. -/
theorem capped_ternary_return_earns_lower_merge
    {n : Nat} (_hn : 1 < n)
    (hc : SourceCappedTernaryReturn n) :
    ∃ p, 0 < p ∧ LowerMerge shortcut n p := by
  obtain ⟨k, hmod, hcap⟩ := hc
  let y := iter shortcut k n
  let p := (2 * y - 1) / 3
  have hy : 1 < y := by
    dsimp [y] at hmod ⊢
    omega
  have heq0 : 2 * y - 1 = 3 * p := by
    dsimp [p]
    omega
  have heq : 2 * y = 3 * p + 1 := by omega
  have hp : 0 < p := by omega
  have hlt : p < n := by
    change 2 * y - 1 < 3 * n at hcap
    omega
  have hstep : shortcut p = y := exact_inverse_odd_step y p heq
  refine ⟨p, hp, ⟨hlt, k, 1, ?_⟩⟩
  change iter shortcut k n = shortcut p
  exact hstep.symm

/-- If every positive source above 1 admits such a capped ternary return,
then every positive natural terminates by strong induction on the
ORIGINAL source. This theorem is explicitly conditional. -/
theorem collatz_of_source_capped_ternary_bar
    (hbar : ∀ n, 1 < n → SourceCappedTernaryReturn n) :
    ∀ n, 0 < n → CollatzGood n := by
  have hnone : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hn : 1 < n := by
      by_cases hgt : 1 < n
      · exact hgt
      · have hnpos : 0 < n := hmin.1.1
        have hone : n = 1 := by omega
        subst n
        have hgood : CollatzGood 1 := ⟨0, by simp [iter, Terminal]⟩
        exact False.elim (hmin.1.2 hgood)
    obtain ⟨p, hp, hm⟩ :=
      capped_ternary_return_earns_lower_merge hn (hbar n hn)
    exact positive_minimal_no_lower_merge hmin p hp hm
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hnone n ⟨hn, hbad⟩

/-- If Collatz termination already holds, y=2 on the actual
forward orbit yields a source-capped ternary return for each n>1. -/
theorem source_capped_ternary_bar_of_collatz
    (hcollatz : ∀ n, 0 < n → CollatzGood n) :
    ∀ n, 1 < n → SourceCappedTernaryReturn n := by
  intro n hn
  obtain ⟨k, hk⟩ :=
    collatzGood_eventually_one (hcollatz n (by omega))
  refine ⟨k + 1, ?_, ?_⟩
  · rw [iter_succ_last, hk, shortcut_one]
  · rw [iter_succ_last, hk, shortcut_one]
    omega

/-- Exact QED seam: mathematical equivalence, not a proof of either side.
The unproved direction in practice is establishing hbar unconditionally. -/
theorem collatz_iff_source_capped_ternary_bar :
    (∀ n, 0 < n → CollatzGood n) ↔
    (∀ n, 1 < n → SourceCappedTernaryReturn n) := by
  constructor
  · exact source_capped_ternary_bar_of_collatz
  · exact collatz_of_source_capped_ternary_bar

#print axioms capped_ternary_return_earns_lower_merge
#print axioms collatz_of_source_capped_ternary_bar
#print axioms source_capped_ternary_bar_of_collatz
#print axioms collatz_iff_source_capped_ternary_bar

end SourceProduct
end CollatzFinal
