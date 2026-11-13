# C126–C127: original N7 source function-type head, C105-derived surrogate

Status: **WARRANTED_BOUNDED native diagnostic**; no standard-budget closure or
general checker optimization. Date: 2026-11-14 NZDT.

## Source and lineage

- Frozen upstream Arena artifact `11272848230`, ZIP SHA256
  `f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`.
- Original, unchanged `good/perf/magma-list-pair-n7.ndjson`, SHA256
  `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.
  Original AST `ExprId(8835) = App(ExprId(8805), ExprId(8834))` checked by
  the input validation script.
- Remote isolated branch `research/nucleus-c125-c105-surrogate-ci-20261114`,
  source revision `4a6c462620686c9f6c6648cef998150bb3e1dcc7`;
  [C126 green run](https://github.com/heathsanchez/test/actions/runs/43481556498)
  and [C127 green run](https://github.com/heathsanchez/test/actions/runs/43482343571).
  [C127 uploaded receipt](https://github.com/heathsanchez/test/actions/runs/43482343571/artifacts/14066455649)
  SHA256 `e87ab115ad061177483f11a75a46357cf2cbf9b50d25f24853a7d0512586f035`.
- **This is a C105-lineage surrogate.** Do not identify this with the separate
  exact-C124 C125b local commit `d8be1443f2f1352634aaf333a282f32e7ec8a719`.
  The latter's parent C124 `70eed42069fedd156231f82113eba2c43ea28804`
  is unavailable in this checkout; C106–C108 prerequisites are still missing.

## Original source-native result

Both runs set `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` and
`NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR=1`, with the original input, unchanged
checker rules and budgets. Each budget was executed with the read-only observer
both off and on; stdout and exit status agreed in all nine pairs. The observed
head is from actual `TypeChecker::infer_in` on source function `8805`, at
application `8835`, in context depth zero.

| Requested steps | Function-type head at Expr 8835 | Checker exit | Local outer charge |
| ---: | --- | --- | ---: |
| 65,536 | UNKNOWN, unresolved qualified recursor heads | UNKNOWN (2) | 203 |
| 131,072 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 262,144 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 524,288 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 1,048,576 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 2,097,152 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 4,194,304 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 8,388,608 | UNKNOWN, same reason | UNKNOWN (2) | 203 |
| 14,155,776 | PROVEN Pi head, `application-type-instantiation` | ACCEPT (0) | 203 |

The proof-relevance tracer produced 40 certificate lines at each budget. A
locally equal 203-step **outer** charge does **not** establish equal inner
evaluation work: deeper source-driven replay and conversion probes have their
own budget/owner mechanics. Neither a unique crossover value, an admissible
reuse key nor a standard-budget speedup is established here.

## Decision and next smallest experiment

The discrepancy is an exact-source, budget-dependent *function-type evidence*
boundary, not a generic missing Pi parser or need to admit a recursor by name.
At high budget the needed Pi becomes available from source-checked evaluation;
at lower budget the checker properly retains UNKNOWN. The high diagnostic
ACCEPT is not an Arena-standard ACCEPT. Six original valid standard-budget
UNKNOWNs remain open; this C126–C127 diagnostic did not rerun the original
196-case or protected 403-case matrices or forged-proof suite.

**C128 discriminator:** on exactly this source and both endpoint budgets, trace
actual nested `Decidable.rec` constructor-demand owners and RHS continuations:
their source heads, captured frame/levels/arguments, owner allowance, charge,
entry/completion/UNKNOWN status, and any *completed stable result repeated*
under an identical validated key. Seek one actually repeated source-checked
subresult that can be safely shared under a single accountable fuel owner.
If none exists, **reject cache reuse** and test structural source-recursor
evaluation instead. Never promote an unfinished major, an UNKNOWN, two
context-distinct captures, or the successful high-budget verdict to a proof.
Before a semantic change can be promoted, require a new standard-budget N7
ACCEPT, the unchanged six-case census, forged controls and 403-case regression.
