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
Decision: NOT ADMITTED in public optimization stream.

## E0013 — SPINE_LENGTH_FAST_REJECT
Run `31856147246`, artifact `9239099644`, digest `sha256:f2453a9fae8712039cb03ca53311e6c2f5d2ec5d6f5a66a6b2a4e7c0bf4aa023`.
- A2: 161/161, zero declines
- E0013: 161/161, zero declines
- median paired change: +2.0898%
Decision: REJECT.

## Fresh A2 profile
Run `31856330536`, artifact `9239142575`, digest `sha256:ad27ef258922b67d8635b61b41eeaade9daff3a2682728225c5f09934b0b0f03`.
Largest measured self instruction cost on `good/perf/grind-ring-5.ndjson`:
- `prune_env_cold`: ~11.55%
- `spine_snoc_hc`: ~5.46%
- `mk_rigid_hc`: ~3.82%
- `key_env`: ~0.44%
- `fire_recursor`: ~0.21%

## A2 prune diagnostic
Run `31856816866`:
`PRUNE_STATS total=3373253 mask0=0 subset=638397 cell_hit=188807 cell_mismatch=368698 dm_hit=82451 dm_occupied_miss=2366604 cold=2463598 cold_cons=1580782 cold_framed=882816`
Cold path ~73.03% of prune calls.

## E0014 — two-way prune direct map
Run `31856928587`, artifact `9239338367`, digest `sha256:7907398061db6a38a2cf008645825f8983962de9fb1e90fddb907df104750e9f`.
- 161/161 both arms
- median paired change: +0.5779%
Decision: REJECT.

## Cold-prune shape diagnostic
Run `31857113683`, artifact `9239385370`, digest `sha256:49491a9efc0e76df15b60b3fa157fd4eaedf16fda1206d9714fc3eea57ce4ecb`.
`PRUNE_SHAPE cold=2480824 pc1=755617 pc2=652431 pc3=443965 pc4p=628811 popsum=6437142 spansum=10606157 span8=2203970 span16=263781 span32=12090 span64=983 cons=1591908 framed=888916`
Derived:
- singleton masks 30.46%
- population <=2 56.75%
- population <=3 74.64%
- span <=8 88.84%
- mean selected population ~2.59
- mean span ~4.28

## E0015 — singleton prune fast path
Run `31857364894`, artifact `9239467287`, digest `sha256:ec31912f51275f7de9dec295dd803a5c56b8c44a390108c7adc7f0b4600083e8`.
- 161/161 both arms
- median paired change: +0.7837%
Decision: REJECT.

## E0016 — infer canonical-env threading
Run `31857516519`, artifact `9239511850`, digest `sha256:11ef702d1dd5b46baff22b33a379077f61d08bd5ef21001bd37f6c431dc9e589`.
- A2: 161/161, zero declines
- E0016: 161/161, zero declines
- A2 median proxy: 0.764280 s
- E0016 median proxy: 0.766739 s
- median paired change: +0.1246%
Decision: REJECT. Duplicate inference-side canonicalization exists but is too small to pay on the public proxy.

## E0017 — eval canonical-env threading
Status: LAUNCHED.
Mechanism: for open structural expressions, `eval` already computes `te = key_env(env,e)` and calls `eval_no_cache(depth, te, e)`. The Lambda/Pi branches inside `eval_no_cache` currently call `key_env(env,e)` again. E0017 preserves closed-expression handling but reuses the already-canonical incoming environment on the open structural path, removing the second prune.

## Negative laws
- E0012 level-equality cache: no public A2 proxy win.
- E0013 spine-length reject: no public A2 proxy win.
- E0014 more prune associativity: no public A2 proxy win.
- E0015 singleton prune specialization: no public A2 proxy win.
- E0016 infer duplicate canonicalization removal: no public A2 proxy win.
- Do not stack negative candidates.

## Execution rules
- Continue from A2.
- One intervention at a time.
- Same-runner A2 control for every public comparison.
- Infrastructure failures are not scientific evidence.
- Exact-Mathlib promotion still requires a frozen exact fixture/protocol.

## Next gate
Resolve E0017. If positive, run exact protected validation before admission. If negative, instrument `key_env`/`prune_env` by caller class before another intervention.
