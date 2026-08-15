# LIVE STATUS — Triskelion × Lean Kernel Arena

## Current admitted frontier
A2 remains the current admitted frontier pending protected validation of E0018.

A2 reconstruction:
- upstream sokonanoda `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`
- 4 threads
- session budget 2,621,440 bytes

Public immutable Arena artifact: `8931227426` (161 cases).

## Current performance state
Fresh A2 Callgrind on `good/perf/grind-ring-5.ndjson`:
- `prune_env_cold`: ~11.55% self instruction cost
- `spine_snoc_hc`: ~5.46%
- `mk_rigid_hc`: ~3.82%
- `key_env`: ~0.44%
- `fire_recursor`: ~0.21%

Cold-prune diagnostics:
- ~73% of prune calls reach cold path
- singleton masks: 30.46% of cold calls
- population <=2: 56.75%
- population <=3: 74.64%
- span <=8: 88.84%
- mean selected population ~2.59; mean span ~4.28

Callgrind call-edge audit of A2 shows `prune_env_cold` reached mainly through:
- `key_env`: ~1.83M cold calls
- `apply_many` variants directly: ~0.61M cold calls

## Recent rejected/not-admitted experiments
- E0012 level-equality cache: +0.9939% paired proxy; NOT ADMITTED.
- E0013 spine-length fast reject: +2.0898%; REJECT.
- E0014 two-way prune direct map: +0.5779%; REJECT.
- E0015 singleton prune fast path: +0.7837%; REJECT.
- E0016 infer canonical-env threading: +0.1246%; REJECT.
- E0017 eval canonical-env threading: -0.0616% paired median; direction positive but too small/noisy; NOT ADMITTED.

## E0018 — defer intermediate pruning in apply_many
Run `31857998385`, artifact `9239651349`, digest `sha256:23565e7108f438df59c1d082af9b2114afcb69f726c05dfdd0940e4d58cd34be`.

Intervention: inside the nested-Lambda fast path of `apply_many`, remove the transient
`key_env(env, body)` between successive `env_extend` operations. Keep the full semantically equivalent transient environment and let the normal downstream evaluation/persistence boundary canonicalize it when needed.

Semantic gate:
- A2: 161/161, zero declines
- E0018: 161/161, zero declines

24-case paired public proxy, 16 counterbalanced repetitions:
- A2 median: 0.901814 s
- E0018 median: 0.856736 s
- median paired fractional change: -4.6975%
- raw median speed ratio A2/E0018: 1.05262 (~5.26%)
- E0018 won all 16/16 paired repetitions

Decision: STRONG CANDIDATE / PUBLIC PROXY PASS, NOT YET ADMITTED AS A3. This is the strongest post-A2 candidate so far and must now clear a protected Arena-shaped resource gate (actual build recipe where practical, CPU/wall/RSS, semantic preservation) before admission.

## Current law update
The useful distinction is now sharper:
- pruning at persistence/cache boundaries is valuable;
- pruning transient environments between immediately chained Lambda applications can be pure overhead.

Candidate law:
`CANONICALIZE_AT_PERSISTENCE_BOUNDARIES, NOT_TRANSIENT_COMPOSITION_BOUNDARIES`.

## Negative laws
- More prune capacity/associativity does not pay.
- Singleton cold-loop specialization does not pay.
- Isolated duplicate canonicalization at infer/eval closure construction is too small to admit.
- Do not stack negative candidates.

## Execution rules
- A2 remains official frontier until E0018 protected validation passes.
- One intervention at a time.
- Same-runner control for every public comparison.
- Infrastructure failures are not scientific evidence.
- Exact-Mathlib promotion requires a frozen exact fixture/protocol.

## Next gate
Protected validation of E0018: reconstruct the current Arena sokonanoda build/benchmark recipe, preserve 161/161 semantics, measure paired wall + CPU + peak RSS, and only then decide whether E0018 becomes A3.
