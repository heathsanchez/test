# LIVE STATUS — Triskelion × Lean Kernel Arena

## Current internal frontier
A3 remains the admitted internal/public optimization frontier.

A3 reconstruction:
- upstream sokonanoda `9b4ea12f4cd437d00b6bcd0e34743065c58dea08`
- 4 threads
- session budget 2,621,440 bytes
- E0018: defer intermediate `key_env` pruning inside the nested-Lambda `apply_many` fast path

External submission remains blocked on the separate exact-Mathlib/full-official validation gate; nothing has been submitted publicly to Lean Kernel Arena.

Public immutable Arena artifact used here: `8931227426` (161 cases).

## E0018 — admitted as A3
Initial public proxy run `31857998385`, artifact `9239651349`, digest `sha256:23565e7108f438df59c1d082af9b2114afcb69f726c05dfdd0940e4d58cd34be`.

Initial gate:
- both arms 161/161, zero declines
- A2 median proxy 0.901814 s
- E0018 median proxy 0.856736 s
- median paired change -4.6975%
- E0018 won 16/16 paired repetitions

Protected Arena-style validation:
- Arena recipe audited at rev `65a8d80adee64be9f18367197b7474b9537ce0c4`: 4 threads, init-prelude PGO, `target-cpu=native`
- first attempt `31858187878`: INFRASTRUCTURE-BLOCKED due missing `llvm-profdata`
- corrected run `31858264346`, artifact `9239739451`, digest `sha256:20d9ba36bd56e3dda60ebc725db3d8eba1fd48f564be2fb8cbbc87fba63a87e6`
- both arms 161/161, zero declines
- 12/12 wall wins; 12/12 CPU wins; 9/12 RSS wins
- median wall 0.815 -> 0.780 s
- median CPU 1.06 -> 1.02 s
- median RSS 535070 -> 518824 KiB
- median paired wall -4.9082%
- median paired CPU -4.6513%
- median paired RSS -3.4164%

Decision: ADMIT E0018 AS A3.

Admitted law: `CANONICALIZE_AT_PERSISTENCE_BOUNDARIES, NOT_TRANSIENT_COMPOSITION_BOUNDARIES`.

## Fresh A3 profile
Run `31858552774`, artifact `9239805478`, digest `sha256:0c7a95f7de6bcb3eef198951c1adc1ff5d02df2e1247d9baaf3bb5c938aa6107`.

Semantic replay: 161/161, zero failures.

Per-case timing:
- `good/perf/grind-ring-5.ndjson`: ~0.6400 s median
- `good/perf/app-lam.ndjson`: ~0.0447 s
- `good/init-prelude.ndjson`: ~0.0406 s
- remaining cases are much smaller

Generic x86-64 Callgrind on grind-ring-5:
- total measured instructions: 2,697,871,700
- `prune_env_cold`: 382,910,453 self instructions = 14.19%

Interpretation: after the ~5% A3 gain, cold environment pruning remains the dominant measured local residual.

## Frame-interner diagnostic
Run `31859221975`, artifact `9240001631`, digest `sha256:3c6854b949584e1691db9282f4e24c04569bafc78cab65b91347e0ea515b9a9a`.

On grind-ring-5:
`FRAME_INTERN_STATS calls=1848149 hits=745981 misses=1102168`

Derived:
- existing canonical-frame reuse: ~40.36%
- frame constructions/new misses: ~59.64%

## E0019 — output-frame direct-map L0
Run `31859367528`, artifact `9240061642`, digest `sha256:523f4e067cad8cfa2d247862ed25945ab397a5f7090fb3e0a3e8c138f4af1c84`.

Intervention: 4096-slot exact-checked direct-mapped accelerator in front of `tc_cache.frames.find` inside `intern_frame`.

Results:
- A3: 161/161, zero declines
- E0019: 161/161, zero declines
- A3 median proxy: 0.727750 s
- E0019 median proxy: 0.733530 s
- median paired change: +0.5518%
- E0019 won only 9/20 paired repetitions
- median speed ratio A3/E0019: 0.99212

Decision: REJECT. The ~40% existing frame-interner reuse does not imply enough cheap direct-map locality to pay for another lookup/verification layer.

## Recent rejected/not-admitted experiments
- E0012 level-equality cache: +0.9939% paired proxy; NOT ADMITTED.
- E0013 spine-length fast reject: +2.0898%; REJECT.
- E0014 two-way prune direct map: +0.5779%; REJECT.
- E0015 singleton prune fast path: +0.7837%; REJECT.
- E0016 infer canonical-env threading: +0.1246%; REJECT.
- E0017 eval canonical-env threading: -0.0616% paired median; too small/noisy; NOT ADMITTED.
- E0019 output-frame L0 direct map: +0.5518%; REJECT.

## Negative laws
- More input-prune-map capacity/associativity does not pay.
- Singleton cold-loop specialization does not pay.
- Isolated duplicate canonicalization at infer/eval closure construction is too small to admit.
- Frame interning has substantial reuse, but another direct-map lookup layer does not pay on A3.
- Do not stack rejected candidates.

## Execution rules
- Continue from A3 until a later arm clears protected admission.
- One intervention at a time.
- Same-runner control for every public comparison.
- Infrastructure failures are not scientific evidence.
- Exact-Mathlib/full-official promotion remains a separate gate before external submission.

## Next gate
E0020: session arena reuse only. Replace `SessionBump::reset()`'s fresh `bumpalo::Bump::new()` with an in-place bump reset, holding table-capacity policy fixed. Benchmark A3 vs E0020. If this wins, test table-capacity retention separately before considering their interaction.
