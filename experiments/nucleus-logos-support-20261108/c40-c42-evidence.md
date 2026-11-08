# C40–C42 — exact source argument and stuck recursor diagnosis (8 November 2026)

Status: **WARRANTED_BOUNDED diagnostic observations; REJECTED as six-case closure.** No production checker or soundness claim is promoted. All original six valid source inputs remain **UNKNOWN** at the selected 262,144 judgment-step limit.

## Authority and reconstruction

- Base: C39 [commit](https://github.com/heathsanchez/test/commit/fc6e7f6a2257fec51abf84d764038b0a5b9454df), [successful run #42465168281](https://github.com/heathsanchez/test/actions/runs/42465168281), artifact 13610449997 (ZIP SHA-256 `29d91933a12d8c1244314b7e1bf0087e4bb8dc187205266a9bd4cff629f98c0f`).
- Locally reconstructed from C37 qualifying source tar SHA-256 `bb64f47470f950f78e7fe4c659fbcb2a75d72e96831430ec1eb3562c55175152` + the branch's C38 and C39 zero-fuzz patches.
- This branch's `c40-c42-source-capture.patch` applies with `patch --fuzz=0 -p1 -d metatron-kernel` after C38/C39. Patch SHA-256 `be8ad19e7d938984efa32838299511cbd5893180941ef3ab886bc01808325ff7`.
- Rust 1.99.1; `cargo build --locked --release --features diagnostics` PASSED. Local diagnostic binary SHA-256 `cb6397b7c26f9bff66e38f1fb36a6d7241d296c3aee044ef1115dfefd00be290`.
- The C40/C42 observer flags are OFF unless explicitly set. C41 retries the ordinary independent converter, again OFF by default. All six source hashes below were checked against exact frozen Arena originals. No full protected 403-case qualification has been run on this C40–C42 patch; C38's earlier 403/403 receipt is not transferable to this candidate.

| Original proof | SHA-256 | C40 original verdict |
| --- | --- | --- |
| magma-list-pair-n7 | abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35 | UNKNOWN |
| magma-list-pair-n21 | b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84 | UNKNOWN |
| magma-list-deep-n21 | b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526 | UNKNOWN |
| magma-list-deep-n36 | 6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac | UNKNOWN |
| grind-ring-5 | e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f | UNKNOWN |
| fueled-chain | e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a | UNKNOWN |

## Observations, not acceptance claims

**C40, source argument capture.** Under the selected 24 NUCLEUS flags, C38 early full typed spine + C39 failure classification, added `NUCLEUS_DIAGNOSTIC_C40_SOURCE_ARGS=1`. In n7 and n21 a `Decidable.rec` same-head congruence trial fails at its fourth argument's *right exact-source inference* (local budget 776). Separately, an `Eq` data-congruence trial at root depth zero fails comparing a captured `Bool.true` constructor with an explicit source `Decidable.decide` expression. These are failed optional trial premises, not proven logically necessary bottlenecks of the top-level original theorem.

**C41, cheapest discriminator for the root Eq trial.** With `NUCLEUS_DIAGNOSTIC_C41_RETRY_TYPED_DATA=1`, re-ran the exact existing converter on the n7 data pair with local allowance 8,192, 32,768 and 262,144, plus original 512. At all four allowances `proved=false` and unchanged original verdict UNKNOWN. This rejects the narrow “raise this conversion sublimit” hypothesis, without claiming no other normalization strategy can close it. The extra retry is OFF by default.

**C42, reduction shape.** With `NUCLEUS_DIAGNOSTIC_C42_STUCK_EXPOSURE=1`, independently exposed the captured sides under full transparency at 8,192 and 262,144 steps. LHS becomes a zero-arity `Bool.true` constructor; RHS remains `Decidable.rec` neutral (five arguments). The recursor's last major argument is a captured `BVar(2)` and exposing that major likewise leaves a five-argument `Decidable.rec` neutral under both allowances. No constructor rule is earned by these observations. This is concrete evidence why that *particular* equality cannot be established by simply granting more fuel or equating the neutral to true.

The older C31 source trace independently observed repeated deferred `PProd` projection transitions inside checked recursor replay. Together they support a **candidate** for a source-certified demand-driven major/projection continuation. They do **not** prove that one continuation repairs any complete original.

## Next cheapest decisive experiment

Instrument an exact **one-step recursor-major transition certificate** (constructor/projection/source/environment/owner before and after) for n7 and one other case, testing whether the repeated same source projections are semantically stable and can be resumed under a retained shared owner without using the expected output. Only implement a new evaluation step after the trace distinguishes (a) genuinely new source work, (b) repeat of a completed stable value and (c) still-open neutral. The successful control must ACCEPT the unchanged original under standard budget and preserve forged-proof REJECTs, followed by full protected 403 regression; otherwise retain the negative as UNKNOWN/REJECTED.

Source: the attached `Rigorous_Breakthrough_Stack_v1.1` — exploit existing operations, demand a minimal discriminator, verify before promoting, preserve failures and lineage. It supplies method, **not a Lean-specific theorem or reduction license**.
