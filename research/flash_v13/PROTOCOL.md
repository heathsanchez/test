# FLASH V13 — Prospective incremental global consequence closure

Freeze: 2026-10-12. Parent independently qualified V12b run #38202495321 / exact head ad5c4cade218c3e67538f05c26463ae590dcde17; V11 run #38201499353; V10 run #38199516805.

## Canonical research source
September 2026 `Flash: Incremental Global Consequence Closure for Nonlinear Development` (Library: Flash_Incremental_Global_Consequence_Closure_Architecture_Note(1).docx) defines **event → dependency cone → warranted reclosure → changed frontiers → local fixed point**. FLASH is not simply step ordering, parallel agents or introspective language. The paper's six implementation gates are: (1) cross-frontier propagation, (2) dormant-capability revival, (3) negative propagation, (4) incrementality, (5) provenance-based revocation, and (6) restart with compiled warranted state.

## Frozen objective
Build ONE generic executable consequence engine over a typed finite authority/rule/frontier fixture, with new authenticated events changing all affected dependent frontiers without recomputing unaffected ones. Compare after every event to a separately implemented batch fixed-point oracle. Explicitly distinguish *causal origin* from *logical support*: revoking one parent must not revoke independently supported descendants. Support multiple Horn-hyperedge certificates, negative separators and equivalence refinement.

## Data and event boundaries
- `fixture.json` contains synthetic multi-frontier graph rules, typed event schedule, candidate/resource guards, alternative supports and a disjoint negative control; freeze it in GitHub **before writing engine or reference implementation**.
- Real bounded source authority inputs: V10 matroid independence, V11 complete hereditary branch search and V12b score-aware branch engine. Pinned run IDs are evidence pointers, NOT proof of the synthetic cross-domain dependency edges.
- Synthetic event authorities are fixture-specific finite simulated certificates; they are *not* actual Lean/QCK physical results. Do not conflate emulated event physics with outside-world truth.
- Engine must fail closed on unrecognized facts, forged authority, improper revoke, or oversized nonconvergent rule sets.
- Positive Horn closure is least fixed point. Separators/obstructions can block candidates and force safe quotient split. Revocation may retract active consequences only after all alternative supports are gone.
- Future frontiers recompute exactly when their semantics depend on changed facts; protected budgets and source-evidence assumptions must be respected.

## Independent tests and comparison
1. Derive affected dependency cone from the frozen graph, not manually curated frontier lists.
2. Against a separate independent full-batch reference: exact active-fact sets, per-fact supporting proof alternatives, selected capability/cost, frontier candidate statuses, and event history after each event.
3. Test cross-frontier propagation, AND synergy, dormant revival, separator/nonmonotone negative propagation, late revocation, alternate evidence, disjoint-frontier incrementality, idempotence, order invariance where appropriate, and deliberate forged event injection.
4. Serialize the reclosed present, restart from a SHA-pinned snapshot without replaying earlier discoveries; continue future events, compare with batch authority at every point.
5. Record dirty-graph/frontier work, batch work, memory and wall time, including initial graph validation, independent oracle and persistence overhead; do not claim total speedup if only touched-node counts fall.
6. Freeze the engine and external validator source and run independent exact-head GitHub Actions; retain artifacts/negative tests.

## Promotion boundary
WARRANTED only as a finite, source-pinned, synthetic event-closure implementation. No causal recursive generator invention, universal convergence, new physical ontology, or universal computational advantage follows. A fully informed sequential program can emulate the same finite event-closure semantics. Its relative cost is the meaningful benchmark.

## Decisive outcome
If all six gates pass, FLASH is a verified, restartable operational layer rather than a research metaphor. If any gate fails, keep exact counterexample and refuse promotion. Continue to open-world external authority / true generator-change transfer only after this strict gate.
