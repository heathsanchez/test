# C130: N7 first divergent source argument proof obligation

Status: **WARRANTED_BOUNDED diagnostic**, C105-lineage surrogate. Original
standard-budget N7 still UNKNOWN; no semantic checker change. 2026-11-14 NZDT.

## Authority

Unchanged original Arena N7 input SHA256
`abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`;
frozen upstream artifact `11272848230`. Source AST validates
`Expr 8805 = App(8753, 8804)`. Diagnostics `NUCLEUS_C130_APP_ARG`
read the *actual* `TypeChecker::check_with_formation` result for argument
Expr 8804 against the inferred Pi domain of function Expr 8753. The same
RELEVANCE and DEMAND_MAJOR flags were enabled at both budgets; observer ON
and OFF verdict/stdout matched. [C130 green run #43485274893](https://github.com/heathsanchez/test/actions/runs/43485274893),
[uploaded source receipt](https://github.com/heathsanchez/test/actions/runs/43485274893/artifacts/14065834929),
artifact ZIP SHA256 `7af77f7c9457b519c65bbedb3a996900220e3fce2fe8c61eaae539df1de59a67`.
Remote isolated revision `058c18417ad85548c27f0a138312a410bd537ec1`.
Verified full Rust source blob `c67b15878b944227ccefe00a241299c114715790`
equals the local committed file; no truncated-source transfer.

| Exact source observation | Standard 65,536 | Diagnostic 14,155,776 |
| --- | --- | --- |
| Function-side Pi of App 8805 | PROVEN | PROVEN |
| `check_with_formation(8804, domain(8753))` | UNKNOWN | PROVEN |
| Argument judgment | `unresolved-qualified-recursor-heads` | `guarded-relational-conversion` |
| Outer charge in App 8805, including argument | 202 | 202 |
| Type of function Expr 8805 at App 8835 | UNKNOWN | PROVEN Pi |
| N7 overall | UNKNOWN | ACCEPT |

The source-obligation result is the first verified *judgment* divergence;
the earlier C129 function-head-only trace does not independently prove that
argument 8804 passes. Equal outer charge says nothing about inner probe work.

## Next smallest C131 discriminator

At exactly the one `check_with_formation(8804, domain(8753))` call, record
the **source-inferred actual type**, exact expected type closure, captured
frame and universe levels, and the single `convert_with_policy_in_context`
result with caller depth and budget. Within the conversion, trace the first
consequential registered-recursor head mismatch on this same operation,
capturing exact source head, spine/major, phase and actual charged work.
The goal is a sound smaller source-checked conversion certificate or a
proven stable reusable completed result, *not* a heuristic replacement of
UNKNOWN with ACCEPT. A future semantic change must pass the original six
valid cases, frozen forged controls, full 403-case matrix, and the standard
65,536-step gate. Exact historical C124/C125b source remains unavailable here.
