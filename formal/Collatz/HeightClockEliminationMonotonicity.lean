import Collatz.DominantClockSourceGraph

namespace CollatzFinal
namespace SourceProduct

/-!
V174 — SOURCE-HEIGHT/CLOCK CAUSAL ABLATION IN THE CANONICAL
ALL-ORIGINAL-SOURCE TWO-CLOCK GRAPH.

We must distinguish TWO independent elimination operations:
(1) keep source-height cutoff fixed, enlarge real clock H;
(2) keep real clock H fixed, admit additional original sources.

Both operations are mathematically MONOTONE for actual finite
source-coalescence paths and for seeded convergence certificates:
a previously genuine terminal certificate is never invalidated.

This property is important because finite declines in unseeded
components were previously confounded by changing H(k)=8k and
X(k)=2^k at the same time. An improved audit tests these
dimensions separately, compares their exact effect on specific
original sources, and retains the synthetic G7/S5 controls.

These monotonicities DO NOT imply that every unseeded component
eventually closes or a uniform all-scale no-giant law. Global
Collatz UNKNOWN — NO QED.
-/

/-- Both clock and source-height windows may grow without losing
    ANY existing genuinely checked original-source meeting path. -/
theorem v174_canonical_path_monotone
    (X H X' H' : Nat)
    (hHeight : X<=X') (hClock : H<=H')
    {n m : Nat} (hPath : V170FullClockPath X H n m) :
    V170FullClockPath X' H' n m := by
  induction hPath with
  | identity n =>
      exact .identity n
  | meeting hn hm hnX hmX hi hj hEndpoint =>
      exact .meeting hn hm
        (Nat.lt_of_lt_of_le hnX hHeight)
        (Nat.lt_of_lt_of_le hmX hHeight)
        (Nat.le_trans hi hClock)
        (Nat.le_trans hj hClock)
        hEndpoint
  | reverse h ih =>
      exact .reverse ih
  | compose ha hb iha ihb =>
      exact .compose iha ihb

/-- Every real terminal seed retained at a smaller height and
    clock remains a fully warranted terminal seed after either
    kind of finite search extension. -/
theorem v174_terminal_seed_monotone
    (X H X' H' n : Nat)
    (hHeight : X<=X') (hClock : H<=H')
    (hSeed : V170HasTerminalSeed X H n) :
    V170HasTerminalSeed X' H' n := by
  obtain ⟨p,hp,hpX,hPath,j,hj,hTerm⟩ := hSeed
  exact ⟨p,hp,Nat.lt_of_lt_of_le hpX hHeight,
    v174_canonical_path_monotone X H X' H'
      hHeight hClock hPath,
    j,Nat.le_trans hj hClock,hTerm⟩

/-- Contrapositive: a presently unseeded original source
    cannot have been seeded by any earlier, strictly smaller
    complete source-and-clock search window. -/
theorem v174_unseeded_only_persists_backward
    (X H X' H' n : Nat)
    (hHeight : X<=X') (hClock : H<=H')
    (hUnseeded : ¬ V170HasTerminalSeed X' H' n) :
    ¬ V170HasTerminalSeed X H n := by
  intro hSeed
  exact hUnseeded
    (v174_terminal_seed_monotone X H X' H' n
      hHeight hClock hSeed)

/-- Any hypothetical true BAD positive source is excluded from
    terminal-seeded status at ALL search heights/clocks, not
    just a chosen finite budget. This is an epistemic guard,
    NOT an existence proof for a bad source. -/
theorem v174_bad_source_excluded_at_every_finite_budget
    (n X H : Nat) (hBad : ¬ CollatzGood n) :
    ¬ V170HasTerminalSeed X H n := by
  intro hSeed
  exact hBad (v170_terminal_seeded_class_is_good X H n hSeed)

#print axioms v174_canonical_path_monotone
#print axioms v174_terminal_seed_monotone
#print axioms v174_unseeded_only_persists_backward
#print axioms v174_bad_source_excluded_at_every_finite_budget

end SourceProduct
end CollatzFinal
