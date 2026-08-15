# LIVE STATUS — Triskelion × Lean Kernel Arena

## Current internal frontier
A3 is now the admitted internal/public optimization frontier.

A3 reconstruction:
- upstream sokonanoda `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`
- 4 threads
- session budget 2,621,440 bytes
- E0018: defer intermediate `key_env` pruning inside the nested-Lambda `apply_many` fast path

External submission remains blocked on the separate exact-Mathlib/full-official validation gate; nothing has been submitted publicly to Lean Kernel Arena.

Public immutable Arena artifact used here: `8931227426` (161 cases).

## A2 residual that produced A3
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
- Callgrind call-edge audit: `key_env` ~1.83M cold calls; `apply_many` variants ~0.61M direct cold calls

## Recent rejected/not-admitted experiments
- E0012 level-equality cache: +0.9939% paired proxy; NOT ADMITTED.
- E0013 spine-length fast reject: +2.0898%; REJECT.
- E0014 two-way prune direct map: +0.5779%; REJECT.
- E0015 singleton prune fast path: +0.7837%; REJECT.
- E0016 infer canonical-env threading: +0.1246%; REJECT.
- E0017 eval canonical-env threading: -0.0616% paired median; too small/noisy; NOT ADMITTED.

## E0018 — defer intermediate pruning in apply_many
Initial public proxy run `31857998385`, artifact `9239651349`, digest `sha256:23565e7108f438df59c1d082af9b2114afcb69f726c05dfdd0940e4d58cd34be`.

Intervention: inside the nested-Lambda fast path of `apply_many`, remove the transient `key_env(env, body)` between successive `env_extend` operations. Keep the full semantically equivalent transient environment and allow normal downstream evaluation/persistence boundaries to canonicalize it when needed.

Initial gate:
- A2: 161/161, zero declines
- E0018: 161/161, zero declines
- A2 median proxy: 0.901814 s
- E0018 median proxy: 0.856736 s
- median paired change: -4.6975%
- E0018 won 16/16 paired repetitions

Protected Arena-style validation:
- current Arena sokonanoda recipe independently audited at Arena rev `65a8d80adee64be9f18367197b7474b9537ce0c4`: 4 threads, init-prelude PGO, `target-cpu=native`
- first protected attempt `31858187878`: INFRASTRUCTURE-BLOCKED because hosted image lacked `llvm-profdata`; no scientific result
- corrected protected run `31858264346`
- protected artifact `9239739451`, digest `sha256:20d9ba36bd56e3dda60ebc725db3d8eba1fd48f564be2fb8cbbc87fba63a87e6`
- both arms: 161/161, zero declines
- 12/12 E0018 wall wins
- 12/12 E0018 CPU wins
- 9/12 E0018 RSS wins
- median wall: A2 0.815 s -> E0018 0.780 s
- median CPU: A2 1.06 s -> E0018 1.02 s
- median RSS: A2 535070 KiB -> E0018 518824 KiB
- median paired wall change: -4.9082%
- median paired CPU change: -4.6513%
- median paired RSS change: -3.4164%

Decision: ADMIT E0018 AS A3 for the internal/public optimization stream. It preserves the frozen semantic corpus and gives a large, consistent Arena-style PGO resource improvement. Exact-Mathlib/full-official submission validation is still required before any external Arena submission.

## Admitted law
`CANONICALIZE_AT_PERSISTENCE_BOUNDARIES, NOT_TRANSIENT_COMPOSITION_BOUNDARIES`

Scoped interpretation: environment pruning remains valuable for cache/persistent closure identity, but pruning between immediately chained Lambda applications in `apply_many` destroys and reconstructs information before any persistence boundary and is measurable overhead.

## Negative laws
- More prune capacity/associativity does not pay.
- Singleton cold-loop specialization does not pay.
- Isolated duplicate canonicalization at infer/eval closure construction is too small to admit.
- Do not stack rejected candidates.

## Execution rules
- Continue from A3, not A2.
- Freshly profile A3 before choosing another optimization.
- One intervention at a time.
- Same-runner control for every public comparison.
- Infrastructure failures are not scientific evidence.
- Exact-Mathlib/full-official promotion remains a separate gate before external submission.

## Next gate
Fresh A3 profile: remeasure `grind-ring-5` and per-case distribution after E0018, determine how much `prune_env_cold` moved, and re-rank the next candidate from the new frontier rather than historical A2 residuals.
