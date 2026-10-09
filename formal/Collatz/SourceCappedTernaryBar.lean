import Collatz.ParityCollisionBridge
import Collatz.OrdinaryExitReduction

namespace CollatzFinal
namespace SourceProduct

/-- The actual orbit of the ORIGINAL source visits the smaller odd-inverse cone. -/
def SourceCappedTernaryReturn (n : Nat) : Prop :=
  ∃ k, (iter shortcut k n) % 3 = 2 ∧
    2 * iter shortcut k n - 1 < 3 * n

/-- A source-capped actual ternary endpoint gives a genuine smaller
positive predecessor with an equal future. -/
theorem capped_ternary_return_earns_lower_merge
    {n : Nat} (_hn : 1 < n)
    (hc : SourceCappedTernaryReturn n) :
    ∃ p, 0 < p ∧ LowerMerge shortcut n p := by
  obtain ⟨k, hmod, hcap⟩ := hc
  let y := iter shortcut k n
  let p := (2 * y - 1) / 3
  have hmodY : y % 3 = 2 := hmod
  have hy : 1 < y := by omega
  have heq0 : 2 * y - 1 = 3 * p := by
    dsimp [p]
    omega
  have heq : 2 * y = 3 * p + 1 := by omega
  have hp : 0 < p := by omega
  have hcapY : 2 * y - 1 < 3 * n := hcap
  have hlt : p < n := by omega
  have hstep : shortcut p = y := exact_inverse_odd_step y p heq
  refine ⟨p, hp, ⟨hlt, k, 1, ?_⟩⟩
  change iter shortcut k n = shortcut p
  exact hstep.symm

/-- Conditional reduction: this theorem does not establish its hbar premise. -/
theorem collatz_of_source_capped_ternary_bar
    (hbar : ∀ n, 1 < n → SourceCappedTernaryReturn n) :
    ∀ n, 0 < n → CollatzGood n := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
      intro hn
      by_cases hone : n = 1
      · subst n
        exact ⟨0, Or.inl rfl⟩
      have hgt : 1 < n := by omega
      obtain ⟨p, hp, hm⟩ :=
        capped_ternary_return_earns_lower_merge hgt (hbar n hgt)
      have hpgood : CollatzGood p := ih p hm.1 hp
      exact lower_merge_preserves_eventual shortcut Terminal
        terminal_forward_invariant hm hpgood

/-- Termination implies a capped return because every good orbit reaches 2. -/
theorem source_capped_ternary_bar_of_collatz
    (hcollatz : ∀ n, 0 < n → CollatzGood n) :
    ∀ n, 1 < n → SourceCappedTernaryReturn n := by
  intro n hn
  obtain ⟨k, hk⟩ :=
    collatzGood_eventually_one (hcollatz n (by omega))
  have htwo : iter shortcut (k + 1) n = 2 := by
    rw [iter_succ_last, hk, shortcut_one]
  refine ⟨k + 1, ?_, ?_⟩
  · simpa only [htwo] using (show 2 % 3 = 2 from by decide)
  · rw [htwo]
    omega

/-- Equivalence is formal only once compiled; neither side is established here. -/
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
