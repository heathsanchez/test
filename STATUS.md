# LIVE STATUS — Triskelion × Lean Kernel Arena

## Current admitted frontier

A2 remains the current admitted frontier.

A2 reconstruction:
- upstream sokonanoda `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`
- 4 threads
- session budget 2,621,440 bytes

Public immutable Arena artifact used here: `8931227426` (161 cases). Do not relabel these public results as the later private 178-file corpus.

## E0012 — symmetric universe-level equality cache

Run `31855875785`, artifact `9239017873`, digest `sha256:448c3c17713f21824e56e6a978634bb26741aca09282d4369e1aa197dd20e103`.

- A2: 161/161, zero declines
- E0012: 161/161, zero declines
- A2 median proxy: 0.917405 s
- E0012 median proxy: 0.919181 s
- median paired change: +0.9939%

Decision: NOT ADMITTED in public optimization stream. Private exact-Mathlib decision remains formally open because those local fixtures were not pushed.

## E0013 — SPINE_LENGTH_FAST_REJECT

Run `31856147246`, artifact `9239099644`, digest `sha256:f2453a9fae8712039cb03ca53311e6c2f5d2ec5d6f5a66a6b2a4e7c0bf4aa023`.

- A2: 161/161, zero declines
- E0013: 161/161, zero declines
- A2 median proxy: 0.959417 s
- E0013 median proxy: 0.977648 s
- median paired change: +2.0898%

Decision: REJECT.

## Fresh A2 profile

Run `31856330536`, artifact `9239142575`, digest `sha256:ad27ef258922b67d8635b61b41eeaade9daff3a2682728225c5f09934b0b0f03`.

Largest case by far: `good/perf/grind-ring-5.ndjson` (~0.646 s median in 3-run per-case profiling).

Callgrind on grind-ring-5 re-ranked the A2 residual. Largest measured self instruction cost:
- `prune_env_cold`: ~11.55%
- `spine_snoc_hc`: ~5.46%
- `mk_rigid_hc`: ~3.82%
- eval/eval_no_cache paths follow
- `key_env`: ~0.44% self
- `fire_recursor`: ~0.21% self

Interpretation: after A2, cold environment pruning is the dominant measured self-cost. Historical iota/recursor candidates are no longer the first target.

## A2 prune diagnostic

Run `31856816866` on grind-ring-5:

`PRUNE_STATS total=3373253 mask0=0 subset=638397 cell_hit=188807 cell_mismatch=368698 dm_hit=82451 dm_occupied_miss=2366604 cold=2463598 cold_cons=1580782 cold_framed=882816`

Approximate rates:
- subset fast path: 18.93%
- per-env one-entry hit: 5.60%
- direct-map hit: 2.44%
- cold path: 73.03%
- cold Cons: 64.17% of cold
- cold Framed: 35.83% of cold

The direct map is frequently occupied by a different key, but occupancy alone does not prove useful associativity/reuse.

## E0014 — two-way prune direct map

Run `31856928587`, artifact `9239338367`, digest `sha256:7907398061db6a38a2cf008645825f8983962de9fb1e90fddb907df104750e9f`.

Intervention: retain a second recent entry for each prune direct-map slot; check both ways before cold pruning.

- A2: 161/161, zero declines
- E0014: 161/161, zero declines
- A2 median proxy: 0.799205 s
- E0014 median proxy: 0.803238 s
- median paired change: +0.5779%

Decision: REJECT. More associativity does not pay for itself on this workload despite the high occupied-miss count. This joins the older capacity-sweep negative: do not attack `prune_env_cold` by simply adding more direct-map storage/lookups.

## Negative laws

- E0012 universe-level equality cache: no public A2 proxy win.
- E0013 immediate spine-length mismatch reject: no public A2 proxy win.
- E0014 two-way prune direct map: no public A2 proxy win.
- Larger/more associative prune lookup is not currently the route; optimize or avoid cold pruning itself.

## Execution rules

- Continue from A2.
- One intervention at a time.
- Same-runner A2 control for every public performance comparison.
- Do not stack negative or unresolved candidates.
- Infrastructure failures are not scientific evidence.
- Any exact-Mathlib result must use a frozen reconstructed Mathlib fixture/protocol, not this 24-case proxy.

## Next gate

Characterize the 2.46M cold prune calls before modifying the algorithm: measure free-variable mask population/count shape and traversal shape on grind-ring-5. Use that evidence to choose a narrow cold-path specialization rather than another cache experiment.
