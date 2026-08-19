# V25 — Lean Developmental Reachability precommit

Date frozen: 2026-08-20 NZST

## Sharp question

Can a verifier-derived distinction learned before protected Mathlib evaluation causally enlarge which Lean checking episodes are reachable under a frozen one-call continuation budget?

V25 is a bridge experiment, not yet a claim of arbitrary proof-constructor invention. It tests whether installing the already-frozen V21 distinction changes the reachable continuation set on the independently predeclared V24 Mathlib gold corpus.

## Frozen lineage

- Base branch: `agent/developmental-distinction-mathlib-gold-v24`
- V24 head at freeze: `10759bf3af4c96878cf56bdb84dfb8b535ce678e`
- V24 corpus: 16 predeclared Mathlib modules, selected before trace-feature inspection.
- Frozen feature: `final_depth_step`
- Frozen V21 rule: `NONE -> INFER_APP`, `U -> PROJECTION`, `F -> IOTA`.
- Candidate order for the cold arm: `INFER_APP, PROJECTION, IOTA`.

No feature invention, rule fitting, threshold changes, corpus rescue, target reselection, or post-hoc budget change is allowed in V25.

## State and reachability

Let `A0` be the cold continuation policy with no developmental distinction installed. Under the frozen one-call budget it always tries the first candidate, `INFER_APP`.

Let `O` be the frozen quotient/distinction mapping from `final_depth_step` to the predicted continuation family.

Let `A1 = A0 + O`. Under the same one-call budget, A1 tries the family selected by O.

An episode is `reachable` iff the single permitted verifier continuation returns `accept`.

The protected target set is exactly the V24 independently predeclared Mathlib gold episodes produced by the unchanged V23/V24 evaluator. V25 does not inspect target outcomes before freezing the policy or budget.

## Arms

1. **COLD A0** — one verifier call; fixed first candidate `INFER_APP`.
2. **WARM A1** — one verifier call; candidate chosen by frozen O.
3. **ABLATION A1-O** — remove O and restore the exact cold policy.
4. **RELOAD** — serialize O to JSON, reload it in a fresh object, and apply the same one-call policy.

## Gates

- **G0 V24 prerequisite**: V24 external Mathlib evaluation completes with zero semantic mismatches and its frozen quotient gate passes.
- **G1 Cold residual**: at least one protected episode is unreachable under A0.
- **G2 Warm strict expansion**: `Reach(A1)` is a strict superset of `Reach(A0)`.
- **G3 Exact causal delta**: every newly reachable episode is attributable to a changed first continuation selected by O; no episode may be counted from extra verifier calls.
- **G4 Ablation**: `Reach(A1-O) = Reach(A0)` exactly.
- **G5 Persistence**: serialize/reload O and require `Reach(reload(O)) = Reach(A1)` exactly.
- **G6 Safety**: all counted successes are actual `accept` verdicts already produced by the checker/verifier path; advisory labels never count as acceptance.
- **G7 No regression**: `Reach(A0) subseteq Reach(A1)`.

## Primary measurement

Write the exact sets:

`DeltaC(O) = Reach(A1) \ Reach(A0)`

and report cold/warm/ablation/reload reachability counts and episode identifiers.

## Interpretation boundary

A PASS establishes only this:

> On the protected V24 Mathlib checker episodes and a frozen one-call continuation budget, installing a previously learned verifier-derived distinction causally enlarges the set of episodes reachable by the continuation policy; ablation removes exactly that gain and serialization/reload preserves it.

It does **not** establish that Lean's logical language changed, that a new theorem became provable in Lean, that an arbitrary operator was invented, or that the MathGraph kernel itself learned autonomously. Those require a later proof-constructor acquisition experiment.

## Verdict

`PASS_V25_LEAN_DEVELOPMENTAL_REACHABILITY` iff G0–G7 all pass.

Otherwise emit a gate-specific negative result; do not rescue or redefine reachability.
