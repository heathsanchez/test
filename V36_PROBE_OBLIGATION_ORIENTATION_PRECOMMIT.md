# V36 Probe Obligation Orientation — Frozen Precommit

## Residual

V35 found two stable minimum transformer classes: order-4 FORWARD and order-4 REVERSE. Inspection of the runtime showed that both target-specific continuations (`ACCEPT_COUNTERMODEL_WITNESS` and `ADVANCE_PROOF_SEARCH_FRONTIER`) were licensed from the probe Boolean/order alone, without checking whether the model query was oriented in the target implication direction.

For an implication-style SAIR episode, a FORWARD query searches for a model satisfying the premise and falsifying the target. A REVERSE query searches for the converse pattern. The latter may be observation-sound but cannot by itself certify a countermodel to the original target or exhaustion of target-directed countermodels.

Residual: `TARGET_SPECIFIC_CONTINUATION_OBLIGATION_UNTYPED_BY_PROBE_ORIENTATION`.

## Frozen hypothesis

Once target orientation is made an explicit certified obligation of target-specific continuations, reverse probes may remain lawful observations but must not directly license either target countermodel acceptance or target proof-frontier advancement. Recomputing the repaired V34 raw carrier under this typed semantics should reveal whether V35's reverse intervention class was a real developmental alternative or an artifact of under-typed action obligations.

## Frozen protocol

1. Use the official SAIR development corpus and remove protected labels before routing/synthesis.
2. Reconstruct a natural V30/V34-style successor under the corrected planning/execution semantics.
3. Populate exact bounded-model outcomes for every atomic probe reachable from the repaired raw one-literal carrier on that successor, with independent witness recheck.
4. Add the obligation `TARGET_ORIENTED` to both `ACCEPT_COUNTERMODEL_WITNESS` and `ADVANCE_PROOF_SEARCH_FRONTIER`.
5. Require `TARGET_ORIENTED=true` iff the active atomic model query is FORWARD.
6. Demonstrate that REVERSE probes remain executable, verifier-sound observations but cannot satisfy either target-specific continuation's lawful obligations.
7. Recompute the exhaustive repaired raw-transformer carrier and all minimum-cost resolving records.
8. Do not add a new grammar primitive, target order, semantic SUCC operator, protected label, or preference rule.

## Gates

- official natural SAIR corpus used answer-blind;
- repaired raw carrier reconstructed;
- all reachable atomic verifier outcomes available with zero bad witnesses and zero unknowns on the evidentiary successor;
- reverse probe observation remains verified/sound;
- reverse probe cannot lawfully license countermodel acceptance;
- reverse probe cannot lawfully license proof-frontier advancement;
- every minimum resolving transformer is target-oriented FORWARD;
- after quotienting duplicate derivations by concrete probe, there is a unique minimum resolving concrete probe;
- no protected answer enters routing, synthesis, or obligation checks;
- `V36_PROBE_OBLIGATION_ORIENTATION_GATE=true` iff all gates pass.

## Claim boundary

A pass establishes only that the V35 forward/reverse ambiguity was caused by missing target-orientation typing in the declared finite SAIR continuation semantics. It does not establish general intervention selection, unrestricted probe identity, or grammar invention.