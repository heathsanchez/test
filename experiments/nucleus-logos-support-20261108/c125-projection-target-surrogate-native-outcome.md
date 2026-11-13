# C125 projection target: native surrogate outcome

Status: **WARRANTED_BOUNDED observation; Nucleus residual UNKNOWN** (2026-11-14 NZ).

## Exact scope and lineage

- Source: unchanged `magma-list-pair-n21.ndjson`, SHA256
  `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.
- Independent Rust instrument: C105-descended diagnostic-only research source,
  **not** the unrecovered original C124 branch. Published CI source branch:
  `heathsanchez/test`, `research/nucleus-c125-c105-surrogate-ci-20261114`.
- Authoritative initial native execution: GitHub Actions run
  [#43477795606](https://github.com/heathsanchez/test/actions/runs/43477795606),
  source-native probe and all three forged controls passed, although the
  subsequent Rust suite failed on CI test-thread stack exhaustion.
- After setting `RUST_MIN_STACK=67108864`, run
  [#43478152170](https://github.com/heathsanchez/test/actions/runs/43478152170)
  again passed the native probe and all three forged controls, and proceeded
  through 67 unit tests and several integration modules; the suite then
  exposed the known intentionally-red positive
  `distinct_proof_arguments_of_same_checked_proposition_are_convertible`
  because `NUCLEUS_EXPERIMENTAL_RELEVANCE` was unset. This is the established
  opt-in proof-irrelevance gate; its dedicated qualification workflow
  (`nucleus-checked-relevance-signature-v1.yml`) explicitly checks OFF red,
  ON green and data negatives. C125 changes no conversion rule.
- **Final qualified run:** [#43478924553](https://github.com/heathsanchez/test/actions/runs/43478924553),
  commit `21e737d3e8aa5bc3cd0552b090dd1c17863d7aab`, **SUCCESS**.
  Source-native observation and all three forged controls passed; the
  diagnostic Rust test suite passed **340 tests across 39 suite results**, with
  **0 failed and 17 ignored**. For the Rust suite **only**, the established
  `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` flag was enabled; the native probe used
  its independently pinned environment. The receipt artifact has id
  `14063683014` (ZIP SHA256
  `27be9086ba8367f3069297f082b0c26cbe8d62a1762ecc2ac73b20dd3c763b45`).

## Observed invariant, with exact native counters

The frozen source gives 80 nested projection-major calls costing 26,132
source-work units (20 owned by 32,578-start unit; 60 by 65,157-start unit).
All 80 terminal frames, captured binding-node identities, and full debug
payload fingerprints differ. Every observed target is a closure with captured
`ExprId(11)` and zero level arguments, reached by two source-BVar closure
links through terminal Expr 7198. The source-preserving observer leaves
the N21 verdict `UNKNOWN` and operations unchanged:

| Counter | Unchanged native result |
| --- | ---: |
| Declarations | 276 |
| Inductive signatures | 89 |
| Type judgments | 247 |
| Conversions | 44,957 |

The three pinned forged controls remained `REJECT`, `UNKNOWN`, `REJECT`
(exit codes 1, 2, 1), respectively, with source/observer verdict and
operation parity. A negative control that stays `UNKNOWN` is **not** claimed
to be `REJECT`.

## Consequence, not overclaim

This independently reproduces C124's 80/26,132 projection population on a
separately recovered C105 lineage, and rules out **direct identity-keyed
reuse** of these captured projection operands. Distinct frame IDs, binding
node IDs and debug fingerprints **do not prove semantic inequality**.
Conversely, sharing source Expr IDs `1`, `811`, or `7198`, or even the same
captured payload Expr `11`, does **not** authorize reuse across differing
binders, environments or levels.

The standard-budget N21 result is still `UNKNOWN`; the six original valid
UNKNOWNs are not closed by this observation. The cheapest genuinely decisive
next experiment is a typed, binder- and level-parametric continuation
certificate for the actual captured projection payload, tested against
source identity, changed captures, fuel, complete native positive cases, and
the protected forged non-ACCEPT matrix. Without that certificate, preserve
separate evaluation and UNKNOWN rather than silently memoizing.

The C124 parent chain remains unrecoverable from the available thin bundles
until the C106–C108 missing commit objects are recovered; this report does
not supersede that lineage gap.
