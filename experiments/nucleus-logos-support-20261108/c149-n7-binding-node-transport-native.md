# C149: one-step immutable used-binding-node transport — native bounded gate

**WARRANTED_BOUNDED native regression, NOT a formal transport theorem or production cache.**
Recovered source commit [`474d1a4219f48aeadb3a4e3cbbbfbe8fe9e2cc8f`](https://github.com/heathsanchez/test/commit/474d1a4219f48aeadb3a4e3cbbbfbe8fe9e2cc8f) on the **C105-descendant surrogate**, not the independently recovered original C124/C125b checker. [Corrected source-native original N7 workflow #43514141790](https://github.com/heathsanchez/test/actions/runs/43514141790) **SUCCESS**: **341 Rust tests passed / 0 failed / 17 ignored, 40 suites**, plus all prior exact-source C126–C148 diagnostics and source-verdict parity. Native artifact `14080686683`, ZIP SHA256 `546e83740446dcdedb283c8a298bfccd55581de89148694b66a3bd3f6da8c4ff`. Independent same-commit [C125/three-forgery companion #43514141352](https://github.com/heathsanchez/test/actions/runs/43514141352) **SUCCESS**, likewise 341/0/17. Original unchanged N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.

## Tested boundary

The regression `same_used_binding_node_ignores_distinct_unused_outer_frames` builds an authentic `Expr::BVar(1)` evaluator step, two different immutable `EnvFrame`s which look through different unused top bindings to the **same underlying lower used node**, and a control which instead uses a **different** lower node. Their `lookup_with_node_id(1)` values are explicitly compared. With identical source BVar, evaluator authority, transparency and an identical **nonempty pending argument**, the two shared-node cases return the same proven neutral exposure; the different-node control returns a different proven value. A second same-node case captures an immutable Nat-literal closure, preserving the same proven numeric value despite distinct unused outer frames.

These are finite native examples of a local transport fact. Neither the test nor the implementation establishes a universal theorem about every `EnvBinding`, recursive evaluation, universe substitution, cyclic state, proof authority, visit-history, cost model or completed `Exposure` replay. No cache key, result, kernel proof rule, verdict or budget policy was changed. C148's 4,086 extra **observed** exact-pending-context collisions remain diagnostic opportunities rather than verified fuel savings.

## Negative and corrected lineage

- [Initial source commit `8706305`](https://github.com/heathsanchez/test/commit/8706305eafcbd1b5c58a7c213d7a3af7dc6415c4) had a test-only missing `BigNat` import, producing Rust `E0433`; the [initial companion workflow #43513921858](https://github.com/heathsanchez/test/actions/runs/43513921858) **FAILED** to compile. The [initial full workflow #43513921891](https://github.com/heathsanchez/test/actions/runs/43513921891) subsequently **FAILED** at its C145 native regression stage. These runs are **SUPERSEDED for qualification**, not erased.
- [Corrected commit `474d1a4`](https://github.com/heathsanchez/test/commit/474d1a4219f48aeadb3a4e3cbbbfbe8fe9e2cc8f) imports the type in the test module without changing checker semantics. Both native gates are green at that exact commit.

## Decision

**What changed:** a same-node one-step equality candidate has a source-native test and negative identity control. **What did not:** the original 65,536-step N7 remains UNKNOWN, its high-budget diagnostic remains ACCEPT, six original valid standard-budget UNKNOWNs remain open, and full Mathlib/production qualification is not established by this test.

**Highest leverage next:** the separately preserved *byte-identical* C124/C125b history in the self-contained Git archive (`sha256:a31a9fc837ced439e2b9f82022f5fc145c66de9db473678299a6ce0f0c352f73`) must be requalified natively and used as the reference for any eventual work-saving change. C150 source qualification does this without transporting diagnostic-only C148 measurements or optimistic quotient keys.
