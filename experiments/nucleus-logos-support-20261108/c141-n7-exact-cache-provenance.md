# C141: earlier certified exposure publication explains high-budget N7 cache hit

Status **WARRANTED_BOUNDED** for read-only native C105-derived research surrogate. **Not** acceptance of N7 under standard budget or qualification of unavailable historical C124/C125b checker.

Native green [run 43498724590](https://github.com/heathsanchez/test/actions/runs/43498724590), artifact ID `14073332568`, artifact ZIP SHA256 `8e48f768ae5f6f37d0aaa0f2594c23894e3908bdf1b3f4e0aa9d1bf7358a7a0b`. Native source commit `c0764453c084b22ad4801ff6caed09c1a139233d`; local observer commit `c539ae3`. Exact frozen original Arena N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Original `65,536` vs diagnostic `14,155,776` budgets, and both experimental flags, unchanged. Observer ON/OFF stdout and verdict identical. 17 local Python parser tests and native CI all green.

All receipts here are for **the same exact `CachedExposureKey`**: source `Expr8799@Env0@Levels[]`, authority `386`, `Transparency::Reducible`, `preserve_stuck_projection=true`, zero pending closures. The key itself also includes the complete captured closure (not just those displayed fields) and is checked for exact equality. A matching hash is not used as an equality proof.

| Event sequence | Standard `65,536` | Diagnostic `14,155,776` |
| --- | --- | --- |
| Two preliminary low-allowance calls (`507`) | miss → proven exposed stuck neutral `Const147A5` → **publication skipped**, twice | same, twice |
| First call at comparison allowance (`65,250` / `14,155,490`) | miss → exposed stuck `Const147A5` → **publication skipped** | miss → completed `Const169A0` → **published to cache** |
| Later C140 scoped cheap-right exposure at same allowance | **miss** → recomputes `Const147A5` → publication skipped | **hit** → returns completed `Const169A0` (zero metered head steps) |
| Subsequent call at allowance `56` | no corresponding cache hit in traced path | **hit** → retains completed `Const169A0` |
| Overall original N7 input in this surrogate replay | exit 2 / UNKNOWN | exit 0 / ACCEPT |

**C140 hypothesis confirmed:** the high run's zero-work right-hand exposure came from an earlier exact-key positive cache publication. The low run did not cache its non-normal recursor: the guard that excludes an unexposed recursor major correctly prevented unsafe reuse. High outcome is backed by prior high-budget completion **within that run**; it cannot be transported into the standard-budget run.

**New highest-leverage residual:** determine how much *duplicated work* the earlier and later standard-budget exact-key misses perform, and whether any certified, immutable, source-qualified completed **subresults** or a sound bounded continuation can be reused to complete the remaining reduction within 65,536. The smallest C142 experiment is an observer-only per-call cost-and-prefix lineage meter for these two exact misses, including independently charged fuel and repeated subcall identities. This would distinguish a safe reuse opportunity from an intrinsically >65,536-work reduction. Do not cache stuck values, equate differing neutral heads, or loosen fuel/recursor checks.

Lineage C133→C134→C135→C136→C137→C138→C139→C140→C141. Six original valid UNKNOWNs remain at the standard budget; neither complete Mathlib nor protected forged regression was rerun by this narrow diagnostic workflow.
