# C96: major-cost source binding and short-chain audit (13 November 2026)

**State:** WARRANTED_BOUNDED read-only native diagnostics. Both untouched
source-qualified original Arena inputs still return UNKNOWN. No source
authority or acceptance algorithm was modified; a full external forged-proof
corpus or completeness promotion is **not** claimed.

## Source authority and reproducibility

- Parent C95 tree `392358bec43bae7dba9f85209e81d9958056c326` and its
  disjoint owner-phase evidence. C96 adds only Rust
  `#[cfg(feature="diagnostics")]` source-binding histograms and a native
  source-hash-pinned Python probe. No recursor rule, fuel, cache inference or
  parser/metadata change.
- Upstream Arena `6c2d82164f1a2b1ac94aee62290fe78a3c3853fb`; exact
  bytes SHA256 n7 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`,
  n21 `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.
- Compiled with `cargo build --locked --features diagnostics`; diagnostic
  binary SHA256
  `d51cd685bed367cd3ec5f0141ecf652707890c7005736238ff830926e00f65e8`.
  Runtime base flags `NUCLEUS_EXPERIMENTAL_RELEVANCE=1`,
  `NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1`,
  `METATRON_KERNEL_DIAGNOSTICS=1`. Observer toggles
  `NUCLEUS_C96_MAJOR_TRACE=1` only.
- Run `python3 -B
  experiments/nucleus-logos-support-20261108/probe_c96_major_lineage.py
  metatron-kernel/target/debug/metatron-kernel
  /path/to/arena/_build/tests/perf/magma-list-pair-n7.ndjson` (also n21).
  It asserts source SHA, same original UNKNOWN exit2, identical operation
  counters ON/OFF, and that aggregated observed major charges never exceed
  the charged owner. Initial missing-receipt test was RED before adding C96;
  both unmodified originals were GREEN after adding it.
- C95's disjoint phase-conservation native probes remain GREEN for both
  originals on the C96 binary with unchanged charged totals, verdicts and
  operations. The earlier C94/C95 evidence is neither overwritten nor
  superseded by a new acceptance claim.
- Qualified `NUCLEUS_EXPERIMENTAL_RELEVANCE=1
  NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1 cargo test --release --locked`
  completed exit 0 across active unit/integration tests, retaining explicit
  historical ignores. This is not an external 403-case corpus recheck.

## Dynamic source binding groups in the exhausting owner

Each group classifies the **actual immutable binder value** read by the
major source BVar. `kind=0` means an `EnvBinding::Closure` with the indicated
*bound* ExprId. This grouping is for cost diagnosis, **not an equivalence
claim**: the bound closures retain distinct captured EnvFrames, universes
and source arguments.

| Original and caller recursor | Bound ExprId | Major exposures | Charge | Produced nested qualified recursor | Exposure UNKNOWNs | BVar-closure links: total / max |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| n7 `Decidable.rec` (`NameId(147)`) | 11 (`BVar(2)`) | 206 | 26,811 | 183 | 0 | 438 / 4 |
| n7 `Bool.rec` (`NameId(170)`) | 1 (`BVar(0)`) | 28 | 10,158 | 0 | 0 | 84 / 3 |
| n7 `Decidable.rec` (final small group) | 1 | 1 | 1 | 1 | 0 | 2 / 2 |
| n21 `Decidable.rec` | 11 | 197 | 38,984 | 158 | 0 | 406 / 4 |
| n21 `Bool.rec` | 1 | 8 | 2,456 | 0 | 0 | 24 / 3 |
| n21 `Decidable.rec` (final small group) | 1 | 1 | 1 | 1 | 0 | 2 / 2 |

For n7 all grouped major exposures total **36,970 charged units across 235
demands**. For n21 they total **41,441 across 206 demands**. These match the
independently recorded C95 major-exposure totals exactly. Neither owner
returned a major-exposure UNKNOWN in its sampled charged worklist: each
exposure completed and most `Decidable.rec` exposures generated another
registered recursor before the **enclosing** worklist eventually exhausted
its shared budget.

The actual direct lexical BVar closure chain is only **at most four links**
in either original. The dynamic walk has a 4096-step diagnostic hard cap;
no cap was reached. Therefore a shortcut targeting only long BVar-to-closure
chains cannot explain tens of thousands of charged major-exposure steps in
these two owners. It must lie **after** the short capture lookup, in
source-term reduction and recursor continuation work. Observing the same
ExprId(11) repeatedly is not an exact closure cache hit or an authorized
branch choice.

## High-leverage residual and further decisive experiment

Under the *same* exact captured major closures and shared fuel, instrument
the internal exposure transition mix after the short BVar chain: source
delta heads, beta/zeta, matched registered constructor recursors, native Nat
steps and unresolved/unknown exits, with a bounded per-definition cost
histogram. Pin dynamic source heads back to the original NDJSON name table.
The C29 association with `Nat.decidableBallLT` is still a candidate; C96
does not yet prove it is the expensive dynamic caller. Only if such a trace
isolates a source-semantic repeated computation should a single charged
algorithmic rewrite be attempted, followed by original/forged control replays
at identical input and allowance.

The old C85/C88/C89 exact cache and alias negatives remain relevant and
unreversed. The six standard-budget valid UNKNOWNs and source-qualified full
Mathlib acceptance remain UNKNOWN. C96's 65,536-step C91 boundary is not
directly comparable to C89's frozen 262,144/24-flag source boundary.
