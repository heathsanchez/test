import Collatz.BiadicLexicographicCloseout
import Collatz.SourceProductAffine

namespace CollatzFinal
namespace SourceProduct

/-- A positive shortcut-periodic point.  This includes the terminal 1↔2 cycle;
the live/nonterminal restriction is imposed separately by callers. -/
def PositivePeriodic (n : Nat) : Prop :=
  0 < n ∧ ∃ k, 0 < k ∧ iter shortcut k n = n

/-- The actual affine return equation at depth k closes exactly at the
starting point.  By exact_affine this is equivalent to shortcut periodicity. -/
def ActualAffineFixed (n k : Nat) : Prop :=
  2 ^ k * n = 3 ^ oddCount n k * n + bias n k

theorem actualAffineFixed_iff_periodic_eq (n k : Nat) :
    ActualAffineFixed n k ↔ iter shortcut k n = n := by
  constructor
  · intro hfix
    have ha := exact_affine n k
    have hmul :
        2 ^ k * iter shortcut k n = 2 ^ k * n :=
      ha.trans hfix.symm
    exact Nat.eq_of_mul_eq_mul_left (by positivity) hmul
  · intro hper
    unfold ActualAffineFixed
    have ha := exact_affine n k
    simpa [hper] using ha.symm

theorem actualAffineFixed_positive_periodic
    {n k : Nat} (hn : 0 < n) (hk : 0 < k)
    (hfix : ActualAffineFixed n k) :
    PositivePeriodic n := by
  refine ⟨hn, k, hk, ?_⟩
  exact (actualAffineFixed_iff_periodic_eq n k).mp hfix

/-- Exact decomposition of the remaining V82 premise.

A universal macro classifier may expose either:
  * a genuine lexicographic rank decrease, or
  * an actual periodic endpoint.

If periodic endpoints are excluded on ZeroTailLive states, the periodic branch
disappears and the already-qualified V82 closeout proves Collatz.

Thus the universal residual is cleanly split into source-admitted macro
coverage/classification and the nonterminal-cycle obstruction; exact-zero
affine returns are not another rank coordinate. -/
theorem collatz_of_zero_tail_eventual_lex_or_periodic_free
    {Q : Type}
    (project : State → Q)
    (major minor : Q → Nat)
    (hmacro :
      ∀ s, ZeroTailLive s →
        ∃ j,
          ZeroTailLive (iter step j s) ∧
          ((major (project (iter step j s)) < major (project s) ∨
            (major (project (iter step j s)) = major (project s) ∧
             minor (project (iter step j s)) < minor (project s))) ∨
           PositivePeriodic (endpoint (iter step j s))))
    (hcyclefree :
      ∀ s, ZeroTailLive s → ¬ PositivePeriodic (endpoint s)) :
    ∀ n, 0 < n → CollatzGood n := by
  apply collatz_of_zero_tail_eventual_lex_rank project major minor
  intro s hs
  obtain ⟨j, hjlive, hdec | hper⟩ := hmacro s hs
  · exact ⟨j, hjlive, hdec⟩
  · exact False.elim ((hcyclefree (iter step j s) hjlive) hper)

/-- Equivalent formulation: if an actual affine fixed-return equation is the
only non-rank branch produced by the universal macro classifier, then excluding
positive live periodic points discharges that branch exactly. -/
theorem collatz_of_zero_tail_eventual_lex_or_affine_fixed
    {Q : Type}
    (project : State → Q)
    (major minor : Q → Nat)
    (hmacro :
      ∀ s, ZeroTailLive s →
        ∃ j k,
          ZeroTailLive (iter step j s) ∧
          0 < endpoint (iter step j s) ∧
          0 < k ∧
          ((major (project (iter step j s)) < major (project s) ∨
            (major (project (iter step j s)) = major (project s) ∧
             minor (project (iter step j s)) < minor (project s))) ∨
           ActualAffineFixed (endpoint (iter step j s)) k))
    (hcyclefree :
      ∀ s, ZeroTailLive s → ¬ PositivePeriodic (endpoint s)) :
    ∀ n, 0 < n → CollatzGood n := by
  apply collatz_of_zero_tail_eventual_lex_or_periodic_free
    project major minor
  · intro s hs
    obtain ⟨j, k, hjlive, hpos, hk, hdec | hfix⟩ := hmacro s hs
    · exact ⟨j, hjlive, Or.inl hdec⟩
    · refine ⟨j, hjlive, Or.inr ?_⟩
      exact actualAffineFixed_positive_periodic hpos hk hfix
  · exact hcyclefree

#print axioms actualAffineFixed_iff_periodic_eq
#print axioms actualAffineFixed_positive_periodic
#print axioms collatz_of_zero_tail_eventual_lex_or_periodic_free
#print axioms collatz_of_zero_tail_eventual_lex_or_affine_fixed

end SourceProduct
end CollatzFinal
