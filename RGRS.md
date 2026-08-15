# Residual-Guided Representation Search (RGRS)

Purpose: force the Lean kernel optimization programme to respond to failure by changing representation only when evidence justifies it, then retain a change only when a small causal test and an external verifier support it.

## Residual record

Every failed or suboptimal experiment terminates in one primary residual:

- R1 Search — representation is adequate; search is insufficient.
- R2 Cost — semantics pass but CPU/RSS/wall gate fails.
- R3 Redundancy — equivalent work is repeated; canonicalize/quotient.
- R4 Observability — work cannot affect verified output; make evaluation selective/lazy.
- R5 Applicability — mechanism helps only some regimes; learn/certify activation predicate.
- R6 Representation — needed distinction/object is absent from the current language/IR.
- R7 Composition — lawful combination of known mechanisms closes the gap.
- R8 Access — useful structure exists but is expensive to recover; add index/persistent structure.
- R9 Soundness — semantic violation; reject immediately.
- R10 Infrastructure — runner/build/network/provisioning failure; repair experiment, no semantic conclusion.
- R11 Boundary — gain depends on arbitrary granularity/language boundary; test alternate reasonable boundary.
- R12 Displacement — complexity moved rather than reduced; measure total cost.

Canonical record:

```text
rho = (class, location, evidence, scope, confidence)
```

No vague labels such as "performance issue" or "didn't work".

## When representation change is allowed

Representation change is allowed only after at least one predeclared trigger:

1. Repeated residual: same residual survives two materially different interventions in the current representation.
2. Conditional regime: incompatible workloads prefer incompatible mechanisms; expose the separator rather than globally choosing one.
3. Quotient: distinctions are repeatedly computed but verifier-equivalent; collapse them.
4. Non-observation: values cannot affect a verified observable; do not force them eagerly.
5. Missing object: current language cannot state the distinction explaining the residual.
6. Composition before invention: test lawful composition of existing mechanisms first.
7. Total cost: construction + activation + verification + runtime + memory must improve overall.
8. Boundary robustness: claimed novelty survives at least one alternate reasonable granularity.

## Smallest deciding test

Every representation proposal must answer one separator question:

> What is the smallest experiment whose outcomes distinguish the new-representation hypothesis from the strongest old-representation explanation?

Required structure:

- one intervention;
- at least two opposing discriminators;
- frozen baseline/runner/compiler/hardware/corpus/verifier;
- causal ablation preserving everything else;
- precommitted decision table.

## Outcome table

- Clean mechanism win -> escalate to external gate.
- No effect -> reject mechanism; retain negative law.
- Conditional win -> R5 Applicability; identify separator, stop global tuning.
- Fast but semantically invalid -> R9 Soundness; reject.
- Faster local core but worse total cost -> R12 Displacement; reject unless displaced cost is independently eliminated.
- Infrastructure failure -> R10; repair and rerun without updating scientific belief.

## Admission gate

A retained architectural change requires all four:

```text
G = semantic AND causal AND resource AND reproducible
```

Semantic: independent checker/corpus shows no false accept/reject in frozen scope.

Causal: gain disappears or materially weakens under ablation.

Resource: predeclared metric improves; no metric switching.

Reproducible: same commit/config/corpus/runner procedure reproduces it.

State transition:

```text
PROPOSED -> SEPARATED -> VERIFIED -> ADMITTED
```

Otherwise retain as REJECTED or OBSTRUCTED.

## Operating loop

1. Run strongest current representation.
2. Extract and classify residual.
3. Decide search-level versus representation-level.
4. Generate the smallest distinction-changing representation.
5. State the predicted separator.
6. Build the smallest deciding test.
7. Run frozen baseline + intervention + ablation.
8. Send outcome through external verifier.
9. Admit, reject, or refine applicability.
10. Write result to the experiment ledger and negative-law set.

Governing rule:

> Never search harder inside a representation after the residual says the missing information lives outside it.
