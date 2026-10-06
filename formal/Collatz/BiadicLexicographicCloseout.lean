import Collatz.BiadicRankedNormalization

namespace CollatzFinal
namespace SourceProduct

/-- Two-level macro closeout. The major rank may decrease while the minor rank
is allowed to recharge arbitrarily; when the major rank is unchanged, the
minor rank must strictly decrease. This is the formal shape needed by the
source-precision / defect-reserve decomposition. -/
theorem zero_tail_kernel_empty_of_eventual_lex_rank
    {Q : Type}
    (project : State → Q)
    (major minor : Q → Nat)
    (hprogress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          ZeroTailLive (iter step j s) ∧
          (major (project (iter step j s)) < major (project s) ∨
            (major (project (iter step j s)) = major (project s) ∧
             minor (project (iter step j s)) < minor (project s)))) :
    KernelEmpty ZeroTailLive Next := by
  intro S hsub hPost
  have aux :
      ∀ a, ∀ b, ∀ s,
        major (project s) = a →
        minor (project s) = b →
        ¬ S s := by
    intro a
    induction a using Nat.strongRecOn with
    | ind a ihA =>
        intro b
        induction b using Nat.strongRecOn with
        | ind b ihB =>
            intro s hmajor hminor hs
            have hzero : ZeroTailLive s := hsub s hs
            obtain ⟨j, hjlive, hdec⟩ := hprogress s hzero
            have hSj : S (iter step j s) :=
              postfixed_iter_mem S hPost j s hs
            rcases hdec with hMaj | hMin
            · have hltA :
                  major (project (iter step j s)) < a := by
                calc
                  major (project (iter step j s)) <
                      major (project s) := hMaj
                  _ = a := hmajor
              exact ihA
                (major (project (iter step j s))) hltA
                (minor (project (iter step j s)))
                (iter step j s) rfl rfl hSj
            · have hEqA :
                  major (project (iter step j s)) = a :=
                hMin.1.trans hmajor
              have hltB :
                  minor (project (iter step j s)) < b := by
                calc
                  minor (project (iter step j s)) <
                      minor (project s) := hMin.2
                  _ = b := hminor
              exact ihB
                (minor (project (iter step j s))) hltB
                (iter step j s) hEqA rfl hSj
  intro s
  exact aux (major (project s)) (minor (project s)) s rfl rfl

/-- One-shot positive-Collatz closeout for a lexicographic macro rank. -/
theorem collatz_of_zero_tail_eventual_lex_rank
    {Q : Type}
    (project : State → Q)
    (major minor : Q → Nat)
    (hprogress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          ZeroTailLive (iter step j s) ∧
          (major (project (iter step j s)) < major (project s) ∨
            (major (project (iter step j s)) = major (project s) ∧
             minor (project (iter step j s)) < minor (project s)))) :
    ∀ n, 0 < n → CollatzGood n := by
  exact collatz_of_zero_tail_kernel_empty
    (zero_tail_kernel_empty_of_eventual_lex_rank
      project major minor hprogress)

/-- A strictly increasing precision sequence always outruns any fixed natural
source. This is the abstract natural-bar fact behind the finite-source side of
the closeout: an infinite sequence of source refinements cannot stay forever
below a fixed source value. -/
theorem strict_precision_ge_index
    (precision : Nat → Nat)
    (hstrict : ∀ i, precision i < precision (i + 1)) :
    ∀ i, i ≤ precision i := by
  intro i
  induction i with
  | zero =>
      exact Nat.zero_le _
  | succ i ih =>
      have hs := hstrict i
      omega

theorem strict_precision_eventually_past_source
    (source : Nat)
    (precision : Nat → Nat)
    (hstrict : ∀ i, precision i < precision (i + 1)) :
    ∃ i,
      source < precision i ∧
      source < precision (i + 1) := by
  have hge := strict_precision_ge_index precision hstrict
  refine ⟨source + 1, ?_, ?_⟩
  · have h := hge (source + 1)
    omega
  · have h := hge (source + 2)
    simpa [Nat.add_assoc] using (show source < precision (source + 2) by omega)

/-- Therefore a rule excluding two consecutive post-source precision events
rules out an infinite strictly increasing switch-precision sequence. -/
theorem no_infinite_switch_precision_of_no_two_past_source
    (source : Nat)
    (precision : Nat → Nat)
    (hstrict : ∀ i, precision i < precision (i + 1))
    (hno :
      ∀ i,
        ¬ (source < precision i ∧
           source < precision (i + 1))) :
    False := by
  obtain ⟨i, hi, hi1⟩ :=
    strict_precision_eventually_past_source source precision hstrict
  exact hno i ⟨hi, hi1⟩

/-- Remaining source-precision fuel strictly drops whenever a still-unexhausted
precision is refined. The minor rank may therefore be reset on such a move. -/
def remainingPrecision (source precision : Nat) : Nat :=
  source + 1 - precision

theorem remainingPrecision_strict
    {source p q : Nat}
    (hp : p ≤ source)
    (hpq : p < q) :
    remainingPrecision source q < remainingPrecision source p := by
  unfold remainingPrecision
  omega

#print axioms zero_tail_kernel_empty_of_eventual_lex_rank
#print axioms collatz_of_zero_tail_eventual_lex_rank
#print axioms strict_precision_ge_index
#print axioms strict_precision_eventually_past_source
#print axioms no_infinite_switch_precision_of_no_two_past_source
#print axioms remainingPrecision_strict

end SourceProduct
end CollatzFinal
