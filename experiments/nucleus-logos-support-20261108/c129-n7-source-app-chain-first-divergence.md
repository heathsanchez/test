# C129: exact-source application-chain divergence on N7

Status: **WARRANTED_BOUNDED diagnostic**, C105-derived surrogate; six original
standard-budget UNKNOWNs remain. 2026-11-14 NZDT.

## Source-native boundary

Frozen unchanged Arena N7 SHA256
`abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.
The diagnostic recorded real source App IDs 8700–8835 under up to three
binders; the parser cross-checked every `(app, fun, arg)` against the exact
NDJSON AST. The source checker ran with RELEVANCE + DEMAND_MAJOR on, at
65,536 and 14,155,776 steps. Observer-on/off exit codes and stdout agreed.
No semantic checker changes.

Native [green run #43484377090](https://github.com/heathsanchez/test/actions/runs/43484377090),
[receipt artifact](https://github.com/heathsanchez/test/actions/runs/43484377090/artifacts/14067291207),
ZIP SHA256 `3a123e0e963c5c657e4e629e368008074d9470ddb31fbb89524415887925916e`.
Isolated remote revision `b79b543158510bd2a7ecfe5e08e0d82a87e4072e`;
its Rust blob exactly matches local committed source (`652d821fbe3de863c1314119597118c23efa6784`).

## Exact comparison

| Native source-app observations | 65,536 | 14,155,776 |
| --- | ---: | ---: |
| Total observed source applications | 65 | 89 |
| Common source application identities | 65 | 65 |
| Common sites whose function-side Pi/type status differs | 1 | 1 |
| Distinct divergence site | Expr 8835: UNKNOWN | Expr 8835: PROVEN Pi |
| Preceding 64 source application heads | all PROVEN Pi | all PROVEN Pi |
| Application Expr 8805 function-side head (function Expr 8753) | PROVEN Pi | PROVEN Pi |
| Extra application sites visited only after successful outer 8835 | none | 24 |
| Overall N7 | UNKNOWN | ACCEPT |

The first changed observation is source `Expr 8835 = App(8805, 8834)`.
Critically `Expr 8805 = App(8753, 8804)` itself has a **proven function-side
Pi** at both budgets. This trace records the *function-side* head before the
argument check: it does **not** prove that Expr 8805's argument is accepted or
that the type of the *whole* Expr 8805 is proven at both budgets. In fact, the
outer expression reports that Expr 8805 has an UNKNOWN type at low budget.

The corrected run followed a red CI failure #43484158071 where a large Rust
file was truncated in transport. The recovered GitHub blob exactly matches
the local Rust source; the red run never tested source N7. Preserve this
failure as transfer lineage, not a kernel regression.

## C130 cheapest test

Instrument the genuine `check_with_formation` result for **argument Expr 8804
against the actual Pi domain inferred for function Expr 8753 in App Expr
8805**, at both endpoint budgets, recording judgment and caller-owned charge.
This distinguishes a budget-sensitive argument proof from a later fixed-Pi
substitution or beta-spine continuation; neither can be inferred from C129's
function-head-only observations.
