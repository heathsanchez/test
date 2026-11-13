# C159: protect captured-binding distinction while transporting a genuinely shared binding

**WARRANTED_BOUNDED POSITIVE SAFETY REGRESSION, NOT AN N7 PERFORMANCE FIX.** Native Rust regression `machine::c159_captured_binding_distinction_tests::identical_bvar_source_distinguishes_values_but_transports_a_shared_binding` passes on source recovered from the exact original independent C125b Nucleus checker. It protects the source/environment distinction exposed by C156–C158; it does not establish that all irrelevant environment bindings may be erased or that a new quotient is sound.

Source [commit `4656be1`](https://github.com/heathsanchez/test/commit/4656be1c6d12fa2415d657f27a0bd9b0838f5c1b) on isolated branch `research/nucleus-c159-binding-distinction-regression-20261114`; native [GitHub Action #43523063450](https://github.com/heathsanchez/test/actions/runs/43523063450) **SUCCESS**; retained artifact `nucleus-c159-binding-distinction-receipt` ID `14083772042`, GitHub digest `sha256:7e747a32e082c435d8a4d5bfc06742254b4d43e35b2b8f671f29ceea739e935c`. Recovered original C125b `d8be1443f2f1352634aaf333a282f32e7ec8a719`; original frozen Arena N7 `sha256:abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.

## What the new test actually establishes

1. Three `EnvFrame` configurations use the identical original source expression `BVar(2)` and the exact existing exposure cache. The first and third have different immutable captured bindings holding `NatLit 1` and `NatLit 2`: exact evaluation returns **different** values, not a false cache hit.
2. The first and second configurations extend distinct outer frames but share the *same immutable captured binding node* at the queried index. Exact evaluation returns `NatLit 1` for both, including repeated use of the first configuration; the distinct irrelevant outer frames do not change the observed result in this single native test.
3. The test explicitly checks that the shared-binding pair has identical binding-node identity at `lookup_with_node_id(2)`, while the two distinct-value configurations do not. It therefore distinguishes **source syntax**, **immutable binding origin**, **whole environment identity**, and **actual result**.

The source file checksum declared by the native Action is `sha256:c0d8d88999ec966da692b9e94e58ca6f73338ae086749101538233935f7e0ce3` for `metatron-kernel/src/machine.rs` (C159 includes the opt-in diagnostic hooks inherited from C151–C158). The production decision logic was not changed by C159; the new case is `#[cfg(test)]`.

## Frozen protection and limits

- Filtered C159 Rust regression: **1 passed, 0 failed**.
- Full native `cargo test --features diagnostics`: **342 passed, 0 failed, 17 ignored, 40 test suites** (aggregate of unfiltered test results in job log).
- Same frozen source `magma-list-pair-n7`: **UNKNOWN exit 2 at 65,536**; **ACCEPT exit 0 at 14,155,776** diagnostic steps. It did not move the completeness boundary.
- Three pinned adversarial NDJSON controls: **exit 1, exit 2, exit 1**, with no forged ACCEPT.
- C151–C158 read-only probes and their ON/OFF outcome-parity gates also passed in the C159 Action.
- Not rerun: entire original 196-case corpus, the previously protected 403-case matrix, or Mathlib. No universal cross-environment transport result and no performance improvement has been proved.

**Decision:** promote the observed C159 regression to **REUSABLE (bounded, native-tested safety test)**; retain C156–C158's rejection of syntax-only quotients and expensive binding-forwarder shortcuts. The six original valid low-budget UNKNOWNs are still **OPEN**: `fueled-chain`, `grind-ring-5`, `magma-list-deep-n36`, `magma-list-deep-n21`, `magma-list-pair-n7`, `magma-list-pair-n21`.

**C160 candidate, the smallest useful next experiment:** identify *one* exact typed-relevance or recursor-major evaluator operation that makes N7 smaller **without merging distinct captured environments**. First specify the guarded transform; demonstrate a native positive and a forged/incorrect-major negative; run the frozen N7 at unchanged 65,536 steps and the three adversarial controls. If and only if it helps safely, broaden to all six UNKNOWNs, the 403 regression, and source-qualified Mathlib. If it does not, retain the negative and reject the candidate. This supersedes C158's provisional C159-algorithmic naming, since C159 was used for the protective test.
