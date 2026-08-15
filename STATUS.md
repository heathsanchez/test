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

Protected Arena-style validation run `31858264346`, artifact `9239739451`, digest `sha256:20d9ba36bd56e3dda60ebc725db3d8eba1fd48f564be2fb8cbbc87fba63a87e6`:
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
- semantic replay 161/161
- grind-ring-5 ~0.6400 s median and dominates the corpus
- generic Callgrind: `prune_env_cold` 382,910,453 / 2,697,871,700 self instructions = 14.19%

## Frame-interner diagnostic
Run `31859221975`, artifact `9240001631`, digest `sha256:3c6854b949584e1691db9282f4e24c04569bafc78cab65b91347e0ea515b9a9a`.
`FRAME_INTERN_STATS calls=1848149 hits=745981 misses=1102168`
- existing frame reuse ~40.36%
- misses/new frames ~59.64%

## E0019 — output-frame direct-map L0
Run `31859367528`, artifact `9240061642`, digest `sha256:523f4e067cad8cfa2d247862ed25945ab397a5f7090fb3e0a3e8c138f4af1c84`.
- both arms 161/161, zero declines
- A3 median 0.727750 s
- E0019 median 0.733530 s
- median paired +0.5518%
- wins 9/20
Decision: REJECT.

## E0020 — session arena reuse only
Run `31859502887`, artifact `9240106578`, digest `sha256:c00f8593e2aab0f34ad5e144af723e9cb8952ce00f5adb0b2bb24ccc30216909`.
- both arms 161/161, zero declines
- A3 median 0.754090 s
- E0020 median 0.758541 s
- median paired +0.6846%
- E0020 wins 6/20
Decision: REJECT.

## E0021 — table capacity retention
Initial proxy run `31859635982`, artifact `9240145420`, digest `sha256:4ded8c1d7bb08d39fe7e45271486baf55367f8a9aa5b821c26291e1b37486902`:
- both 161/161, zero declines
- A3 median 0.831512 s
- E0021 median 0.820946 s
- paired median -1.4633%
- E0021 wins 16/20

Protected Arena-style PGO run `31859768733`, artifact `9240190729`, digest `sha256:28c59c2ae0a6c6388e98655ff774ad3b72465ebed911b4c4e654b430ca933b5d`:
- both arms 161/161, zero declines
- median wall: 0.70 s vs 0.70 s
- median CPU: 0.90 s vs 0.90 s
- median RSS: 515800 vs 513734 KiB
- paired median wall: 0.0%
- paired median CPU: +1.1111% (worse)
- paired median RSS: -0.5288%
- wins: wall 3/12, CPU 2/12, RSS 6/12

Decision: REJECT. The native proxy gain did not survive the Arena-style PGO resource gate; CPU moved the wrong way. A3 remains frontier.

## E0022 — bypass open Let cache
Run `31860047529`, artifact `9240278345`, digest `sha256:e17bba3e31daf2e6736ab86a801a8813cce6bc36637e4dd2d23a6cc4df42be91`.
- both arms 161/161, zero declines
- A3 median 0.798503 s
- E0022 median 0.797575 s
- paired median -0.2050%
- E0022 wins 11/20
Decision: NOT ADMITTED. Direction is positive but too small/noisy for promotion.

## A3 open-eval cache diagnostic
Run `31860481789`, artifact `9240408036`, digest `sha256:28311009f16464d6622b4a879d71b4e5ea3eb76893043061c628d914af36033c`.
Sampled grind-ring-5 open-eval cache economics by expression class:
- App: n=1489, hit 32.57%, same-env 14.71%, mean loose=5.564, mean mask-pop=2.764
- Lambda: n=383, hit 29.50%, same-env 12.79%, mean loose=4.606, mean mask-pop=3.196
- Pi: n=267, hit 58.05%, same-env 4.12%, mean loose=2.539, mean mask-pop=1.820
- Proj: n=17, hit 70.59%, same-env 0%
- Let: n=7, hit 0% in the sample

Interpretation: App and Lambda are the only high-volume classes with moderate hit rates and expensive environment projection. Pi/Proj appear substantially more cache-valuable. This motivates scoped deletion tests before inventing a new representation.

## Current live experiments
- E0023: bypass open-eval canonicalization/cache for Lambda only. Run `31860855495` launched from commit `46f15b6cb334dfa633f72e70543105a7ed9e84c6`; currently executing.
- E0024: bypass open-eval canonicalization/cache for App only. Launched from commit `ae2ed5db0cbe6fa80ee9cb7db8fcc7052c7ee766`; independent A3-rebased arm.

## A3 vs current zignodamus diagnostic
Run `31860374211` compared A3 PGO against zignodamus `111372299e41188a159d05f8df780342e12aff1b` on the same frozen corpus/workload. Both replayed 161/161. The zignodamus benchmark arm repeatedly aborted/core-dumped during resource measurement and therefore is not a clean scientific performance comparison; do not use its large apparent wall/CPU gap as leaderboard evidence. The correctness replay is still useful.

## Recent rejected/not-admitted experiments
- E0012 level-equality cache: +0.9939% paired proxy; NOT ADMITTED.
- E0013 spine-length fast reject: +2.0898%; REJECT.
- E0014 two-way prune direct map: +0.5779%; REJECT.
- E0015 singleton prune fast path: +0.7837%; REJECT.
- E0016 infer canonical-env threading: +0.1246%; REJECT.
- E0017 eval canonical-env threading: -0.0616% paired median; too small/noisy; NOT ADMITTED.
- E0019 output-frame L0 direct map: +0.5518%; REJECT.
- E0020 in-place arena reset: +0.6846%; REJECT.
- E0021 retain oversized table capacities: protected CPU +1.1111%; REJECT.
- E0022 bypass open Let cache: -0.2050%; too small/noisy; NOT ADMITTED.

## Negative laws
- More input-prune-map capacity/associativity does not pay.
- Singleton cold-loop specialization does not pay.
- Isolated duplicate canonicalization at infer/eval closure construction is too small to admit.
- Frame interning has substantial reuse, but another direct-map lookup layer does not pay.
- Retaining allocator chunks alone does not pay.
- Retaining oversized table capacities can look positive in a non-PGO proxy but does not survive the Arena-style PGO gate.
- Bypassing a tiny near-zero-hit class (Let) is semantically safe but too small to matter alone.
- Do not stack rejected candidates.

## Execution rules
- Continue from A3 until a later arm clears protected admission.
- One intervention per candidate arm.
- Same-runner control for every public comparison.
- Infrastructure failures are not scientific evidence.
- Exact-Mathlib/full-official promotion remains a separate gate before external submission.

## Next gate
Resolve E0023 and E0024. If either shows a clear same-runner proxy win, run the protected Arena-style PGO wall/CPU/RSS gate immediately. If neither wins, retain Pi/Proj caching and move from deletion to a representation-level experiment: avoid fully materializing canonical environments for low-value App/Lambda cache lookups while preserving semantic cache identity.
