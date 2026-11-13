# C140: exact right-hand exposure does zero metered head work at high budget

Status: **WARRANTED_BOUNDED** for read-only observation on the C105-derived native surrogate. Not a proof of cache provenance, not the unavailable historical C124/C125b checker, and not standard-budget N7 acceptance.

Native green [run 43497170776](https://github.com/heathsanchez/test/actions/runs/43497170776), artifact ID `14073201056`, artifact ZIP SHA256 `5ccdba759a811711774b55ccca5a950e7da92c2a0d50755e8baaec290a5e3c10`. Source commit `587aedf`, remote source/workflow commit `2963efd70d9ef7fce732dadfeb7837d04157e080`. Frozen unchanged `good/perf/magma-list-pair-n7.ndjson` SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.

The scoped observer counts evaluator head steps, qualified recursor-result calls, and replay-key work **within** the exact cheap `expose_for_conversion` of the second deferred pair's right-hand closure `Expr8799@Env0@Levels[]`. It does not count previous exposures or cache population. Observer ON and OFF preserve stdout/verdict at both unchanged budgets. Native CI and 16 local parser checks green.

| Exact right-hand exposure | Standard `65,536` | Diagnostic `14,155,776` |
| --- | ---: | ---: |
| Allowance at call | 65,250 | 14,155,490 |
| Judgment | PROVEN | PROVEN |
| Exposed head | Neutral Const `NameId147`, arity 5 | Neutral Const `NameId169`, arity 0 |
| Metered evaluator head steps | **60,444** | **0** |
| Qualified recursor-result calls within scope | 0 | 0 |
| Replay-key work within scope | 0 | 0 |

**Distinction:** the two PROVEN exposed values are different: standard remains at a qualified recursor, while high returns the matching constant. Neither observation warrants equating their heads. High spends no *scoped head-loop work* at this call, while standard spends 60,444 and remains stuck. The zero-work high result **suggests**, but does not prove, an earlier source-qualified completed exposure-cache hit; other unmetered return routes are not excluded.

**Cheapest decisive next experiment (C141):** observe exact `CachedExposureKey` hit/miss, positive-value retention, and earlier producer at both budgets for this same closure, including authority, level substitution, transparency, pending exposures, and projection-preservation flag. Only then consider sound intra-run exact-source reuse or continuation. Never reuse high-budget results to claim low-budget closure. The original six standard-budget valid UNKNOWNs remain. Lineage C133→C134→C135→C136→C137→C138→C139→C140.
