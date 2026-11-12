# C91: strict Arena gates; original-six residual retained

**State:** WARRANTED_BOUNDED native source qualification of six *new* Arena
cases; original six valid performance cases **UNKNOWN**; complete Mathlib
acceptance **UNKNOWN**. Do not collapse these different claims into one score.

## Authority and replay boundary

- Checker: `research/nucleus-context-warrant-20261113`, based on the independent
  C58 Nucleus source. `metatron-kernel/src/checker.rs` SHA-256 before commit:
  `8b009ff49a02c65a245dae86141b728bcd9fb3dc6db487d7ddb05ff4733f1306`.
- Arena: `leanprover/lean-kernel-arena` at
  `6c2d82164f1a2b1ac94aee62290fe78a3c3853fb`, generated using
  `uv run lka.py build-test ...`; exporter format 3.1.0; Lean 4.34.1.
- Checker source uses original native NDJSON bytes, no repaired or simplified
  proof. `cargo test --release --locked` passed under the historically selected
  `NUCLEUS_EXPERIMENTAL_RELEVANCE=1` and
  `NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1` flags; ignored tests remain ignored.
- The six new Arena cases **also** returned identical strict outcomes with
  both experimental flags absent when replayed through the release CLI.
  This is a local Rust + native Arena qualification, **not** the historical
  403-case protected outcome matrix nor full Mathlib.

| Unchanged Arena source | SHA-256 | Native verdict | Requested |
| --- | --- | --- | --- |
| `bugs/rec-rule-proof-irrel` | `e144c9d6a65cc1fbd26a0875788306d72e7690eae61d12d2967a3c4ea7c3287c` | REJECT | REJECT |
| `bugs/rec-rule-proof-irrel-nested` | `61cff0dc13e0287cd21541543b63fc47aa89bebf14d30f14766b4d74f5c77c8c` | REJECT | REJECT |
| `bugs/rec-type-proof-irrel` | `a366791c3deb8c259c8b5f03d61c5016879c1177756372fbd2302539d7c8e581` | REJECT | REJECT |
| `bugs/rec-rule-wrong-arg` | `cf3b02e4dc0c8a3adcf912f09e81a2e467c7cc667b5c5c545b50ad03760eccc9` | REJECT | REJECT |
| `bugs/open-term-cache-context` | `ebacb89b4e72a34aed58f4479e864f562c80ae110e26e7b839563e828cd08f07` | REJECT | REJECT |
| `perf/prop-struct-projections` | `20f2f293fb8e9b75da413b62a0ccc04390ec72594ff0d10c510150784952e8c0` | ACCEPT (1.63 s CLI) | ACCEPT (60 s limit) |

## What changed and why it is constrained

1. A 200-field *proof-only* proposition follows the existing independent
   source-derived large-elimination derivation, lifted from the former
   64-field resource guard to 256. Each source field, recursor, and rule must
   still prove its obligations. A rule with a forged field count is non-ACCEPT.
2. A closed one-field Boolean record with a reduction rule passing `true` or
   `false` instead of its bound constructor field is structurally REJECTED.
   This is **negative-only**, with no new positive recursor authority.
3. An index-preserving family `I : Bool → Prop`, `mk (b : Bool) : I b`, receives
   a checked source-derived formation/recursor path. It permits large
   elimination because the field is fixed by the index, *not* because proofs
   are treated as interchangeable. The genuine prefix through `Box` ACCEPTS.
4. A purported `@id T (mk b)` inside a recursor type or rule is REJECTED only
   if the identity signature and indexed constructor have been checked and
   the claimed type is rigidly headed by a distinct motive or the other
   concrete Boolean index. A control replacing the forged `Box.mk true` with
   matching `Box.mk false` leaves the unsupported `Q` UNKNOWN rather than
   triggering this contradiction guard. No proof-irrelevant quotient of
   *types* or captured binder contexts is used.

## Six existing valid performance residuals

Re-exported independently from the **current** Arena commit above. Verdicts
are from the same local release CLI with the two historical flags enabled;
these are current-source replays. Do **not** assume they are byte-identical to
older frozen exports without comparing SHA-256.

| Test | Current-source SHA-256 | Native verdict / first terminal reason |
| --- | --- | --- |
| `magma-list-pair-n7` | `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35` | UNKNOWN / `application-function-type` |
| `magma-list-pair-n21` | `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84` | UNKNOWN / `application-function-type` |
| `magma-list-deep-n21` | `b7a211699ab32a5d2397319702e2d5552f5796a6bdac990efa69fb186039f526` | UNKNOWN / `distinct-neutral-heads` |
| `magma-list-deep-n36` | `6669cee92ad330dada351ac9e63656f7e9e848dd70376f17030d64677f8c81ac` | UNKNOWN / `distinct-neutral-heads` |
| `fueled-chain` | `e5ca34489fc7b8ee13b1e7f09f76247ab7b01dd1a752a13cc8b796c569e1401a` | UNKNOWN / `application-function-type` |
| `grind-ring-5` | `e9c394e0ff311fd10f60dee2433a530f16e82354c32d6588a8775baa06fd221f` | UNKNOWN / `distinct-neutral-heads` |

**Next decisive experiment:** on byte-frozen `magma-list-pair-n7`, trace the
*first* source-owned stuck `Decidable.rec` major and its fully captured binder
origin, plus the exact failed application-function Pi obligation. Compare one
proposed continuation/memo with the same source and judgment budget; do not
transfer a result across merely similar expressions, proof-irrelevant terms,
or context frames. Require unchanged forged-proof verdicts and original
protected matrix before promotion. Next integration boundary: source-qualified
full Mathlib, independently replayed on the exact advertised exporter/Lean
versions, not inferred from a prefix or smoke test.
