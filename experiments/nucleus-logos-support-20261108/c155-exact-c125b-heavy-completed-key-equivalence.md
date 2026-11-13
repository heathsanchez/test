# C155: all 407 expensive completed N7 nonleaf calls have distinct exact keys

**WARRANTED_BOUNDED negative: the observed 407 high-cost completed nonleaf exposure calls do not offer exact full-call memoization.** On recovered exact C125b `d8be1443f2f1352634aaf333a282f32e7ec8a719`, C155 added only opt-in `#[cfg(feature="diagnostics")]` observation of the *actual* `CachedExposureKey` (`AuthorityId`, complete captured `Closure` including environment and levels, `Transparency`, preserve-stuck-projection policy, and complete pending `Vec<Closure>`). It retained the exact input/result for each completed nonleaf call with at least 65,536 measured evaluator-head visits, compared keys using `Eq` after hash-indexing (never declared a hash collision equal), and computed an overlap-adjusted upper envelope of work for any subsequent exact repeated completed calls. No value was reused and no kernel policy or budget was changed.

- [Source commit `0d19f77`](https://github.com/heathsanchez/test/commit/0d19f77ff7883c4f52358ccb27c43fe7f64360ad) on `research/nucleus-c155-expensive-exact-keys-20261114`.
- [Native Action #43519890128](https://github.com/heathsanchez/test/actions/runs/43519890128) **SUCCESS**; receipt artifact `14082118049` SHA256 `ab65fac6c4315755b936c4613d597b2310d7e1c296a2280c06f329df267cb99b`.
- Frozen original N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Standard 65,536 **UNKNOWN exit 2**; diagnostic 14,155,776 **ACCEPT exit 0** unchanged. Observer ON/OFF verdict/stdout and non-observer stderr byte-identical. Three SHA-pinned forged controls retain **exit 1/2/1**, all non-ACCEPT. **341 Rust tests pass, 0 fail, 17 ignored (39 suites)**. Full 196/403 and Mathlib not rerun.

## Native result

| Exact high producer, original `Expr8799@Env0` | Value |
| --- | ---: |
| Completed nonleaf calls with >=65,536 evaluator heads | **407** |
| Unique full existing-cache keys | **407** |
| Repeats of a previously completed full key in this costly subset | **0** |
| Conflicting results for repeated keys | **0** (vacuous; there were no repeats) |
| Sum of overlapping repeated head intervals | **0** |
| Maximum disjoint head work available from those exact repeats | **0** |

At standard budget the same >=65,536-head class is empty, as the two long source producers each stop below this threshold (C154 maxima 63,692 and 60,352). This does **not** establish the absence of smaller exact repeats; C154 already counted 50,495 existing-cache hits in the high producer. It establishes the absence of exact input equivalence among **these 407 completed expensive nonleaf calls**, at the unchanged source and diagnostic budget. No high-budget result may be treated as a low-budget certificate.

## Decision / next experiment

**REJECT** adding cache capacity or memoizing complete *identical* input calls as the path to eliminate the 407 expensive intervals: they are all exact-key-distinct. Together C153–C155 close the cheap leaf-cache and high-cost exact nonleaf-cache hypotheses on N7. They do **not** prove that a different evaluation algorithm could not share or compress computation.

**C156 CANDIDATE:** within these same 407 original completed calls, identify whether any intentionally weaker *source-shape* equivalence classes recur when the captured environment differs; compare resulting values and dependency provenance without caching or assuming congruence. If there is a meaningful repeated family, prove a **support-qualified environment noninterference/transport law** (Distinguish/Quotient/Warrant) over immutable binder nodes, universe substitutions, complete pending spine, projection/recursor rules, and source witness before implementing sharing. If not, stop deriving memo keys and build an independently warranted graph/continuation reducer. Preserve all six original valid standard-budget UNKNOWNs, protected forged cases and source-native completeness boundaries. No general quotient rule has been proved by this experiment.
