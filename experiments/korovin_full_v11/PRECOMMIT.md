# Korovin V11 — Standalone Usefulness of Invented Theory

## Question

After a residual-generated mathematical theory has been verified, can it become a standalone reusable capability for a separate downstream solver after access to the original semantic oracle is removed?

This is a stronger criterion than recovery/completeness. It tests whether the invented object and laws support new computations outside the discovery horizon.

## Frozen source worlds

Use the V10 public root `KOROVIN_V10_PUBLIC_COMPLETION_TRANSFER_2026-08-22` and exactly the residual-bearing indices discovered under that already-frozen all-draws protocol: 4, 5, and 11.

No V10 world is replaced.

## Artifact compilation

For each source world:

1. Reproduce the unchanged V5 baseline theory.
2. Apply finite residual completion and fixed-point global pruning.
3. Independently certify every canonical state-generator edge from the final equations.
4. Compile a standalone artifact containing only:
   - the alphabet;
   - canonical state representatives;
   - the certified finite transition table;
   - the human-readable retained equations;
   - proof/certificate provenance for each transition.
5. The downstream consumer receives no generator transformation tables and no semantic execution oracle.

The verifier may use the hidden world semantics only before artifact sealing and afterward for protected scoring. The downstream consumer may not call it.

## Protected downstream tasks

Root phrase: `KOROVIN_V11_STANDALONE_USE_2026-08-22`.

For each of the three worlds generate 1,000 deterministic protected token programs after the artifact is sealed:

- 250 lengths in [20, 49];
- 250 lengths in [50, 99];
- 250 lengths in [100, 249];
- 250 lengths in [250, 1000].

The standalone consumer must compute the final canonical state using only the compiled transition table.

An external scorer then compares the consumer state with the hidden original semantic oracle.

## Counterfactual / causality

Compile the pre-residual V5 theory under the same contract. Because it has uncertified canonical edges on these worlds, it must fail the standalone-complete artifact gate.

For every retained residual-generated law, remove it from the final theory and rerun compilation. The complete certified artifact must cease to exist or lose at least one certified transition.

## Gates

- G0: all three frozen V10 residual-bearing worlds reproduce.
- G1: each final theory compiles to a fully certified standalone artifact.
- G2: the downstream consumer makes zero oracle calls.
- G3: 3,000/3,000 protected long-horizon programs are classified correctly.
- G4: every length stratum is perfect independently.
- G5: no pre-residual V5 theory can compile a fully certified artifact on these three worlds.
- G6: removing every retained residual-generated law independently breaks full certification.
- G7: all retained equations are emitted in human-readable finite presentation form.
- G8: maximum protected program length is at least 1,000, far outside the discovery/candidate horizons.

## Claim boundary

A pass establishes standalone machine usability of the invented finite mathematical theory: once verified and compiled, another solver can use it without access to the original world semantics to answer new long-horizon queries exactly.

It is not direct evidence that human mathematicians find the objects useful; a human-use study would be a separate experiment.