# C145: exact N7 producer is overwhelmingly application–beta–binding traffic

**Status: WARRANTED_BOUNDED for exact-source C105-descendant surrogate only.** [Corrected native run #43506402408](https://github.com/heathsanchez/test/actions/runs/43506402408) completed **SUCCESS** at remote source commit [`476f833`](https://github.com/heathsanchez/test/commit/476f83357016e7df2c31200807b668a517a844fa). Source-locked N7 measurement step 26, the full Rust regression step 27, and artifact step 28 all passed; receipt artifact `14076857033`, ZIP SHA256 `db730075e7fc36813548f316bf456f8104608a0166068e12931ce9590bf11fbc`. The prior native [run 43504619782](https://github.com/heathsanchez/test/actions/runs/43504619782) had already passed the source-pinned census but **FAILED** the Rust suite in `distinct_proof_arguments_of_same_checked_proposition_are_convertible` (`rigid-value-constructor-mismatch`). That test is the expected negative control with `NUCLEUS_EXPERIMENTAL_RELEVANCE` unset; the failed workflow omitted the flag. Correction enables `NUCLEUS_EXPERIMENTAL_RELEVANCE=1 NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1`, as in the earlier source-qualified suite. Preserve the failed run and its artifact `14077000655` (ZIP SHA256 `efb7d790bcf938c2749c085418a456992df5afdf31dfb8b4390758b041713bca`) as diagnostic lineage. Separately, the original [C125 surrogate/three-forgery-control run 43504619882](https://github.com/heathsanchez/test/actions/runs/43504619882) completed successfully (artifact `14075567241`, ZIP SHA256 `91e0a76579180f9f90f16cfa7311cafbc791489ae735344c64991cc313059cc3`).

## Authority and measurement

Exact original Arena input `good/perf/magma-list-pair-n7.ndjson` SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`, same C105-descendant **surrogate**, not recovered C124/C125b source. C145 adds diagnostic-only Rust counters gated on exact `Expr8799@Env0@Levels[]`, `Reducible`, preserved projection and empty pending (runtime-observed authority `386`), plus a parser that rejects missing, forged or non-conserving records. Each original `Expr::` constructor is counted exactly once on entry to an evaluator head iteration, and each BVar visit is classified by the **actual immutable environment lookup**; no inference, normalization result, budget, recursor eligibility, cache admission or proof rule is modified. Instrumented and silent runs must match exit verdict and stdout, enforced by the native probe. Loop counts are **not** Arena cycles or shared owner fuel.

| Disjoint observed head kind | Low first exposure (65,250 available) | Low later exposure (65,250) | High completed producer (14,155,490) |
| --- | ---: | ---: | ---: |
| Application | 24,033 | 22,742 | **4,814,916** |
| Lambda with pending argument (beta) | 16,991 | 15,964 | **3,333,267** |
| Bound-variable lookup | 13,772 | 12,955 | **2,694,572** |
| Constant | 7,155 | 6,913 | 1,504,060 |
| Projection | 1,475 | 1,409 | 310,927 |
| Native literal head | 482 | 461 | 103,642 |
| Let / other / unapplied lambda | 0 | 0 | 0 |
| **Conserved total** | **63,908** | **60,444** | **12,761,384** |

| Actual BVar lookup result | Low first | Low later | High |
| --- | ---: | ---: | ---: |
| Captured closure | 13,268 | 12,491 | **2,590,933** |
| Native Nat | 504 | 464 | 103,639 |
| Free / neutral / unavailable | 0 | 0 | 0 |

The three-machine-action application/β/BVar subtotal is **10,842,755 / 12,761,384 = 84.965%** of high producer loops; the low first-exposure subtotal is 85.742%. These are *head action counts*, not measured marginal CPU time or proof-work savings. The 199.68× high/low work ratio does not imply an equivalent ratio in workload size, caching potential or Arena score.

## Interpretation and next experiment

**WARRANTED_BOUNDED:** the hot path is an application–beta–captured-binding spine, not primarily direct projection forcing (2.436% head steps) or qualified recursor invocations (C142 high exact producer recorded zero). C144's eight hot syntax IDs include BVar 0/1/2 and a projection under two lambdas; C143 proves source ExprId equality alone vastly overstates exact closure identity.

**C146 local candidate, not yet natively verified:** sample the three hot BVar sources under a complete, source-known *used-binding-node* fingerprint, preserving source ExprId, fixed evaluator authority/levels and the exact pending closure spine. Compare full-EnvFrame unique keys with only-for-observation projected binding-node keys. The expressions are known **before** reduction, unlike the rejected C6 predictive inference cache whose output syntax was not yet available. This is a discriminating census only; no transport of previous results, no cross-frame presumed equality. If projected repeats do not dramatically exceed exact repeats, reject simple lexical-support quotient and inspect repeated app/beta continuation instead. Any reuse must prove semantic adequacy in the presence of pending arguments, transparency, proof authority, cyclic source terms, unbounded recursion and projection obligations.

Lineage C141 → C142 → C143 → C144 → C145; C5/C6 rejected anticipatory type-result caching, C105 rejected terminal-BVar closure deduplication in N21. Six original valid standard-budget UNKNOWNs, full Mathlib and production selection remain OPEN.
