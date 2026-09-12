# V38 — Mathlib Exclusive Cost Atlas

## Target / verifier

Primary objective: maximize Lean Kernel Arena leaderboard margin while preserving the exact submitted MathGraph V2 semantic behavior.

Frozen checker revision: `metalogiclabs/mathgraph-lean-kernel@3d7585c21242f29fdaa48ae9a16e16c6afe42238`.

Primary workload: Arena `mathlib` at Arena revision `aaa6aedd3a4f4de88bf825319a8a050e572c9cce`.

Success at this stage is diagnostic, not an optimization claim. V38 passes if it obtains a native, symbol-level **self/exclusive** CPU profile of the exact submitted checker on Mathlib and identifies at least one cost family with enough measured mass that a plausible intervention could move total Mathlib cost by >=5%. If no such family exists, the outcome is `DIFFUSE_COST` and local optimization is down-scoped.

Semantic boundary: Mathlib must still be accepted by the exact submitted checker. No candidate kernel modifications are made in V38.

## Frozen rivals

- `H_ENV`: environment construction / pruning / keying / closure handling contains >=5% plausibly removable Mathlib cost.
- `H_CONV`: conversion / unification / WHNF / force / unfolding contains >=5% plausibly removable Mathlib cost.
- `H_IOTA`: iota / recursor / projection reduction contains >=5% plausibly removable Mathlib cost.
- `H_INFER`: inference / declaration checking contains >=5% plausibly removable Mathlib cost.
- `H_MEMORY`: hashing / interning / allocation / data-structure management contains >=5% plausibly removable Mathlib cost.
- `H_PARSE`: parser / import handling contains >=5% plausibly removable Mathlib cost.
- `H_DIFFUSE`: no single measured family has enough self-cost to license a large local intervention.

These are not assumed mutually exclusive.

## Frozen measurement

1. Clone Arena at `aaa6aedd...`.
2. Build Arena `mathgraph` checker exactly through its own checker recipe (including its PGO procedure).
3. Build the Arena Mathlib export with `lka.py`.
4. Run Mathlib once as a semantic smoke gate.
5. Run a second Mathlib check under `perf record` using a software CPU sampling event (`cpu-clock:u`) and callgraph capture.
6. Generate `perf report --no-children` so percentages are self/exclusive rather than inclusive call-tree mass.
7. Classify symbols into frozen families using name-based rules; preserve an `OTHER` bucket rather than forcing unmatched symbols into a hypothesis.

The profiler run is diagnostic only. Its overhead is not treated as leaderboard timing.

## Outcome → next action map

Let `S_i` be measured self CPU share of family i. A family is only licensed for a next intervention if both:

- `S_i >= 0.05`, and
- there is a concrete source-level mechanism suggesting >=20% of that family can be eliminated without changing semantics.

Priority is `S_i × plausible_removable_fraction`, not raw call frequency.

- If `H_ENV` wins: map environment representation primitives and freeze the smallest representation separator before implementing a rewrite.
- If `H_CONV` wins: split conversion self-cost into direct/cold/WHNF/unfold/force/spine and test whether an entire producer→consumer phase can be removed.
- If `H_IOTA` wins: map recursor/iota/projection subpaths; do not revive V35 unless a different high-mass residual appears.
- If `H_INFER` wins: identify repeated inference objects and test elimination rather than caching first.
- If `H_MEMORY` wins: compare allocation/interner/layout strategy against sokonanoda/zignodamus/nanoclo/nanobruijn at the measured hot object class.
- If `H_PARSE` wins: separate parser throughput from kernel checking before any semantic rewrite.
- If `H_DIFFUSE` wins: reject the one-hot-subsystem hypothesis and move to a whole-machine representation/architecture experiment.

## Attack / descaffolding plan

No optimization is admitted from this profile alone. Any candidate produced by V38 must subsequently pass:

- full available Arena semantic/soundness gate;
- deterministic instruction comparison where practical;
- native repeated timing;
- ablation of the intervention only;
- transfer to at least two source-distinct real corpora (priority: Std, CSLib, Cedar, Init) before retention;
- comparison against the exact submitted V2 baseline under the same build/Pgo/configuration.

## Negative laws already in force

V32–V37 prohibit treating high event frequency, cheap pointer exits, reconstructed closure identity, or free Pi-body provenance as sufficient evidence of economic value. V35 establishes that the remaining MathGraph analogue of Lean #10565 is real but economically shallow (~0.5% deterministic instruction gain on grind-ring-5). V38 therefore measures actual Mathlib self-cost before any further invention.
