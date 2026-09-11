# Verified Meta-Developmental Compounding V1 — Frozen Protocol

## Question

Does retaining an acquired developmental procedure reduce the fully charged cost of acquiring a different later developmental procedure, and does accumulating two acquired developers reduce the next acquisition cost further?

## Frozen curriculum

- `D1` (already acquired): find one verifier-certified separating coordinate and pair it with the protected representation. Training selected fields 0 and 1; its frozen generic program contains no later target IDs.
- `D2`: repair a residual requiring the least joint cover of two novel static coordinates, fields 2 and 3. `D1` alone cannot solve it.
- `D3`: repair a residual requiring two history-sensitive coordinates, lag-fields 0 and 1. Neither `D1` nor `D2` alone can solve it without acquiring temporal lifting.

Primitive substrate: `SCAN`, `FILTER`, `FIRST`, `PAIR`, `EXTEND`, `TEMPORAL`. Retained developers are callable verified macros whose internal verifier probes remain charged.

## Search and cost

All syntactic programs are enumerated by increasing token length. Every program at the first successful length is evaluated, eliminating within-level enumeration-order effects. The primary metric is every verifier probe performed by `FILTER`, `EXTEND`, and `PAIR`, including probes inside macros. Search nodes and candidate evaluations are also recorded.

Conditions:

- `COLD`: primitives only.
- `WARM_D1`: primitives plus acquired `D1`.
- `WARM_D1_D2`: primitives plus acquired `D1` and `D2`.
- `ABLATION`: remove the earlier capability predicted to matter.
- `SHAM`: matched macro slots containing inert programs with the same nominal state budget.
- `ANSWER_MEMORY`: earlier selected coordinate IDs without the acquired procedures.

## Precommitted pass

1. All conditions preserve correctness; warm has no regression.
2. `D2`: `WARM_D1 < COLD`; ablation restores cold; sham and answer memory do not reproduce the gain.
3. `D3`: `WARM_D1_D2 < WARM_D1 < COLD`; ablating `D2` restores the `D1`-only cost; sham and answer memory do not reproduce the gain.
4. Aggregate warm cost is at least 2× lower than cold.
5. Warm next-acquisition cost decreases from `D2` to `D3`.

## Boundary

A pass earns bounded meta-developmental compounding in this finite program language. It does not establish cross-domain, unbounded, or model-training compounding.
