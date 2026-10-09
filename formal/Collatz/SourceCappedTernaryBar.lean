import Collatz.CylinderCoalescence

namespace CollatzFinal
namespace SourceProduct

/-- One actual shortcut iterate lies in the odd-inverse cone below the
    unchanged ORIGINAL positive source. This is a proof target, not an axiom. -/
def SourceCappedTernaryReturn (n : Nat) : Prop :=
  ∃ k y : Nat,
    iter shortcut k n = y ∧
    y % 3 = 2 ∧
    2 * y - 1 < 3 * n

/-- A capped hit gives a strictly smaller positive source that reaches
    the same genuine trajectory endpoint by one shortcut step. -/
theorem source_capped_hit_lower_merge
    (n : Nat) (h : SourceCappedTernaryReturn n) :
    ∃ p : Nat, 0 < p ∧ LowerMerge shortcut n p := by
  obtain ⟨k, y, hy, hmod, hcap⟩ := h
  let p := (2 * y - 1) / 3
  have heq : 2 * y = 3 * p + 1 := by
    dsimp [p]
    omega
  have hpPos : 0 < p := by omega
  have hpLess : p < n := by omega
  have hstep : shortcut p = y := exact_inverse_odd_step y p heq
  refine ⟨p, hpPos, hpLess, k, 1, ?_⟩
  calc
    iter shortcut k n = y := hy
    _ = iter shortcut 1 p := by simp [iter, hstep]

/-- The universal source-capped hit bar would settle positive Collatz,
    by actual smaller-source coalescence and strong induction. -/
theorem collatz_of_universal_source_capped_bar
    (hbar : ∀ n : Nat, 1 < n → SourceCappedTernaryReturn n) :
    ∀ n : Nat, 0 < n → CollatzGood n := by
  intro n
  induction n using Nat.strongRecOn with
  | ind n ih =>
      intro hn
      by_cases hone : n = 1
      · subst n
        exact ⟨0, Or.inl rfl⟩
      have hgt : 1 < n := by omega
      obtain ⟨p, hpPos, hm⟩ :=
        source_capped_hit_lower_merge n (hbar n hgt)
      have hp : CollatzGood p := ih p hm.1 hpPos
      exact lower_merge_preserves_eventual shortcut Terminal
        terminal_forward_invariant hm hp

/-- If Collatz holds, the orbit reaches 2, which satisfies the cap. -/
theorem source_capped_bar_of_collatz
    (hgood : ∀ n : Nat, 0 < n → CollatzGood n) :
    ∀ n : Nat, 1 < n → SourceCappedTernaryReturn n := by
  intro n hn
  obtain ⟨k, hterminal⟩ := hgood n (by omega)
  have hcap : 2 * 2 - 1 < 3 * n := by omega
  rcases hterminal with h1 | h2
  · have hhit : iter shortcut (k + 1) n = 2 := by
      rw [iter_add]
      simp [h1, iter, shortcut_one]
    exact ⟨k + 1, 2, hhit, by decide, hcap⟩
  · exact ⟨k, 2, h2, by decide, hcap⟩

/-- Exact equivalence: this isolates the unresolved universal source bar;
    it does NOT prove the bar, nor the Collatz conjecture. -/
theorem universal_source_capped_bar_iff_collatz :
    (∀ n : Nat, 1 < n → SourceCappedTernaryReturn n) ↔
    (∀ n : Nat, 0 < n → CollatzGood n) := by
  constructor
  · exact collatz_of_universal_source_capped_bar
  · exact source_capped_bar_of_collatz

#print axioms source_capped_hit_lower_merge
#print axioms collatz_of_universal_source_capped_bar
#print axioms source_capped_bar_of_collatz
#print axioms universal_source_capped_bar_iff_collatz

end SourceProduct
end CollatzFinal
