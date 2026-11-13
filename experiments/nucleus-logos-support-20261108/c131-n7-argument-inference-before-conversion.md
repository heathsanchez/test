# C131: original N7 source argument inference is the standard-budget blocker

Status: **WARRANTED_BOUNDED diagnostic on C105-derived surrogate**. No
checker semantic/budget change, no standard-budget closure. 2026-11-14 NZDT.

## Native authority

- Frozen unchanged upstream Arena 196-case archive artifact `11272848230`;
  original `good/perf/magma-list-pair-n7.ndjson` SHA256
  `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.
- [Green C131 source-native Actions run #43487064962](https://github.com/heathsanchez/test/actions/runs/43487064962),
  isolated source branch `research/nucleus-c125-c105-surrogate-ci-20261114`,
  remote commit `4a1d151c82fac0535aea3c5a51d207c005bff9e1`.
- [Uploaded C131 source receipt #14067024323](https://github.com/heathsanchez/test/actions/runs/43487064962/artifacts/14067024323),
  artifact ZIP SHA256
  `3715497f752373fad39f72dec10b3c2d6d2861eb7047ff04444bcba1cf631b8c`.
- Actual `check_with_formation(Expr8804, domain(Expr8753))` of frozen AST
  `Expr8805=App(Expr8753,Expr8804)`. Observer enabled/disabled verdict and
  stdout identical. Seven source receipt parser tests pass. Same two flags:
  `NUCLEUS_EXPERIMENTAL_RELEVANCE=1`,
  `NUCLEUS_EXPERIMENTAL_DEMAND_MAJOR=1`.

| Actual source gate | Standard 65,536 | Diagnostic 14,155,776 |
| --- | --- | --- |
| Argument Expr8804 `infer_in` | UNKNOWN `unresolved-qualified-recursor-heads` | PROVEN `application-type-instantiation` |
| Inferred actual type | **Unavailable** | `Term(Closure Expr11, EnvFrame 3399708, levels [])` |
| Expected domain | `Term(Closure Expr6, EnvFrame 64530, levels [])` | same |
| Independent conversion | **Not attempted** | PROVEN `guarded-relational-conversion` |
| Argument inference outer charge | 191 | 191 |
| N7 overall | UNKNOWN | ACCEPT |

**Corrected diagnosis:** C130 had shown the *argument checking* obligation
UNKNOWN/PROVEN, but could not distinguish inference from conversion. C131
proves it is **inference itself** that fails at standard budget. The earlier
C130 report's proposed conversion optimization is superseded by this more
precise diagnostic, not by a repair. Equal outer charge does not bound the
work of internal trials.

## Preserved negative result

The first run [#43486587836](https://github.com/heathsanchez/test/actions/runs/43486587836)
compiled and passed C126–C130 but marked C131 red because its *observer*
incorrectly required a conversion receipt even when inference was UNKNOWN.
The parser was corrected to preserve an inference-only UNKNOWN, explicitly
tested, then run #43487064962 went green. No verdict changes, no admission.

## Next decisive C132 experiment

Record **argument judgment outcomes** of all actual source `Expr::App`
dependencies 8700–8804 under both budgets, cross-check each pair against
the immutable N7 source AST, and find the earliest divergent nested argument
or function-result inference under Expr8804. A failed recursor replay may
then be examined only under that owner and exact source frame. No generic
`UNKNOWN -> PROVEN` rule, enlarged budget, or floating cache authority.

Exact historical C124/C125b source lineage remains separate and not
reconstructed by this C105-descendant probe. The six original valid UNKNOWN
cases remain open at standard budget; a semantic repair must replay forged
controls and protected 403-case matrix before promotion.
