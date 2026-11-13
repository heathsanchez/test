# C162: even source-required N7 proposition captures have 407 distinct immutable binding projections

**WARRANTED_BOUNDED negative result.** The original N7 `Decidable.isTrue` proposition expressions from C161 have small free-de-Bruijn-variable supports: `ExprId(9)` depends only on outer `BVar(3)`; `ExprId(7218)` depends only on outer `BVar(4)` and `BVar(5)` after accounting for its two `forallE` binders. These source supports were independently traversed from the frozen exact N7 NDJSON. Nevertheless, the 407 completed expensive proposition closures still form **407 distinct groups** under a *conservative exact projection* onto those required immutable binding-node identities plus the original universe substitution. No group repeats. A source-free-variable projection does not yield a cheap exact-node reuse opportunity here.

## Source-pinned native evidence and rejected run

- Frozen C125b independent checker commit `d8be1443f2f1352634aaf333a282f32e7ec8a719`; N7 `good/perf/magma-list-pair-n7.ndjson` SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; original Arena 196-case input ZIP SHA256 `f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`.
- First [C162 run #43527387446](https://github.com/heathsanchez/test/actions/runs/43527387446) **FAILURE at compilation**: a missing positional argument in the new read-only diagnostic `eprintln!` format string. It produced no C162 result; frozen source and checksum gates passed. Retain as a tooling failure, not a negative checker verdict.
- Corrected observer-only code [commit `ec9e886`](https://github.com/heathsanchez/test/commit/ec9e88602114f123829925a3a28da0d4f196c0eb) on branch `research/nucleus-c162-proposition-binding-support-20261114`. [Native C162 Action #43527549425](https://github.com/heathsanchez/test/actions/runs/43527549425) **SUCCESS**, job `132236967104`, artifact `nucleus-c162-proposition-capture-support-receipt` ID `14086191726`, digest `sha256:baa39e815fe273747db97611309276481058467694dcb2a75dabe37ae5e958ee`.
- The workflow recomputes free-variable support by independently traversing frozen N7 expressions (applications, `forallE`, lambdas, lets, projections; correct binder-depth subtraction) and asserts the two index sets before accepting any native observer counts. No source patch changes conversion, checking or memoization.

## Exact high-budget and low-budget results

| N7 frozen result | Standard 65,536 | Diagnostic 14,155,776 |
| --- | ---: | ---: |
| Original exit/verdict | 2 / UNKNOWN | 0 / ACCEPT |
| Completed C155 expensive exact-cache-key-distinct calls | 0 | **407** |
| Classified `Decidable.isTrue` proposition closures | 0 | **407** |
| Missing required captured binding or unexpected source | 0 | **0** |
| Distinct `(source, levels, required binding node IDs)` groups | 0 | **407** |
| Repeated projected groups | 0 | **0** |
| Largest projected group | 0 | **1** |
| Source `ExprId(9)` (`BVar(3)`): members/groups | 0/0 | **57/57** |
| Source `ExprId(7218)` (support `BVar(4), BVar(5)`): members/groups | 0/0 | **350/350** |

Every required *position* has a distinct immutable node in its group: source 9/position 3 has 57 distinct nodes; source 7218/position 4 has 350 distinct nodes; source 7218/position 5 has 350 distinct nodes. The low-budget original four producer attempts (507, 507, 65,055, 65,055 steps) again have no completed >=65,536-step calls; the high-budget three attempts (507, 507, 14,155,295 steps) report all 407 in the final attempt.

The native gate passed C162 ON/OFF byte-identical original non-observer stderr/stdout/verdict, C151–C161 gates, pinned three adversarial outcomes exits **1/2/1 (none ACCEPT)**, and native Rust tests **343 passed / 0 failed / 17 ignored across 77 test-result reports**. The full 196 original-case corpus, protected 403 matrix, and complete Mathlib were **not** rerun. The original six valid standard-budget UNKNOWNs remain OPEN.

## Epistemic decision and next target

- **PROMOTE bounded observation:** source-syntax environment support can be computed precisely for these two expressions, but the 407 actual captured *required binding nodes* still do not repeat.
- **REJECT** a source-only closure quotient, exact required-*node*-identity memoization as an effective accelerator on these 407 cases, and any unsupported environment weakening. Distinct nodes may still carry definitionally equal values, but equality of those values was **not measured**; node identity is also a handle for typed context origin and cannot simply be removed.
- **NEXT CANDIDATE:** stop inventing ever-coarser cache keys. Investigate a *typed, source-checked constructor-reduction/recursor recurrence* for the specific `Decidable.rec` branch (on frozen **N7**, `NameId(147)` / `isTrue NameId(146)` / RHS `ExprId(531)`). First produce one source-qualified adjacent-step witness that keeps its own proposition parameter and proof field and tests refusal on swapped binder/proposition or forged proof. Only then attempt a semantics-preserving step induction or conversion optimization within the unchanged 65,536 fuel. If it cannot be justified, retain UNKNOWN.

These observations characterize expensive completed internal reductions of **one** unchanged high-budget N7 input. They do not prove the same mechanism explains all six original UNKNOWNs, do not license a cache change and do not certify independent soundness or full Mathlib acceptance.
