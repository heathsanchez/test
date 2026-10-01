# Bounded proof-type conversion qualification

Status: WARRANTED / REUSABLE on the explicit four dependency-slice boundary, 2026-10-01.

Tested executable: `13d5c777b9837eaff5d8007f17241682404bff37`.
Base: `e5916cf9d2863377d84a717604ef1da452eb62ea`.
Branch: `nucleus-proof-types-v1`.
[Qualification run 36796915663](https://github.com/heathsanchez/test/actions/runs/36796915663), job 110162347791: SUCCESS.
Artifact 11133898998, downloaded ZIP SHA-256 `79c2d0fe34e9e6cd13a12ff97c58364459616c5366b9b081d3c11324ab5514aa` (272435 bytes).

## Law and bounds

Two neutral proof terms may be equal when their independently inferred types are propositions and those types convert in the caller's typed context. The new proposition-type conversion probe preserves caller delta policy, binder depth and context. Its conversion budget is capped at 256. The probe disables this new shortcut recursively, including application and projection congruence; failure declines the shortcut and grants no equality or rejection. Existing structural same-proposition proof irrelevance remains available.

Changes are confined to src/typecheck.rs and src/convert.rs; runtime remains independent, without a complete checker backstop. Global judgment budget 65536 and worker stack 64 MiB are unchanged.

## Qualification

165 Rust tests pass in GitHub CI. Eight dedicated controls cover positive convertible proposition types, data non-erasure, different propositions, caller unfolding policy, scoped dependent proofs, zero budget, non-reentry through application congruence, and the positive 256-step cap under an outer budget of 1000000. Projection flag propagation was inspected in review, not isolated by a dedicated test.

Four valid Nat.modCore_lt dependency slices change UNKNOWN to ACCEPT:
- init-prelude
- perf/grind-ring-5
- perf/magma-list-pair-n7
- perf/magma-list-pair-n21

All eight reference checks accept: KAM and substitution engines of lazylean `68c66fa18c1afe029512b90ecfe0b162c0dcd8fb`. These are two engines within one checker lineage, not two independent checkers.

Pinned current194: **110 ACCEPT / 60 REJECT / 24 UNKNOWN**.
Frozen193: **108 ACCEPT / 61 REJECT / 24 UNKNOWN**.
Both: zero wrong, errors, regressions, or verdict changes. Zero new full-file Arena gains. Both app-lam launcher controls pass under an 8 MiB launcher stack.

Current corpus pin: Arena `4c30c4ac4f14a3a899116beb3ea6131880e79a98`, artifact11090525747. Frozen artifact10712869614. Excluded large corpora and instruction ranking remain unqualified.

## Fresh residuals

The full Init and grind-ring-5 files now first stop at Substring.Raw inductive admission. Both magma pair files stop at Iff inductive admission. The other20 full-file first obstructions were not retraced in this run; retain their earlier baseline trace authority.

Next experiment: derive typed singleton-Prop large elimination for Iff's two proof-valued function fields, with full recursor signature/rule checks and data-field negative controls. Do not name-whitelist Iff or grant generic large elimination. Substring.Raw, Option and WellFounded remain distinct admission work.

## Lineage and review

Red-only commit `5148d20769d8ef8552c7e15a05d59b367117d4d1`, [run36796502065](https://github.com/heathsanchez/test/actions/runs/36796502065), demonstrates three intended failures on baseline: convertible proposition types, dependent local proofs, and policy-sensitive unfolding. Three negative controls already pass.

First candidate `c47677e3c6dc701aa35e25c400f92bf78a6eda0e`, run36796691049: SUCCESS, 163 tests, same four slice gains and unchanged full verdicts. Artifact11133724036 digest supplied by GitHub: cb5e5477f403874321643cfc2b449cd2bfdf5eb0ae1934c7049e0bb9f8e94524 (not independently downloaded).

Independent read-only review found no Critical or Important implementation issues and requested direct non-reentry and positive-cap controls. Final tested13d5 adds both tests without runtime changes. Reviewer inspected the additions and found them sufficient; reviewer did not independently compile. No local Rust SDK was present; all compilation/test claims refer to CI.

Evidence JSON files in this directory are copied from the downloaded, hash-verified final artifact. NDJSON slices remain in that artifact. Historical negative lineage and previous qualifications remain in their original directories.
