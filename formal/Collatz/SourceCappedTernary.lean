import Collatz.SourceProduct

namespace CollatzFinal
namespace SourceProduct

/-!
The exact source-capped ternary cone. This formulation is equivalent
to positive Collatz, NOT proof that its universal premise holds.
-/

def SourceCappedTernaryHit (n : Nat) : Prop :=
  ∃ k t : Nat, iter shortcut k n = 3*t+2 ∧ 2*t+1 < n

theorem ternary_odd_predecessor (t : Nat) :
    shortcut (2*t+1) = 3*t+2 := by
  have h : (2*t+1)%2 ≠ 0 := by omega
  simp only [shortcut, h, ite_false]
  omega

theorem source_capped_hit_yields_lower_merge
    (n : Nat) (h : SourceCappedTernaryHit n) :
    ∃ p, 0 < p ∧ LowerMerge shortcut n p := by
  obtain ⟨k,t,heq,hlt⟩ := h
  refine ⟨2*t+1, by omega, ⟨hlt,k,1,?_⟩⟩
  change iter shortcut k n = shortcut (2*t+1)
  rw [heq]
  exact (ternary_odd_predecessor t).symm

/-- Every least bad positive source avoids the whole capped cone,
not just selected bounded witnesses. This is conditional on the
hypothetical MinimalBad source, which Collatz would exclude. -/
theorem minimal_bad_avoids_capped_ternary
    {n : Nat} (hmin : MinimalBad PositiveBad n) :
    ¬ SourceCappedTernaryHit n := by
  intro hh
  obtain ⟨p,hp,hm⟩ := source_capped_hit_yields_lower_merge n hh
  exact positive_minimal_no_lower_merge hmin p hp hm

/-- Proving the universal capped-cone hit would suffice for Collatz.
No theorem above manufactures this missing universal witness. -/
theorem collatz_of_all_source_capped_ternary_hits
    (hbar : ∀ n, 1 < n → SourceCappedTernaryHit n) :
    ∀ n, 0 < n → CollatzGood n := by
  have hno : ∀ n, ¬ PositiveBad n := by
    apply no_bad_of_no_minimal PositiveBad
    intro n hmin
    have hgt : 1 < n := by
      by_contra h
      have h1 : n = 1 := by omega
      subst n
      exact hmin.1.2 ⟨0, Or.inl rfl⟩
    exact minimal_bad_avoids_capped_ternary hmin (hbar n hgt)
  intro n hn
  apply Classical.byContradiction
  intro hbad
  exact hno n ⟨hn,hbad⟩

theorem capped_ternary_hits_of_collatz
    (hgood : ∀ n, 0 < n → CollatzGood n)
    (n : Nat) (hn : 1 < n) :
    SourceCappedTernaryHit n := by
  obtain ⟨k,hk⟩ := hgood n (by omega)
  rcases hk with h1 | h2
  · have ht : iter shortcut (k+1) n = 2 := by
      rw [iter_add, h1]
      exact shortcut_one
    exact ⟨k+1,0,ht,by omega⟩
  · exact ⟨k,0,h2,by omega⟩

theorem collatz_iff_capped_ternary_bar :
    (∀ n, 0 < n → CollatzGood n) ↔
      (∀ n, 1 < n → SourceCappedTernaryHit n) := by
  constructor
  · exact capped_ternary_hits_of_collatz
  · exact collatz_of_all_source_capped_ternary_hits

#print axioms ternary_odd_predecessor
#print axioms source_capped_hit_yields_lower_merge
#print axioms minimal_bad_avoids_capped_ternary
#print axioms collatz_of_all_source_capped_ternary_hits
#print axioms collatz_iff_capped_ternary_bar

end SourceProduct
end CollatzFinal
