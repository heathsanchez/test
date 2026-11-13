# C137: exact second-capture deferred conversion worklist (observer only)

Status: **WARRANTED_BOUNDED** for C105-derived surrogate; not a C124/C125b or complete Nucleus acceptance result.

Native GitHub Actions [run 43493320641](https://github.com/heathsanchez/test/actions/runs/43493320641) passed, artifact ID `14070037779`, artifact ZIP SHA256 `d56ef7901cff6fd56679de3db222223ff26cfc40fe91a4de3ad7a3e48c9f8d9d`. Frozen source `good/perf/magma-list-pair-n7.ndjson` SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Standard checker budget 65,536; separate high diagnostic 14,155,776. Experimental checker flags unchanged.

The second source-captured conversion owner compares `Expr110@Env66182@Levels[(18, Succ(Zero))]` with `Expr1@Env66180@Levels[(2, Zero)]`. The initial positive comparison is **not** a proof of the full conversion: it enqueues three deferred obligations. The C137 owner-scoped trace retains exact term, environment, universe substitution, depth, pending count, and residual fuel.

| Work pop | Deferred left | Deferred right | Standard, 65,536 | High, 14,155,776 |
| --- | --- | --- | --- | --- |
| 0 | Expr110, Env66182, level 18→Succ(Zero) | Expr1, Env66180, level 2→Zero | remaining 65,264; pending 0 | remaining 14,155,504; pending 0 |
| 1 | Expr1, Env66182, level 18→Succ(Zero) | Expr624, Env0, empty levels | remaining 65,260; pending 2 | remaining 14,155,500; pending 2 |
| 2 | Expr1, Env66182, level 18→Succ(Zero) | Expr8799, Env0, empty levels | remaining 65,255; pending 1; **owner UNKNOWN** | remaining 14,155,495; pending 1; proceeds |
| 3 | Expr6, Env66182, level 18→Succ(Zero) | Expr620, Env0, empty levels | **not reached** | remaining 14,155,490; pending 0; owner PROVEN |

**Consequence:** the first discriminating residual is the second deferred equality, not the initial positive comparison. No cross-capture or cross-level equivalence may be assumed. The experiment did not establish why pop 2 becomes UNKNOWN with standard fuel, nor an optimization that makes it PROVEN. Next smallest experiment: record conversion route and actual failure stage for precisely pop 2, retaining its captured identities; do not alter judgments, resource budget or cache authority.

Source lineage: C133 distinct captured environments → C134 same qualified recursor fallback at both budgets → C135 no expensive high-budget one-step recursor trial → C136 positive initial comparison with deferred work → C137 worklist-localized first non-completed equality. Retain all older C126–C136 negative results; they constrain remedies.
