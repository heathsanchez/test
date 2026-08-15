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

## E0014 — two-way prune direct map

Run `31856928587`, artifact `9239338367`, digest `sha256:7907398061db6a38a2cf008645825f8983962de9fb1e90fddb907df104750e9f`.

Intervention: retain a second recent entry for each prune direct-map slot; check both ways before cold pruning.

- A2: 161/161, zero declines
- E0014: 161/161, zero declines
- A2 median proxy: 0.799205 s
- E0014 median proxy: 0.803238 s
- median paired change: +0.5779%

Decision: REJECT. More associativity does not pay for itself.

## Cold-prune shape diagnostic

Run `31857113683`, artifact `9239385370`, digest `sha256:49491a9efc0e76df15b60b3fa157fd4eaedf16fda1206d9714fc3eea57ce4ecb`.

On grind-ring-5:

`PRUNE_SHAPE cold=2480824 pc1=755617 pc2=652431 pc3=443965 pc4p=628811 popsum=6437142 spansum=10606157 span8=2203970 span16=263781 span32=12090 span64=983 cons=1591908 framed=888916`

Derived shape:
- singleton masks: 30.46% of cold calls
- population <=2: 56.75%
- population <=3: 74.64%
- span <=8: 88.84%
- span <=16: 99.47%
- mean selected population: ~2.59
- mean span/depth: ~4.28
- starting Cons: 64.17%; Framed: 35.83%

The residual is overwhelmingly shallow and sparse. This argues for avoiding repeated pruning work or lowering fixed per-call overhead, not building a general large-mask algorithm.

## E0015 — singleton prune fast path

Run `31857364894`, artifact `9239467287`, digest `sha256:ec31912f51275f7de9dec295dd803a5c56b8c44a390108c7adc7f0b4600083e8`.

Intervention: for a one-bit mask, use direct `Env::lookup` and construct the one-slot canonical frame without the generic cold-prune loop.

- A2: 161/161, zero declines
- E0015: 161/161, zero declines
- A2 median proxy: 0.733165 s
- E0015 median proxy: 0.737547 s
- median paired change: +0.7837%

Decision: REJECT.

## E0016 — infer canonical-env threading

Run `31857516519`, artifact `9239511850`, digest `sha256:11ef702d1dd5b46baff22b33a379077f61d08bd5ef21001bd37f6c431dc9e589`.

Intervention: in `infer_value`, compute `key_env(env,e)` once for the type-cache key and reuse the resulting canonical environment for `Closure::mk_infer` on Lambda cache misses.

- A2: 161/161, zero declines
- E0016: 161/161, zero declines
- A2 median proxy: 0.764280 s
- E0016 median proxy: 0.766739 s
- median paired change: +0.1246%

Decision: REJECT. The duplicate infer-site canonicalization is real but too small/noisy to provide a public proxy win.

## Negative laws

- E0012 universe-level equality cache: no public A2 proxy win.
- E0013 immediate spine-length mismatch reject: no public A2 proxy win.
- E0014 two-way prune direct map: no public A2 proxy win.
- E0015 singleton-mask special case: no public A2 proxy win.
- E0016 infer duplicate canonical-env threading: no public A2 proxy win.
- Larger/more associative prune lookup is not currently the route.
- Shape-specializing the cold loop itself is not sufficient; target repeated calls / representation-level avoidance.

## Execution rules

- Continue from A2.
- One intervention at a time.
- Same-runner A2 control for every public performance comparison.
- Do not stack negative or unresolved candidates.
- Infrastructure failures are not scientific evidence.
- Any exact-Mathlib result must use a frozen reconstructed Mathlib fixture/protocol, not this 24-case proxy.

## Next gate

E0017: canonical-environment threading in evaluation. For open structural expressions, `eval` computes `te = key_env(env,e)` and passes that exact canonical environment to `eval_no_cache`. The Lambda and Pi branches inside `eval_no_cache` then call `key_env(env,e)` again. Remove only that duplicate open-path pruning while preserving the closed-expression semantics, and benchmark as a single intervention on A2.
