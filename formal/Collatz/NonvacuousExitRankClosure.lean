import Collatz.BiadicLexicographicCloseout

namespace CollatzFinal
namespace SourceProduct

/-!
V156 — NONVACUOUS SOURCE-LOCKED EXIT-OR-RANK CLOSEOUT.

Structural audit of V82/V85: their published hprogress type demands
a *later LIVE* state with a strict lexicographic rank decrease from
EVERY ZeroTailLive state. This is stronger than necessary and actually
FALSE for the genuine Collatz map, regardless of rank choice.

Witness: source n=3, actual clock 3, endpoint 4, tail=0.
This is ZeroTailLive (the earlier sources 1 and 2 never reach 4).
The NEXT actual shortcut step is 4 -> 2, an Exit. Every positive
later state is terminal 1 or 2 and therefore NOT Live. j=0 cannot
strictly decrease a rank. Hence the V82 hprogress premise is
provably unrealizable, even though V82's conditional implication was
Lean correct. V85's corresponding later-live macro attempt has
the same nonperiodic last-live-state issue.

The CORRECT nonvacuous universal research obligation is:
  for every ZeroTailLive s, eventually EXIT (terminal, strict
  source-descent, or genuine earlier-source two-clock merge)
  OR reach a later live state with lexicographically smaller
  source-attached rank.

Under a *hypothetical* infinite postfixed Live kernel, the Exit case
is impossible and the rank case contradicts well-foundedness. This
new unconditional logical closeout is proved below. Its universal
exit-or-rank premise remains UNKNOWN; no Collatz QED is claimed.

V155 exact all-source future classes and V134 active proof ledger
remain unchanged.
-/

/-- The REAL shortcut 3 -> 5 -> 8 -> 4, not a 2-adic ghost. -/
theorem v156_source3_clock3_endpoint :
    endpoint (stateAt 3 3) = 4 := by decide

theorem v156_source3_clock3_zero_tail :
    (stateAt 3 3).tail = 0 := by decide

/-- Both smaller positive sources (1 and 2) are confined to
    the already-certified 1 <-> 2 terminal cycle. -/
theorem v156_terminal_orbit_forward
    (p t : Nat) (hp : Terminal p) :
    Terminal (iter shortcut t p) := by
  induction t with
  | zero => simpa [iter] using hp
  | succ t ih =>
      rw [iter_succ_last]
      exact terminal_forward_invariant _ ih

/-- This state is genuinely live, source-attached, and zero-tail,
    yet its actual future reaches terminal at the NEXT step. -/
theorem v156_source3_last_live :
    ZeroTailLive (stateAt 3 3) := by
  constructor
  · constructor
    · exact ⟨3,3,by decide,rfl⟩
    · intro hExit
      rcases hExit with hTerm | hDrop | hMerge
      · have hNo : ¬ Terminal (4 : Nat) := by
          simp [Terminal]
        apply hNo
        simpa [v156_source3_clock3_endpoint] using hTerm
      · have hSrc : (stateAt 3 3).source = 3 := by decide
        have hlt : (4:Nat) < 3 := by
          simpa [hSrc,v156_source3_clock3_endpoint] using hDrop.2
        omega
      · obtain ⟨p,b,hp,hlt,heq⟩ := hMerge
        have hSrc : (stateAt 3 3).source = 3 := by decide
        have hsmall : p < 3 := by
          simpa [hSrc] using hlt
        have hpt : Terminal p := by
          show p=1 ∨ p=2
          omega
        have hT := v156_terminal_orbit_forward p b hpt
        have hEq : iter shortcut b p = 4 := by
          simpa [v156_source3_clock3_endpoint] using heq
        have hT4 : Terminal 4 := by
          simpa [hEq] using hT
        have hNo : ¬ Terminal (4 : Nat) := by
          simp [Terminal]
        exact hNo hT4
  · exact v156_source3_clock3_zero_tail

theorem v156_source3_next_is_real_exit :
    Exit (iter step 1 (stateAt 3 3)) := by
  left
  right
  decide

