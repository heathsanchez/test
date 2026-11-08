# Nucleus C47 inner-work accounting and source-hotspot discriminator

Status: **WARRANTED BOUNDED diagnostic observation; CANDIDATE structural cause; six original standard-budget proofs still UNKNOWN.** No inference rule, constructor selection, type-checking semantics, input byte or selected checker has been changed.

## Setup

Source is the C44 isolated research reconstruction, with the C47 diagnostics-only patch applied. Its four accounting hooks record source exposure-loop transitions, replay-work reservations, checked recursor-worklist steps, and conversion worklist pairs. Counters reset at the exact final `countermodel` judgment (`ExprId(8837)`), selected by `NUCLEUS_DIAGNOSTIC_C47_PROFILE_EXPR=8837`; sampled source-expression frequencies increment every 64th exposure transition. None of the counters influences a judgment, budget, cache, or rule.

Run with frozen C39 selected 24 flags, C38 observer, C44 source-forwarding OFF, the unchanged `magma-list-pair-n7.ndjson` with SHA-256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`, compiled `--locked --release --features diagnostics`, and diagnostic explicit allowance per root judgment. The same instrumented binary was used in every arm.

## Exact quantitative discriminator

| Stated diagnostic allowance | Verdict | Outer steps consumed | Source exposure-loop transitions | Replay reserved units | Recursor-worklist steps | Conversion pairs |
| ---: | --- | ---: | ---: | ---: | ---: | ---: |
| 262,144 | UNKNOWN | 457 | 828,695 | 26,350 | 4,666 | 665 |
| 13,631,488 | UNKNOWN | 457 | 42,944,430 | 997,311 | 245,875 | 665 |
| 14,155,776 | ACCEPT | 512 | 12,774,343 | 746 | 34 | 994 |

The near-threshold failed arm makes **3.36× more source exposure transitions** and **over 7,000× more worklist steps** than the high-budget accepted arm. Yet it stops at the *same* outer-step position (457) as standard budget. The accepted arm advances to 512 outer steps and reaches more conversion pairs downstream. The declared 14-million allowance is therefore **not** 14 million outer judgment steps consumed. It gates inner work which is accounted separately by the evaluator. Its causal optimization potential is a discontinuous resolution/fallback transition, not a blanket reduction of a 14-million-step outer derivation.

These are counts from the named hooks, **not** a complete disjoint operation-cost accounting: nested source transitions may occur during replay, and other runtime work is omitted. The counters are non-semantic observers; a high-budget ACCEPT does not qualify the standard-budget original.

## Earliest failing source and source families

- Diagnostic source census at standard allowance: 275 source declarations preceding final `countermodel` reached without assumed-boundary failure; exactly one failed scalar boundary at declaration index 275, stage `definition.value`, reason `application-function-type`, body `ExprId(8837)`, type `ExprId(8731)`.
- Root application trace: the failing ancestor is application `ExprId(8835)`, function `ExprId(8805)`, argument `ExprId(8834)`, whose function type is UNKNOWN with residual `unresolved-qualified-recursor-heads`; the caller still has 261,687 outer steps. This is a diagnostic fault site, not proof that all failed speculative branches were necessary.
- The most sampled exposure-source identifiers in every regime include `ExprId(1)` (`BVar(0)`), `ExprId(6)` (`BVar(1)`), `ExprId(11)` (`BVar(2)`), and `ExprId(4677)` (the exact `PProd` projection of `BVar(0)`) with enclosing lambda sources `4678` and `4679`. This independently joins the earlier C31 deferred `PProd` projection/recursor-major finding and C42 captured `Decidable.rec` observation. Sampling every 64 steps is only a frequency approximation; do not infer exact hot-closure equivalence from the shared `ExprId` alone, because the environments can differ.

## Controls and repair decision

The local baseline and active observer both produced the unchanged UNKNOWN at standard allowance and the same high-budget ACCEPT. In C45, C44 sparse forwarding ON/OFF had the same sampled 13.63M UNKNOWN / 14.16M ACCEPT boundary, replay-key suppression did not move the boundary enough to help standard, and each of 24 selected flags individually ablated gave UNKNOWN. These observations reject more exact-key or binder-forwarding knob sweeps as a sufficient fix.

The C47 readout patch applied with zero fuzz to the C44 reconstructed source and its Rust release diagnostic build succeeded. The selected-flag, diagnostics-feature native test suite passed **577 tests, 0 failed, 18 ignored** across 45 result groups. This checks local native regressions, not all 403 protected Arena cases.

After recompiling the instrumented production binary and disabling both C44 and the C47 profile trigger, all **six frozen originals** (`magma-list-pair-n7`, `magma-list-pair-n21`, `magma-list-deep-n21`, `magma-list-deep-n36`, `fueled-chain`, `grind-ring-5`) independently returned exit 2 / UNKNOWN under the selected flags. The observer did not silently promote any proof.

Additional previously qualified C29/C31 trace hooks were replayed at standard and 14,155,776 diagnostic allowance: the first **four** deferred `PProd` projection observations were byte-for-byte identical in source, environment and charged local work. The standard run then entered 286 further projected transitions (290 total observations) and 256 printed `NameId(66)` major steps; the successful high run printed only 4 projected transitions and 46 major steps. This is a *first visible branch divergence*, not yet a proof of which reduction causes it. C39/C40 congruence observers still showed the same captured `Decidable.rec` argument-3 inference failure and the `NameId(29)` data-argument-conversion failure in both regimes; therefore the high-budget path does not simply repair those speculative typed-congruence trials.

The live residual is **R4 observability resolved sufficiently to reveal an R2/R3/R8 inner evaluation cliff**. The strongest candidate is repeated work after a source recursor major or `PProd` receiver remains unresolved in a short-lived local grant. To prove it, capture the *first exact source-owned transition* that produces the constructor in the accepted high-allowance arm but fails in the standard arm, including its source expression, environment/captured binder identity, registered recursor rule, parent-and-local owners and fuel before/after. Then implement an opt-in, source-certified continuation or legal structural quotient which transports actual work across grants without granting constructor authority. Re-run frozen originals and protected forged-proof tests before promotion; check the full protected corpus only after a genuine standard-budget ACCEPT.

**Not achieved:** 0/6 standard-budget ACCEPT; no full C47 403-case protected qualification. The C47 patch is purely an observation instrument, not a repair.
