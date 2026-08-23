# Method-on-Method V1 — prospective recursive-method test

Question: does allowing the research method itself to revise from verified methodological residuals improve future research under matched information and resource budgets?

This is the first protocol where the *method* is the experimental subject.

## Frozen arms

### FIXED
Uses UVRM v1 throughout all episodes. It may reason normally inside the method but may not persist method revisions.

### SELF_REVISING
Starts from the same UVRM v1. A method revision may be proposed only from an explicit methodological residual and may be persisted only after its own precommitted causal/prospective gate.

### RAW_HISTORY
Receives the same raw prior episode evidence, including all object-level results and descriptions of past method revisions, but receives no compiled revised policy. It may reconstruct an equivalent policy under the same resource budget. This is the strongest memory/reconstruction rival.

### SHAM_REVISION
Receives the same number and approximate complexity of permitted method edits as SELF_REVISING, but revisions are shuffled across residuals or selected without the residual-specific predicted causal relation. This controls for generic extra flexibility.

## Constitutional invariants

All arms share and may not revise during this protocol:

- external verifier/protected outcome authority;
- evidence monotonicity;
- no protected outcome leakage backward;
- apparatus/objective validity gates;
- not-found != unreachable distinction;
- success requires causal attack before retention;
- matched budgets and preserved negative/null/infrastructure results.

The revisable object is the policy layer: mode-switch thresholds, generator families/slots, residual taxonomy, experiment ranking, equivalence probes, import handling, retention criteria beyond constitutional minima, and other operational rules.

## Episode protocol

For each untouched research episode t:

1. Freeze the object-level goal, verifier, resource budget and protected outcomes.
2. Give each arm the same admissible starting evidence.
3. Record its initial research state and chosen lifecycle/mode.
4. Let the arm choose/generate experiments within the common budget.
5. Preserve every result, including nulls and infrastructure failures.
6. Score object-level research yield.
7. Record any methodological residual `rho_M`:
   - missed separator;
   - premature/late reframe;
   - unnecessary experiment cost;
   - search-basis error;
   - bad equivalence/probe decision;
   - wrong retention;
   - failed transfer;
   - systematic human correction;
   - other predeclared category.
8. SELF_REVISING may propose `Delta M`, but the proposal is not yet admitted.
9. Freeze what `Delta M` predicts on future protected episodes or a protected held-out continuation.
10. Admit `Delta M` only after its declared separator is observed and relevant sham/raw-history rivals are not sufficient explanations.

## Primary outcome

Do not collapse everything into a single arbitrary scalar. Compare a predeclared research-yield vector:

- verified target progress;
- number of decision-changing experiments;
- live rival classes eliminated;
- residual sharpening;
- invalid branches avoided;
- model calls/tokens;
- verifier/solver calls;
- wall/CPU/RSS where applicable;
- scaffold added/removed;
- protected success;
- attack survival;
- transfer survival;
- raw-history reconstruction cost;
- surprise/model-miss rate.

The primary directional hypothesis is that SELF_REVISING should Pareto-improve or clearly dominate FIXED on future untouched episodes without merely consuming more resources.

## Claim ladder

- `SELF_REVISING ~= FIXED`: no evidence that method revision helps.
- `SELF_REVISING > FIXED`, but `RAW_HISTORY ~= SELF_REVISING`: history/reconstruction is sufficient; do not claim compiled method development.
- `SELF_REVISING > FIXED` and `> RAW_HISTORY`, but `SHAM_REVISION ~= SELF_REVISING`: generic flexibility may explain the result.
- `SELF_REVISING > FIXED, RAW_HISTORY, SHAM_REVISION`: prospective evidence that residual-specific method revision contributes causally.
- Stronger recursive claim requires a chain where a previously admitted method revision enables discovery/admission of a later useful method revision that FIXED and matched RAW_HISTORY cannot recover within budget.

## Recursive gate

Target a chain:

`M0 --rhoM0--> M1 --rhoM1--> M2 --future episode--> superior verified research move`

Required ablations:

- SELF_REVISING with M1 removed;
- SELF_REVISING with M2 removed;
- RAW_HISTORY reconstruction at each stage;
- SHAM M1 and SHAM M2 of matched complexity.

A genuine recursive-method result requires causal dependence, not merely chronological accumulation.

## Anti-self-validation rule

The method may propose changes to itself, but it does not get to decide that they worked. Protected future outcomes and frozen external/object-level verifiers do.

If the method changes its own scoring rule, verifier, protected set, or constitutional constraints after seeing results, the corresponding evidence is invalid for method-revision claims.

## Deployment intent

UVRM is meant to be usable across mathematics, Lean/kernel engineering, solver competitions, ML/benchmark work, scientific experiments, software research, and other Metalogic/MathGraph programmes. Project-specific protocols may specialize the search slots, verifier, budget and domain residual classes, while preserving the constitutional core.
