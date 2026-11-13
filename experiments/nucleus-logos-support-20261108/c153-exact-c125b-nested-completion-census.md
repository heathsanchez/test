# C153: recovered exact C125b shows completed *leaf* exposure calls cannot alone close N7

**WARRANTED_BOUNDED, source-qualified diagnostic census; no new standard-budget ACCEPT.** The same recovered C125b core as C150–C152 (`d8be1443f2f1352634aaf333a282f32e7ec8a719`) was instrumented with read-only `#[cfg(feature="diagnostics")]` invocation accounting at the `expose_internal_with_pending` boundary, solely inside the C151 frozen source `Expr8799@Env0@Levels[]` miss. The native code is [commit `e367efe`](https://github.com/heathsanchez/test/commit/e367efe8917888eff0d057cb7cb2922b598b924f) on `research/nucleus-c153-nested-completion-20261114`; [Action #43518391139](https://github.com/heathsanchez/test/actions/runs/43518391139) **SUCCESS**; receipt artifact `14082555718` has SHA256 `f9f715650adff2f2e43867215291134313053c6f65524fa75270db43ab9919a3`.

The immutable original Arena N7 file has SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35` (196-input source archive SHA256 `f6cd590db7f6fb92b8d1b3ca87231d4b0f521f085d73f93abd005f5caaff86d2`). Original low `65,536` outcome **UNKNOWN exit 2** and high `14,155,776` **ACCEPT exit 0** unchanged. C151/C152 diagnostics remain parity-checked; C153 ON/OFF preserves verdict, stdout and other stderr byte-for-byte. Three frozen SHA-checked forged controls remain **1 / 2 / 1**, never ACCEPT. **341 Rust tests passed, 0 failed, 17 ignored, 39 test suites.** This does not rerun the source-native 196/403 or Mathlib.

## What actually completed in the long N7 producer

| Native exact C125b local allowance | Nested calls | Proven calls | Leaf calls | Proven/cache-eligible leaves | Disjoint leaf head work | Largest leaf head work |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low preliminary 507 (first) | 12 | 11 | 4 | 3 | 12 | 8 |
| Low preliminary 507 (second) | 10 | 9 | 4 | 4 | 2 | 2 |
| Low long 65,055 (first) | 3,997 | 3,990 | 1,452 | 1,450 | 7,583 | 8 |
| Low long 65,055 (second) | 3,818 | 3,811 | 1,396 | 1,394 | 7,591 | 8 |
| **High long 14,155,295** | **845,943** | **845,943** | **308,127** | **308,127** | **1,708,344** | **8** |

A *leaf* is an invocation of the existing exposure wrapper that makes no nested invocation of that wrapper before returning. Its evaluator-head interval is thus disjoint from every other leaf interval. It may still contain its own uncached evaluation loop; counts include that work. “Potentially cacheable” matches the existing rule for proven results without witness recording and without unresolved mutable recursor-major neutral. It does **not** mean the leaf was actually cached or hit, or that separately saved work would be zero-cost.

C152 independently measured **12,761,384** head-loop entries inside this exact high completed producer. The **1,708,344** disjoint leaf head-loop entries are **13.387%** of that total; **11,053,040** other head entries, **86.613%**, remain outside leaves. Hypothetically eliminating every leaf's head work would still leave **more than 168 times** the standard 65,536 count (these counters are evaluator heads, **not** the Arena's shared fuel units). This is a quantitative rejection of *completed leaf-call caching alone* as the N7 closure mechanism; it is **not** a formal impossibility bound on graph sharing, larger completed nonleaf subcalls, or a different evaluator.

## Decision / residual

- **WARRANTED_BOUNDED:** The expensive high producer makes 845,943 nested wrapper calls; completed leaves are individually tiny (at most 8 heads) and collectively account for only 13.4% of the measured work. Original verdicts and protected forged controls were unchanged by read-only instrumentation.
- **REJECT as sufficient:** Memoizing completed leaf exposures alone. It cannot account for the core's far larger application/beta/binding loop.
- **UNKNOWN:** Whether larger *completed nonleaf call intervals* repeat with exactly the same complete authority, source closure/environment, universe levels, pending spine, mode, and needed dynamic context. A nonleaf interval includes children: overlapping repeats cannot simply be added as independent savings. Any cache implementation needs proof of transport, preservation of budget/UNKNOWN and forged-proof safety.
- **C154 candidate, cheapest decisive follow-up:** Source-lock the same high producer and rank **completed nonleaf exposure intervals by disjoint charged head work**, with bounded exact-key equality on repeated expensive parents (not mere hashes or interior head repeats). Compute an optimistic, overlap-adjusted head-work ceiling for completed full-call reuse before altering the kernel. If too small, stop adjusting the completed-exposure cache and pursue a source-owning, certified graph/continuation reducer whose operational sharing survives the beta/binder chain. Keep all six original 65,536 valid UNKNOWNs and full Mathlib as explicit residuals.
