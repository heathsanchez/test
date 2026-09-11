# Verified Representation Genesis V1 — Frozen Protocol

## Question

Can a complete negative over a complete stateless meta-language force and license construction of the least history-sensitive representation, rather than another parameterization inside the old form?

## Frozen finite domain

- Inputs and outputs: Boolean.
- Old meta-language: all four stateless unary Boolean maps `Bool -> Bool`, exhaustively enumerated.
- Trigger obligation: on every two-symbol history `(previous,current)`, output `previous` at the second step.
- Residual: histories `(0,0)` and `(1,0)` have the same current observation but require different outcomes.
- Generic genesis rule: create only the equivalence classes forced by a certified separating history coordinate. No named state machine or delay candidate is supplied.
- Constructed representation: quotient histories by their last input, yielding the forced two-state coordinate; synthesize update `state' = input` and readout `output = state` from the complete residual table.
- Prospective reuse target, hidden from construction: on all length-three input sequences, report at each post-initial step whether current input differs from the preceding input.
- Controls: remove the state coordinate; replace it with a matched one-bit inert coordinate; expose trigger answer rows without live state.

## Cost and gates

Every old-candidate/history evaluation, construction-row verification, preservation check, trigger/reuse evaluation, and ablation/control evaluation is charged. A pass requires: exhaustive old-language completeness; certified negative; a witnessed observational collision; proof that at least two states are necessary; construction of exactly two residual-induced classes; external verification; proof-carrying admission; preservation; trigger and prospective-reuse success; and failure of state ablation, inert-state sham, and answer-memory controls.

## Claim boundary

A pass earns **BOUNDED, EXHAUSTIVE, CAUSAL REPRESENTATION GENESIS**. It does not establish unrestricted grammar invention: the generic operation “form a finite quotient from a certified separator” remains supplied.