theorem v156_source3_future_terminal (j : Nat) :
    Terminal (endpoint (iter step (j+1) (stateAt 3 3))) := by
  have h2 : Terminal (iter shortcut j 2) :=
    v156_terminal_orbit_forward 2 j (Or.inr rfl)
  have heq :
      endpoint (iter step (j+1) (stateAt 3 3)) =
        iter shortcut j 2 := by
    calc
      endpoint (iter step (j+1) (stateAt 3 3)) =
          iter shortcut (j+1) (endpoint (stateAt 3 3)) :=
        endpoint_iter_step (j+1) _
      _ = iter shortcut j 2 := by
        rw [v156_source3_clock3_endpoint]
        change iter shortcut j (shortcut 4) = iter shortcut j 2
        have h4 : shortcut 4 = 2 := by decide
        rw [h4]
  simpa [heq] using h2

theorem v156_source3_no_later_zero_tail_live (j : Nat) :
    ¬ ZeroTailLive (iter step (j+1) (stateAt 3 3)) := by
  intro hLive
  have hTerm := v156_source3_future_terminal j
  exact hLive.1.2 (Or.inl hTerm)

/-- The V82-style universal "a strictly lower later LIVE rank
    from EVERY live state" is mathematically impossible, not merely
    computationally hard. For n=3 the last live state must EXIT.

    No choice of quotient/projected rank can repair this quantifier:
    the progress interface itself has to admit exit. -/
theorem v156_old_universal_later_live_rank_is_impossible
    {Q : Type} (project : State → Q)
    (major minor : Q → Nat) :
    ¬ (∀ s, ZeroTailLive s →
      ∃ j,
        ZeroTailLive (iter step j s) ∧
        (major (project (iter step j s)) < major (project s) ∨
          (major (project (iter step j s)) = major (project s) ∧
           minor (project (iter step j s)) < minor (project s)))) := by
  intro hProgress
  obtain ⟨j,hjLive,hjRank⟩ :=
    hProgress (stateAt 3 3) v156_source3_last_live
  cases j with
  | zero =>
      simp only [iter] at hjRank
      rcases hjRank with hMajor | hMinor
      · exact (Nat.lt_irrefl _) hMajor
      · exact (Nat.lt_irrefl _) hMinor.2
  | succ j =>
      exact v156_source3_no_later_zero_tail_live j hjLive

/-- Corrected, NONVACUOUS global finish-line interface:
    every source-attached live state eventually either exits
    or exhibits a certified lexicographic rank decrease while live.

    On a hypothetical infinite live kernel S, no EXIT can occur.
    The remaining rank drops contradict well-foundedness. -/
theorem v156_zero_tail_kernel_empty_of_exit_or_lex_rank
    {Q : Type}
    (project : State → Q)
    (major minor : Q → Nat)
    (hProgress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          Exit (iter step j s) ∨
          (ZeroTailLive (iter step j s) ∧
            (major (project (iter step j s)) < major (project s) ∨
              (major (project (iter step j s)) = major (project s) ∧
               minor (project (iter step j s)) < minor (project s))))) :
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
            obtain ⟨j,hcase⟩ := hProgress s hzero
            have hSj : S (iter step j s) :=
              postfixed_iter_mem S hPost j s hs
            rcases hcase with hExit | ⟨_hjlive,hdec⟩
            · exact (hsub _ hSj).1.2 hExit
            · rcases hdec with hMaj | hMin
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

theorem v156_collatz_of_exit_or_lex_rank
    {Q : Type}
    (project : State → Q)
    (major minor : Q → Nat)
    (hProgress :
      ∀ s, ZeroTailLive s →
        ∃ j,
          Exit (iter step j s) ∨
          (ZeroTailLive (iter step j s) ∧
            (major (project (iter step j s)) < major (project s) ∨
              (major (project (iter step j s)) = major (project s) ∧
               minor (project (iter step j s)) < minor (project s))))) :
    ∀ n : Nat, 0 < n → CollatzGood n := by
  exact collatz_of_zero_tail_kernel_empty
    (v156_zero_tail_kernel_empty_of_exit_or_lex_rank
      project major minor hProgress)

#print axioms v156_source3_clock3_endpoint
#print axioms v156_source3_last_live
#print axioms v156_source3_next_is_real_exit
#print axioms v156_source3_future_terminal
#print axioms v156_source3_no_later_zero_tail_live
#print axioms v156_old_universal_later_live_rank_is_impossible
#print axioms v156_zero_tail_kernel_empty_of_exit_or_lex_rank
#print axioms v156_collatz_of_exit_or_lex_rank

end SourceProduct
end CollatzFinal
