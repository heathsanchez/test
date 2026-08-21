# V27 — SAIR Commitment Router Natural Test

Frozen after V26 commitment-router mathematics passed all 14 gates on commit `f78e61a7f33e36c792adbc3bb42e51e66b7b6ae0` (PR #55 / Actions run 32506643454).

## Scientific question

On real SAIR Stage-2 equations, can a cheap verifier observation regime create action-incoherent cells, and can an exact finite candidate probe carrier restore common lawful commitment at minimum verifier cost under the frozen router mathematics?

This is a mechanistic natural-corpus test, not a new clean leaderboard/generalization estimate. `hard3` has already participated in the V24/V25 research loop and is reported only as a secondary transfer audit.

## Frozen setup

- External source: official public SAIR Stage-2 repository.
- Development corpus: `normal + hard1 + hard2`.
- Secondary transfer audit: `hard3`.
- Lawful commitments: `PROOF` for public TRUE rows, `COUNTERMODEL` for public FALSE rows. Labels are used to define the audit action-incidence relation, not to construct verifier probe outcomes.
- Cheap observational cell key: the six exact Fin-2 verifier ports `v0..v5` from frozen V24. No syntax ports are included in the cell key.
- Candidate probe carrier is generated without action labels:
  - `ModelSearch(2, forward)` and `ModelSearch(2, reverse)` as cheap redundant/nonseparating controls, cost 1;
  - `ModelSearch(3, forward)` and `ModelSearch(3, reverse)` as higher-resolution exact probes, cost 3.
- Order-3 SAT witnesses must be independently re-evaluated exactly; unknown Z3 results are reported and cannot count as verified separators.
- Probe optimization uses the frozen V26 commitment objective, not entropy or generic label accuracy.

For a cheap observational cell E, define `A(E)` as the intersection of row-level lawful commitment sets. A mixed TRUE/FALSE cell is commitment-incoherent. The exhaustive router computes the minimum-cost adaptive pure-probe tree whose every reachable leaf has nonempty `A(leaf)`. If no such tree exists in the declared carrier, `J(E)=infinity` and the result is a probe-language obstruction, not a forced action.

## Gates

1. `v26_router_math_frozen=true`.
2. `external_sair_rows_used=true`.
3. `cheap_fin2_cells_include_epistemic_obstruction=true`: at least one development cell is individually viable row-by-row but has no common lawful commitment.
4. `probe_outcomes_answer_blind=true`.
5. `all_order3_sat_witnesses_rechecked=true`.
6. `router_search_exhaustive_over_declared_probe_carrier=true`.
7. `at_least_one_natural_cell_has_finite_positive_J=true`.
8. `selected_probe_tree_restores_commitment_coherence=true` for every cell counted as resolved.
9. `probe_ablation_restores_incoherence=true` for at least one resolved natural cell.
10. `cheap_redundant_probe_not_preferred_when_nonseparating=true`.
11. `within_split_shuffle_control=true`: order-3 outcomes are shuffled separately inside development and hard3, never across the boundary.
12. Secondary transfer metrics report hard3 coverage/accuracy only for leaf signatures whose action is uniquely determined from development data; unseen or incoherent leaves abstain.

No gate requires Fin-3 to win. If the declared carrier cannot restore coherence, the correct result is a certified probe-language obstruction.
