# Future Consequence Prospective Transfer V1 Protocol

## Question

Does the exact frozen continuation-major mechanism from C4 reduce fully charged acquisition cost on a previously unseen carrier after counterbalancing operation order, or was the C4 gain an enumeration-order effect?

## Freeze and novelty

- Frozen source mechanism commit: `8809c71cd75b49326f921595dfbfe05a310a959e`.
- New carrier: immutable token traces rather than grids.
- Four typed actions append distinct tokens. Exact executable equality is the verifier.
- Targets are all 24 length-four permutations using each action exactly once.
- Every target is evaluated under all 24 permutations of the candidate-operation order: 576 target/order trials.
- Maximum depth remains four. Every unique verifier call, including continuation probes, is charged.
- The controller receives examples and available operations, never the generating target program.
- No external model is used.

The exhaustive target and ordering design was fixed before evaluation and prevents a favorable lexical order from determining the aggregate result.

## Conditions

- `COLD_IMMEDIATE`: depth-first prefix-major enumeration.
- `Q_WARM`: unchanged continuation-major enumeration from the C4 repair.
- `Q_ABLATION`: remove continuation-major ordering and restore cold.
- `SHAM`: matched inert profile state with cold ordering.
- `ANSWER_MEMORY`: earlier result provenance in a non-causal channel with cold ordering.

## Primary metric and gates

Primary metric is aggregate verifier calls across all 576 trials.

Strong prospective transfer requires all of:

1. Correctness on every trial and condition.
2. `Q_WARM` aggregate charged cost below 80 percent of cold.
3. `Q_WARM` wins on more trials than it loses.
4. The gain persists in every target-position stratum.
5. Ablation, sham, and answer-memory equal cold.
6. The exact source controller file hash matches the frozen source commit's recorded controller.

If correctness holds but the counterbalanced aggregate gain vanishes, classify the C4 advantage as ordering-sensitive rather than transferable. This experiment cannot establish generator genesis because all actions remain supplied.
