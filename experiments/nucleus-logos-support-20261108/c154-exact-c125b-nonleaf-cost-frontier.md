# C154: expensive completed nonleaf exposure intervals exist, but overlap

**WARRANTED_BOUNDED source-qualified read-only census, not a cache-transport proof.** Native [source commit `f3294cd`](https://github.com/heathsanchez/test/commit/f3294cdc2d73772d79a6ad04645579d5830ff90b) is the recovered exact C125b (`d8be1443f2f1352634aaf333a282f32e7ec8a719`) plus the prior C151–C153 diagnostics and a C154 metering-only `#[cfg(feature="diagnostics")]` observer. [Action #43519119051](https://github.com/heathsanchez/test/actions/runs/43519119051) **SUCCESS**, receipt artifact `14082805854`, ZIP digest SHA256 `fecb0873d09b4196906362303bceada045169b2ba21ba5851466a3e29c9bd01f`. Same immutable original N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; original 65,536 **UNKNOWN 2**, diagnostic 14,155,776 **ACCEPT 0**. Instrumentation ON/OFF stdout, verdict and other stderr identical. Three SHA-pinned forgeries remain **1/2/1**, non-ACCEPT; **341 Rust tests passed, zero failed, 17 ignored (39 suites)**. Does not qualify full 196/403 or Mathlib.

## Exact original source `Expr8799@Env0@Levels[]` nonleaf intervals

| Allowance / outcome | Completed nonleaf | Max one nonleaf heads | Nonleaf intervals >=64 heads | >=1,024 heads | >=65,536 heads | Existing cache hits within producer |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low first 507 (stuck) | 8 of 8 | 458 | 4 | 0 | 0 | 0 |
| Low second 507 (stuck) | 5 of 6 | 473 | 5 | 0 | 0 | 3 |
| Low first 65,055 (stuck) | 2,540 of 2,545 | 63,692 | 928 | 120 | 0 | 306 |
| Low second 65,055 (stuck) | 2,417 of 2,422 | 60,352 | 886 | 116 | 0 | 246 |
| **High 14,155,295 (completed)** | **537,816 of 537,816** | **12,761,350** | **193,279** | **20,007** | **407** | **50,495** |

These are the existing `expose_internal_with_pending` wrapper's nested, *completed* nonleaf intervals inside a source-locked C151 exposure miss; `max_head_work` and bin thresholds include descendant evaluator heads, so **overlapping intervals must never be summed to claim saved work**. The 50,495 existing cache hits prove that some exact completed source-input reuse is already served (not that every large interval is repeated). Whether any of the 407 expensive intervals have a prior equivalent completed *full* key is **UNKNOWN**. The high maximum 12,761,350 heads is almost the entire C152 producer (12,761,384) and illustrates why additive call-size tallies are invalid.

**Decision:** C153 ruled out leaf-call caching alone; C154 preserves a narrow **CANDIDATE** for large completed *nonleaf* replay, pending exact-key equality and an overlap-corrected savings ceiling. It has not established any missing cache hit or algorithmic speedup. **C155 smallest decisive test:** track only the >65,536-head completed nonleaf calls in this one high producer; retain full `(authority, closure, transparency, preserve-stuck-projection, pending)` keys (with universe/binding provenance carried by each closure), compare exact equality and outcomes, and compute a maximum nonoverlapping set of repeated completed intervals. Never infer key identity from a hash or reuse a high-budget result as a standard-budget certificate. If no meaningful exact repeats, pivot away from tuning the completed-exposure cache toward typed graph/continuation reduction. All six original good standard-budget UNKNOWNs remain open.
