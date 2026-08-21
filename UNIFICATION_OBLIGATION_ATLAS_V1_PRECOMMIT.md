# Lean Kernel Arena — Unification Obligation Atlas V1

## Purpose

Replace function-hotspot optimization with a verifier-induced quotient over **semantic obligations**. The unit of analysis is one definitional-equality/unification episode, not one Rust function.

Pinned kernel: `metalogiclabs/mathgraph-lean-kernel@3d7585c21242f29fdaa48ae9a16e16c6afe42238`.

The V28 Callgrind edge ranking is treated only as a localization signal. Its aggregated edge costs are inclusive/call-graph units and may double-count work; no percentage from that parser is treated as removable instruction mass.

## Core object

For each sampled unification episode `u`, collect a cheap pre-state signature `rho(u)` and the actual resolution trajectory `tau(u)`.

Pre-state vocabulary is intentionally low-level and semantics-inert:

- left/right Value constructor class;
- pointer equality before general unification;
- cacheability class;
- rigid-head relation class when available (same / different / not-rigid);
- spine length buckets when available;
- depth bucket;
- whether each operand changes under force_thunk;
- whether the episode resolves in NAT, DIRECT, or COLD;
- final Boolean result.

Trajectory counters include at minimum:

- recursive unify invocations;
- force_thunk calls;
- direct resolution;
- cold resolution;
- unfold attempts;
- iota attempts;
- spine unification/probes;
- proof-irrelevance probes;
- environment/canonicalization calls if reachable from the episode.

## Lawful-action carrier

The first finite candidate carrier contains only local, verifier-replayable alternatives derived from existing kernel mechanisms:

1. GENERAL — existing path.
2. DIRECT_ONLY — accept only episodes already discharged by the direct relation-specific path; otherwise abstain to GENERAL.
3. SAME_RIGID_HEAD_SPINE — route matching rigid-head episodes directly to the existing spine comparison mechanism; otherwise GENERAL.
4. ONE_SIDE_UNFOLD_LEFT — use only when the pre-state supplies an unfoldable left operand; otherwise GENERAL.
5. ONE_SIDE_UNFOLD_RIGHT — symmetric.
6. IOTA_FIRST — use only for recursor/quotient-head episodes; otherwise GENERAL.

An action is lawful for an episode only if replay produces the same verifier result as GENERAL. Abstention/fallback is not counted as a speedup.

## Commitment complex

For sampled episodes `E`, define

`A*(u) = {Theta : Theta is verifier-equivalent to GENERAL on u}`

and

`E^up = intersection_{u in E} A*(u)`.

A cell may remain joined iff `E^up` is nonempty and contains at least one non-GENERAL action with measured work reduction.

## Representation search

Search the supplied cheap pre-state vocabulary for the minimum quotient `Q` such that every quotient cell admits at least one common lawful non-GENERAL action or is explicitly routed to GENERAL. Every retained distinction must be deletion-load-bearing: removing it must merge at least one pair of cells whose lawful-action intersection loses the selected specialized action.

No semantic labels such as IOTA, UNFOLD, STRUCTURAL, CACHE, or FAST are supplied to the quotient learner; those names are audit-only descriptions of existing mechanisms.

## Gates

G0: pinned baseline passes the complete 161-case Arena semantic corpus with zero declines.

G1: corrected profiling accounting reports per-workload total Ir and exclusive/self function costs without cross-edge double counting.

G2: at least 100k natural unification episodes are collected on grind-ring-5, or the run fails `INSUFFICIENT_OBLIGATION_EPISODES`.

G3: at least one non-GENERAL lawful action applies to >= 1% of sampled episodes and removes >= 1% of measured episode-local work in aggregate. Otherwise conclude `NO_CHEAP_SPECIALIZABLE_OBLIGATION_CELL`.

G4: a minimum cheap quotient makes action choice deterministic on the development sample.

G5: every retained quotient distinction is deletion-load-bearing.

G6: freeze quotient/action map before untouched source-distinct Arena performance cases.

G7: held-out semantics remain exact and selected fast paths preserve outcomes.

G8: measured native/PGO CPU improves on the protected gate before any optimization is admitted.

## Interpretation

- G3 fails: current pre-state does not expose enough information for cheap routing. This is a representation obstruction; next experiment must test new carried semantic state/identity, not another branch tweak.
- G3 passes but G4 fails: lawful actions exist but cheap supplied observables cannot identify applicability; develop the probe/state language.
- G4–G7 pass but G8 fails: the quotient is semantically real but economically irrelevant; retain as negative law.
- G8 passes: install the minimum deterministic router and run exact-Mathlib/full-official promotion.

## Rewrite separator

In parallel, score whether repeated episode-local trajectories show the same semantic obligation being reconstructed through multiple implementation histories. A rewrite is licensed only if the atlas shows one of:

1. a high-mass obligation class with a much smaller common lawful discharge path;
2. repeated reconstruction of verifier-equivalent intermediate state whose identity can be carried once;
3. multiple physical mechanisms implementing one quotient-level semantic operation.

The rewrite target is therefore not `make Rust shorter`; it is `make the operational language factor through the smallest verifier-sufficient obligation algebra`.
