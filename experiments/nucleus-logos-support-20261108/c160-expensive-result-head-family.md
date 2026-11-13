# C160: all 407 distinct expensive N7 results have the same Decidable.isTrue constructor head

**WARRANTED_BOUNDED observational source-native result, not a constructor theorem or completeness fix.** On the frozen original `magma-list-pair-n7`, the 407 exact completed calls identified by C155 and distinguished by C156–C159 include **406 represented `Value`s that differ from the first under strict Rust equality**; pairwise distinctness among all 407 was not measured. Yet their *observable top-level value head family* is identical: `Const NameId(146)` with zero universe arguments and **two term arguments**. The frozen source dictionary and earlier C112 source-qualified rule analysis identify `NameId(146)` as `Decidable.isTrue`. This is a more promising *candidate* for a guarded, typed constructor-selection law than sharing whole results. It is **not** permission to infer `isTrue` in an unobserved context or reuse the varying proposition/proof fields.

## Source, lineage, native authority

- Exact recovered independent C125b source `d8be1443f2f1352634aaf333a282f32e7ec8a719`, frozen original N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`, original Arena 196-case artifact ZIP SHA256 `f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`.
- C159 protected contextual-binding test [source `4656be1`](https://github.com/heathsanchez/test/commit/4656be1c6d12fa2415d657f27a0bd9b0838f5c1b), remains passing, so this observation cannot justify a lossy full-value cache.
- C160 observer source [commit `7b471a7`](https://github.com/heathsanchez/test/commit/7b471a7a353b66078258bf01b3c3e876298bb054), final native receipt-parser fix [`6b2f63e`](https://github.com/heathsanchez/test/commit/6b2f63e53110c94a3e758a23b9dc458185fee602), [Action #43525181684](https://github.com/heathsanchez/test/actions/runs/43525181684) **SUCCESS**. Retained artifact `nucleus-c160-result-head-family-receipt` ID `14085310489`, GitHub digest `sha256:b3a7ef4788c331489c8c4de484246d41e963409dcae0b6a604b8094ba1748068`.
- Original C160 [run #43524753049](https://github.com/heathsanchez/test/actions/runs/43524753049) **FAILURE, diagnostic harness only**: the receipt gate erroneously expected one per-input marker while the instrument emitted one marker per original exposure attempt. It had already passed source build, unchanged verdict/forgery controls and C151–C159 gates; its parser failed on four correct low-budget markers (two 507-grant and two 65,055-grant). C160 follow-up `6b2f63e` fixed only the marker multiplicity expectation, not source evaluator semantics.

## Exact native classification

| Classification on source producer `ExprId 8799 @ Env0` | Standard 65,536 | Diagnostic 14,155,776 |
| --- | ---: | ---: |
| Original N7 exit | 2 UNKNOWN | 0 ACCEPT |
| Completed expensive (>=65,536 evaluator heads) full-cache-key-distinct calls | 0 | **407** |
| Value-head-shape groups among these calls | 0 | **1** |
| Largest value-head-shape group | 0 | **407** |
| Group head | — | `Const146`, universes 0, spine arguments 2 |
| Identical head-shape members whose full Value differs from first | — | **406** |
| Other head-shape classes | 0 | **0** |

The low run issued four producer attempts (507 twice, 65,055 twice) and accumulated no completed calls at the expensive threshold. The high run issued three (507 twice, 14,155,295 once); exactly the long high attempt supplied the 407 expensive completed results. The new C160 classification is read-only and records only `Value`-head names/arity, not source-bound proposition or proof contents; it is **deliberately many-to-one**.

The native Action confirmed C160 observer **ON/OFF byte-for-byte non-observer stderr, stdout and verdict parity**, the same frozen N7 low UNKNOWN/high ACCEPT, three pinned adversarial controls exits **1/2/1 (none ACCEPT)**, and full Rust diagnostics tests **342 passed / 0 failed / 17 ignored (40 suites)**. It also repeated C151–C159 gates. No full frozen original 196-case corpus, protected 403 matrix or Mathlib replay was performed; none of the original six valid standard-budget UNKNOWNs is closed.

## Decision: target source-checked constructor induction, not value memoization

**PROMOTE as WARRANTED_BOUNDED:** in this one high-budget execution, all 407 completed expensive N7 outputs have the same source-identified `Decidable.isTrue` head while their exact environments, immutable binding nodes and represented fields differ.

**REJECT:** transporting `isTrue` merely because it appeared 407 times; treating same head and arity as equality of the complete `Decidable` values; reusing a proof field from a different proposition; or allowing a constructor head through source-only syntax equality. The exact original source proof still needs to establish the proposition and constructor for each new context.

**Next smallest decisive experiment, C161 CANDIDATE:** choose two adjacent expensive N7 `Decidable.isTrue` outputs with *different* captured binders. Recover the exact registered `Decidable.rec` constructor/RHS transition and the argument types around those two cases; attempt a source-checkable **parameterized step**: under explicit verified context and inductive premises, the next constructor is `isTrue`, carrying its *own original proof closure*. First test that proposition/binder changes make the step REFUSE without a proof, and that a native checked positive accepts. If and only if a general source-certified step exists, benchmark replacing the expensive chain under unchanged 65,536 fuel and forged-proof gates. Otherwise retain UNKNOWN and reject the proposed induction. A finite head histogram is not an induction proof.

**Mission:** all original six valid 65,536-step UNKNOWNs, entire original 196/403 protected corpus, independently qualified full Mathlib and proof-level soundness remain OPEN; C160 moves the *candidate target*, not their status.
