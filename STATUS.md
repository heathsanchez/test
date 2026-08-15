# LIVE STATUS — Triskelion × Lean Kernel Arena

## Current admitted frontier
A2 remains the current admitted frontier.

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

Callgrind call-edge audit of the existing A2 profile shows `prune_env_cold` is reached mainly through:
- `key_env`: ~1.83M cold calls
- `apply_many` variants directly: ~0.61M cold calls
This makes `apply_many` a distinct high-volume source of canonicalization work rather than merely another cache lookup site.

## Recent rejected/not-admitted experiments
- E0012 level-equality cache: +0.9939% paired proxy; NOT ADMITTED.
- E0013 spine-length fast reject: +2.0898%; REJECT.
- E0014 two-way prune direct map: +0.5779%; REJECT.
- E0015 singleton prune fast path: +0.7837%; REJECT.
- E0016 infer canonical-env threading: +0.1246%; REJECT.

## E0017 — eval canonical-env threading
Run `31857802298`, artifact `9239591838`, digest `sha256:3d73fddf464f839537faa29694ce7e816ee4df27826947c322f7e5dbeef28e1a`.

Intervention: for open structural expressions, reuse the canonical environment already passed from `eval` into `eval_no_cache` instead of re-running `key_env` in the Lambda/Pi branches; preserve closed-expression reduction to the level-substitution base.

- A2: 161/161, zero declines
- E0017: 161/161, zero declines
- A2 median proxy: 0.800028 s
- E0017 median proxy: 0.798131 s
- median paired change: -0.0616%
- median ratio implies ~0.24% raw median speedup

Decision: NOT ADMITTED. Direction is slightly positive but far below a convincing public proxy gate and the paired samples are noisy/mixed. Preserve as mechanistic evidence only; do not stack it.

## E0018 — defer intermediate pruning in apply_many
Status: NEXT LIVE GATE.

Rationale: `apply_many` accounts for roughly a quarter of observed cold-prune calls in the Callgrind call-edge audit. In its nested-Lambda fast path it repeatedly does:

`env_extend -> key_env(env, body) -> env_extend -> ...`

before the final body is evaluated. E0018 tests whether retaining the semantically equivalent unpruned environment during this transient multi-application sequence and allowing the normal downstream persistence/evaluation boundary to canonicalize it removes a meaningful fraction of cold pruning without damaging semantics or later reuse.

Single intervention only: remove the intermediate `key_env(env, body)` inside the nested-Lambda loop in `apply_many`; keep all other A2 behavior unchanged.

## Negative laws
- More prune capacity/associativity does not pay.
- Singleton cold-loop specialization does not pay.
- Isolated duplicate canonicalization at infer/eval closure construction is too small to admit.
- The remaining target is avoiding high-volume transient pruning, especially `apply_many`, or changing environment representation more fundamentally.

## Execution rules
- Continue from A2.
- One intervention at a time.
- Same-runner A2 control for every public comparison.
- Do not stack negative or unresolved candidates.
- Exact-Mathlib promotion requires a frozen exact fixture/protocol.
