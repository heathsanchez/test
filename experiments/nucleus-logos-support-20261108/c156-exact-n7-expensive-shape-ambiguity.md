# C156: 407 costly exact-key-distinct calls collapse to one BVar source shape, but their stored Values differ

**WARRANTED_BOUNDED observational finding; NO semantic quotient licensed.** On recovered exact C125b `d8be1443f2f1352634aaf333a282f32e7ec8a719`, the same 407 high-cost completed N7 calls from C155 were grouped *without caching* by `(source ExprId, complete level substitution, transparency, preserve-projection policy, ordered pending (ExprId, level substitution))`. This deliberately **drops captured environments** to test whether a source-shape quotient could even be considered. The grouping is NOT a valid cache key. Also computed a weaker source-expression/pending-length grouping as a cross-check.

Native source [commit `b14e1a9`](https://github.com/heathsanchez/test/commit/b14e1a9a38d47bcba2e3cf84cad3f260036d40b2), [Action #43520640924](https://github.com/heathsanchez/test/actions/runs/43520640924) **SUCCESS**, receipt artifact `14082148754` SHA256 `727813a4e9baf851a00d0f3be342b4539a45d233f8464b53f707ad62f6d0c05b`. Frozen original N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; 65,536 original UNKNOWN/exit2; 14,155,776 diagnostic ACCEPT/exit0; instrumented ON/OFF behavior and other stderr byte-identical; three forged proof exits 1/2/1, none ACCEPT; 341 Rust passed/0 failed/17 ignored (39 suites). No checking change, full 196/403 not rerun.

## Exact high producer (`Expr8799@Env0`), threshold >=65,536 inner evaluator heads

| Property | Observed |
| --- | ---: |
| C155 unique full captured-environment keys | **407** |
| C156 intentionally environment-omitting *source-shape* groups | **1** |
| Largest source-shape group | **407** |
| Source ExprId and pending count | **`ExprId 11`, pending 0** |
| Frozen source ExprId 11 syntax | **`BVar(2)`** (`{"bvar":2,"ie":11}` at original input line 26) |
| Same-shape members whose returned `Value` differs from first under strict Rust equality | **406** |
| Coarse `(source ExprId, pending length)` groups | **1** |

Low original 65,536 executions contain no completed nonleaf calls reaching the >=65,536-head selection threshold, so C156 has zero such rows at low budget. In the high run, the shape class is a maximally strong collision despite zero full-key repeats. Its 406 strict result differences are differences of **source-native represented `Value`**, possibly containing captured closures; they **do not alone prove logical/observational inequivalence or false results**. Conversely, same syntax and same successful high-run verdict provide no permission to transport a result to a different binding environment. The missing information is precisely the `BVar(2)` binding provenance and any further dependencies of that bound closure.

**Decision:** REJECT the syntax-only source-shape class as a cache key; preserve C156 as a useful adversarial family for proving the *limits* of quotienting captured contexts. **C157 cheapest decisive test:** group the same 407 exact calls by the *actual immutable binding node* reached by lexical index `2` in each full captured environment; compare node identity and strict results, with possible closure/binding-chain provenance. If all 407 differ at the binding-node level, no first-step binder-identity memo can close them. If some repeat, audit whether the same binding-node value under different outer frames supports a narrowly proved transport lemma (as in the finite C149 witness); do not infer full evaluation congruence from binding identity alone. The larger project remains six valid standard-budget UNKNOWNs, protected 403, Mathlib, independent soundness.
