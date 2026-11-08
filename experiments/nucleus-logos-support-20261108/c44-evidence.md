# Nucleus C44 exact source forwarding experiment

Status: **REJECTED as a six-UNKNOWN closure mechanism; CANDIDATE only as an isolated local optimization.** Not selected for the independent kernel.

## Frozen boundary

- Reconstructed source from selected C37 and qualified C38/C39, followed by C40–C43 experimental patches. The patch is relative to the reconstructed C43 source.
- Previous GitHub research parent: `7b7cd834fcaca9e4a8fa28426ec77dcd2ed1804d`.
- Experiment patch SHA-256: `383e81c6768ff0eaeb8f9c27808b0575c96ffcf2362a58c55c4fc153064d4fa2`.
- Native release build: `cargo build --locked --release --features diagnostics --bin metatron-kernel` (Rust/Cargo 1.99.1 toolchain in local environment).
- Frozen selection: 24 `NUCLEUS_EXPERIMENTAL_*` flags from C39 `base/flags.json`, plus `NUCLEUS_DIAGNOSTIC_C38_EARLY_TYPED_SPINE=1`; C44 enabled only in intervention arm with `NUCLEUS_DIAGNOSTIC_C44_SOURCE_FORWARDING=1`.
- All six tests were the unchanged original `good/perf/*.ndjson`, no input preprocessing or test replacement, at the existing 262,144-step standard allowance.

## Hypothesis, separator and observations

Hypothesis: repeated exact immutable environment/BVar forwarding chains waste enough checked reduction work to account for the remaining failures. A source-only forwarding cache might save that work without reusing a completed or partial recursor result.

C44 remembers sparse checkpoints on a traversed sequence of exact captured `BVar` bindings only after reaching non-`BVar` source syntax. It does not memoize a Value or infer a constructor. Keys include exact captured closure and environment identity. An opt-in flag prevents changes to the selected path.

Red/green test: a 90-binding source chain required more than four exposure steps before C44; after its initial full traversal it completed in four steps. A distinct captured source did not inherit the cached constructor; the sparse retention test required <= 16 checkpoints and prevented caching trivial one-binding chains. Both source-chain tests passed under diagnostics. The full-map cache variant was also exercised, then superseded because of overhead.

Native opt-in regression: `cargo test --locked --release --features diagnostics` with the selected flags plus C44 passed **577 tests, 0 failed, 18 ignored** across 45 test-result groups. This is not the protected Arena verdict corpus.

| Frozen original | SHA-256 | C44 sparse exit | Verdict | Largest printed C44 hit count |
| --- | --- | --- | --- | --- |
| `magma-list-pair-n7` | `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35` | 2 | UNKNOWN | 8 |
| `magma-list-pair-n21` | `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84` | 2 | UNKNOWN | 512 |
| `magma-list-deep-n21` | `b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526` | 2 | UNKNOWN | 2048 |
| `magma-list-deep-n36` | `6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac` | 2 | UNKNOWN | no hit line |
| `fueled-chain` | `e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a` | 2 | UNKNOWN | 2048 |
| `grind-ring-5` | `e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f` | 2 | UNKNOWN | 32768 |

Note that printed hit counts are powers-of-two telemetry checkpoints, *not* total hits. The same source/run with C44 disabled returned UNKNOWN on every unchanged original. The earlier full-map intervention returned UNKNOWN for five and timed out for `grind-ring-5` (110-second cap). No ACCEPT was achieved by the cache family.

## Structured residual and next decision

The attached *Rigorous Breakthrough Stack* requires diagnosing the missing mechanism before further iteration and prunes non-moving variants. C44 establishes a **causal local optimization** but cannot explain a terminal proof result; R3 (exact binder redundancy) is not a sufficient root cause. Do not promote C44 as a solver. Treat it as a negative law for future search: reducing exact environment forwarding alone does not close any of six under the standard budget.

The higher-leverage experiment should distinguish resource exhaustion (R2) from representational loss (R6/R8) *at the earliest irrecoverable deferred projection or checked-recursor major*, using the existing shared work owner and original source. In the smallest proof `magma-list-pair-n7`, isolate the first `NameId(66)` recursor/`PProd` receiver for which a small-budget exposure remains neutral but a larger diagnostic exposure returns a source-certified constructor. Compare a single resumable demand graph retaining owner, captured environment and source path against the existing worklist; require unchanged proof verdict, work consumption and forged controls. No completed constructor can be accepted without checking the original registered iota rule.

**Trust boundary:** The unchanged six remain UNKNOWN; there is no full protected 403-case regression for opt-in C44; earlier C38 protected 403/403 and C39 CI are not evidence of C44 protected coverage. Never qualify or merge C44 on the strength of the local unit test or native suite alone.
