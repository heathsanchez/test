# V33 — Corrected raw-transformer basis test

## Residual

V32 reported `RAW_TRANSFORMER_CARRIER_INSUFFICIENT` with a raw one-literal transformer carrier of size 2. That run used the pre-V31 commitment planner, which did not separate hypothetical probe outcomes used for policy planning from verifier-observed outcomes that actually license downstream actions.

## Frozen question

Under the corrected planning/execution semantics, does the *same frozen V32 raw transformer carrier* contain a resolving singleton? If not, do its existing candidates jointly form a minimum resolving probe basis?

No new raw edit primitive, semantic operator, target order, or protected SAIR label is supplied.

## Protocol

1. Reconstruct the same natural V32 successor residual from official SAIR `normal+hard1+hard2` rows with answers removed.
2. Require the old V28 probe carrier to remain exhausted on that successor.
3. Enumerate exactly the same generic one-literal raw rewrite carrier over literals `{1,2,3,4}`.
4. Evaluate every singleton under the corrected counterfactual planning semantics.
5. If no singleton resolves, exhaustively evaluate every pair from that same carrier.
6. Choose the minimum cardinality, then minimum total-cost resolving basis; report underdetermination if behaviorally distinct minima survive.
7. Execute the resulting policy through actual verifier contact on a natural world; actions become licensed only after observed probe outcomes.
8. Require at least one natural trajectory to use two probe executions before reaching a common lawful continuation if the minimum basis has size 2.
9. Ablate each member of a size-2 minimum basis separately; each deletion must restore the epistemic obstruction.
10. Independently recheck all encountered SAT witnesses and reject any routing query returning `unknown`.

## Gates

- `corrected_planner_used`
- `external_sair_rows_used_without_answers`
- `old_probe_completecover_obstruction`
- `same_v32_raw_carrier_reused`
- `carrier_exhaustive`
- `minimum_basis_found`
- `minimum_basis_cardinality_certified`
- `actual_verifier_execution_reaches_commitment`
- `two_step_trajectory_observed_if_basis_size_two`
- `each_basis_member_load_bearing`
- `all_witnesses_rechecked_no_unknowns`
- `no_protected_answer_routing`
- umbrella: `V33_CORRECTED_RAW_TRANSFORMER_BASIS_GATE`

## Interpretation

A size-1 pass would show the V32 negative was an artifact of the old planner semantics. A size-2 pass would show a different residual: the primitive raw transformer carrier was sufficient, but epistemic language development sometimes requires synthesizing a *basis/set* of new probes rather than a single extension. A failure of all subsets would preserve the original carrier-insufficiency diagnosis and license broadening the raw transformation language in the next experiment.
