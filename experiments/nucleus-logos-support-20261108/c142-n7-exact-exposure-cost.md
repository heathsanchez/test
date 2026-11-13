# C142: 12.76 million evaluator head steps in exact N7 high-budget producer

**WARRANTED_BOUNDED**: source-native read-only C105-derived diagnostic surrogate; neither original standard-budget N7 acceptance nor the unavailable C124/C125b checker. Native [run #43500083665](https://github.com/heathsanchez/test/actions/runs/43500083665) green, artifact ID `14072543941`, artifact ZIP SHA256 `f759faba7d72eb2ac0e60ce22131d4d36cb5c5e1a0979db1a1f8e41487f7a59c`. Local C142 source commit `e1ce682`, remote compiled source commit `5ac0207378d8b85c18f44936abfa910373d39400`. Frozen unchanged source N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Diagnostic observer ON/OFF stdout and verdict identical at both budgets; native source build and 18 Python parser tests green.

Only exact `Expr8799@Env0@Levels[]`, same authority `386`, `Transparency::Reducible`, no pending, projection-preserving cache misses are counted. The meter increments on actual `expose_uncached_internal_with_pending` evaluator head iterations, including nested calls. It observes rather than changes the recursor and cache rules.

| Exact exposure | Allowance | Head steps | Qualified recursor calls | Replay-key work | Exposed value / cache |
| --- | ---: | ---: | ---: | ---: | --- |
| Low preliminary #1 | 507 | 480 | 0 | 0 | PROVEN stuck `Const147A5`; not cached |
| Low preliminary #2 | 507 | 495 | 0 | 0 | PROVEN stuck `Const147A5`; not cached |
| Low earlier producer | 65,250 | **63,908** | 0 | 0 | PROVEN stuck `Const147A5`; not cached |
| Low later C140-scoped retry | 65,250 | **60,444** | 0 | 0 | PROVEN stuck `Const147A5`; not cached |
| High preliminary #1 / #2 | 507 | 480 / 495 | 0 | 0 | PROVEN stuck `Const147A5`; not cached |
| High earlier completed producer | 14,155,490 | **12,761,384** | 0 | 0 | PROVEN `Const169A0`; published, then hit by scoped cheap-right |

`exposure_fuel` was `None` both before and after each exact exposure, so the table is **metered evaluator head-loop work**, not a measurement of decremented shared owner fuel or Arena-wide total cycles. Each exposure nevertheless had the separately observed local `budget` parameter. Original N7 outcomes remain UNKNOWN at 65,536 and 262,144, also UNKNOWN at 8,388,608, and ACCEPT at 14,155,776 **on this surrogate and these flags**.

**Rejected narrower hypothesis:** making the second standard-budget exact exposure a cache hit by simply recovering one prior 60,444-step attempt cannot supply the missing 12.76-million-step completed normal form. The cache correctly excludes the stuck low result. One low retry duplicates work, but that alone is far too small to close the gap. No new proof rule, cross-frame quotient or high-budget transplant is justified.

**Smallest next discriminating experiment (C143):** within the high source-qualified producer, distinguish repeated exact source subcalls from large numbers of genuinely different captured environments, with bounded instrumentation (e.g. exact-key hit/revisit counts and a top source-head census, explicitly separating an `ExprId`-only aggregate from full closure equality). If exact repeated *completed* subresults dominate, develop verified source-qualified reuse; if most work is unique, inspect evaluator reduction order and preserve continuation/progress instead. Then prove/check preservation under 65,536/262,144 and protected 403/403, forged controls, full original 196, Mathlib. Six original valid UNKNOWNs remain.

Lineage C133→C134→C135→C136→C137→C138→C139→C140→C141→C142.
