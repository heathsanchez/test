# V34 — AST / Runtime-Metadata Separation Control

## Frozen question

V33 showed that the corrected commitment planner does not rescue the V32 raw-transformer result: neither of the two materialized raw rewrites, nor their pair, restored commitment coherence. Inspection then exposed a representation error in the V32 carrier itself: probe execution metadata (`cost`) was treated both as an editable integer AST field and as part of structural equality during candidate materialization.

V34 asks whether the original V32 residual-constrained raw-transformer claim succeeds once **probe syntax is separated from runtime metadata**, without adding any new semantic operator or structural edit primitive.

## Frozen repair

The raw transformer language remains exactly one generic integer-literal replacement over probe syntax. The only representation repair is:

- `ast`: external program identifier/string, not editable syntax;
- `cost`: runtime/planning metadata, not editable syntax and not part of structural materialization;
- `kind`, `order`, `direction`: executable probe syntax.

No `SUCC`, `NUMERIC_LITERAL_SHIFT`, increment/decrement operator, target order, protected TRUE/FALSE label, or new edit combinator is supplied.

## Required controls

1. Corrected hypothetical-planning vs observed-entitlement semantics from V31 remain frozen.
2. The natural V30/V31 successor residual must still route to `DEVELOP_PROBES` under the old probe language.
3. Raw carrier enumeration must exclude `cost` from editable paths and materialization equality.
4. The resulting finite one-edit carrier must be exhaustively searched.
5. Any winning transformer must be minimum-cost in that carrier.
6. The generated probe must be absent from the old probe language, executed by the exact verifier, and change the commitment geometry.
7. The post-probe lawful continuation must be recomputed by the generic runtime.
8. The transformer may be typed/retained only after verified execution.
9. Removing it must restore the obstruction.
10. A frozen retained transformer must transfer to a distinct natural successor residual whose old carrier is exhausted.
11. All exact finite-model witnesses must recheck; no Z3 unknowns are permitted.

## Decision

- PASS: the V32 causal chain succeeds after syntax/metadata separation. Then V32's previous red is classified as a representation/infrastructure failure of the carrier, not evidence that one-literal raw transformation is insufficient.
- FAIL with a correctly populated carrier: one-literal raw transformation is genuinely inadequate and grammar development is licensed.

The umbrella gate is `V34_AST_METADATA_SEPARATION_GATE`.
