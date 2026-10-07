import Collatz.UniversalMacroResidual
import Collatz.ProtectedFutureQuotient

namespace CollatzFinal
namespace SourceProduct

/-- Compile source-precision refinement directly into V82's lexicographic
major rank.  The source itself is invariant along the exact SourceProduct
trajectory, so strictly increasing precision below that source strictly
decreases the remaining-precision fuel. -/
def sourcePrecisionMajor
    (precision : State → Nat) (s : State) : Nat :=
  remainingPrecision s.source (precision s)

/-- V85 universal closeout interface.

Every live zero-tail state need only produce one later live macro event of
exactly one of three consequential kinds:
  1. source precision strictly increases;
  2. precision is unchanged and the defect reserve strictly decreases;
  3. the later endpoint is genuinely positive periodic.

No additional rank coordinate or finite grammar assumption is used here.
The first two branches are compiled automatically into V82's lexicographic
rank; V84 identifies the third branch as the exact cycle obstruction. -/
theorem collatz_of_source_precision_macro_classification
    (precision reserve : State → Nat)
    (hprecision :
      ∀ s, ZeroTailLive s → precision s ≤ s.source)
    (hmacro :
      ∀ s, ZeroTailLive s →
        ∃ j,
          ZeroTailLive (iter step j s) ∧
          ((precision s < precision (iter step j s)) ∨
           (precision (iter step j s) = precision s ∧
             reserve (iter step j s) < reserve s) ∨
           PositivePeriodic (endpoint (iter step j s))))
    (hcyclefree :
      ∀ s, ZeroTailLive s → ¬ PositivePeriodic (endpoint s)) :
    ∀ n, 0 < n → CollatzGood n := by
  apply collatz_of_zero_tail_eventual_lex_or_periodic_free
    (project := id)
    (major := sourcePrecisionMajor precision)
    (minor := reserve)
  · intro s hs
    obtain ⟨j, hjlive, hswitch | hsame | hper⟩ := hmacro s hs
    · refine ⟨j, hjlive, Or.inl (Or.inl ?_)⟩
      change
        remainingPrecision (iter step j s).source
            (precision (iter step j s)) <
          remainingPrecision s.source (precision s)
      have hsrc :
          (iter step j s).source = s.source :=
        iter_step_source j s
      rw [hsrc]
      exact remainingPrecision_strict
        (hprecision s hs) hswitch
    · refine ⟨j, hjlive, Or.inl (Or.inr ⟨?_, hsame.2⟩)⟩
      change
        remainingPrecision (iter step j s).source
            (precision (iter step j s)) =
          remainingPrecision s.source (precision s)
      have hsrc :
          (iter step j s).source = s.source :=
        iter_step_source j s
      rw [hsrc, hsame.1]
    · exact ⟨j, hjlive, Or.inr hper⟩
  · exact hcyclefree

/-- Same closeout when the exceptional branch is presented as an actual
affine fixed-return certificate rather than periodicity. -/
theorem collatz_of_source_precision_macro_or_affine_fixed
    (precision reserve : State → Nat)
    (hprecision :
      ∀ s, ZeroTailLive s → precision s ≤ s.source)
    (hmacro :
      ∀ s, ZeroTailLive s →
        ∃ j k,
          ZeroTailLive (iter step j s) ∧
          0 < endpoint (iter step j s) ∧
          0 < k ∧
          ((precision s < precision (iter step j s)) ∨
           (precision (iter step j s) = precision s ∧
             reserve (iter step j s) < reserve s) ∨
           ActualAffineFixed (endpoint (iter step j s)) k))
    (hcyclefree :
      ∀ s, ZeroTailLive s → ¬ PositivePeriodic (endpoint s)) :
    ∀ n, 0 < n → CollatzGood n := by
  apply collatz_of_source_precision_macro_classification
    precision reserve hprecision
  · intro s hs
    obtain ⟨j, k, hjlive, hpos, hk, hswitch | hsame | hfix⟩ := hmacro s hs
    · exact ⟨j, hjlive, Or.inl hswitch⟩
    · exact ⟨j, hjlive, Or.inr (Or.inl hsame)⟩
    · refine ⟨j, hjlive, Or.inr (Or.inr ?_)⟩
      exact actualAffineFixed_positive_periodic hpos hk hfix
  · exact hcyclefree

#print axioms sourcePrecisionMajor
#print axioms collatz_of_source_precision_macro_classification
#print axioms collatz_of_source_precision_macro_or_affine_fixed

end SourceProduct
end CollatzFinal
