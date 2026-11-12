# C94: charged owner recursor phase and binding-identity audit (13 Nov 2026)

**Outcome:** `WARRANTED_BOUNDED` for read-only diagnostics on two exact Arena
originals; `REJECTED` as simple closure hypotheses: repeated completed-worklist
result reuse, replay-key cost elimination by itself, and repeated immutable
binding-node identity. **No new ACCEPT, soundness rule or proof shortcut.** The
six original valid UNKNOWNs and complete Mathlib are still **UNKNOWN**.

## Authority and boundary

- Upstream Lean Kernel Arena revision:
  `6c2d82164f1a2b1ac94aee62290fe78a3c3853fb`.
- Unmodified native re-exports (SHA-256):
  `magma-list-pair-n7.ndjson` =
  `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`;
  `magma-list-pair-n21.ndjson` =
  `b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.
- Baseline C91 code ancestry: local C93 parent `9d0c986`, equivalent published
  C93 GitHub tree `6288aefca190c8450eb134c4b057ec4680ca0467`.
  C94 changes only `#[cfg(feature="diagnostics")]` observer code and a probe;
  non-diagnostic proof authority and the **65,536** default judgment limit
  are unchanged.
- Diagnostic native build: `cargo build --locked --features diagnostics`;
  SHA-256 binary `f88a80aa816ab66ffc7c49e9927e26bdc704b11f151d165dff58efedb5c9a4e5`.
  Test flags: `NUCLEUS_EXPERIMENTAL_RELEVANCE=1`,
  `NUCLEUS_EXPERIMENTAL_EXPECTED_LAMBDA=1`,
  `METATRON_KERNEL_DIAGNOSTICS=1`; A/B adds
  `NUCLEUS_C94_PHASE_TRACE=1` only to the observed arm.
- Reproduction: `python3 experiments/nucleus-logos-support-20261108/probe_c94_owner_phase.py
  metatron-kernel/target/debug/metatron-kernel
  /path/to/arena/_build/tests/perf/magma-list-pair-n7.ndjson` (likewise n21).
  Probe asserts source hash, original `UNKNOWN` exit 2 with and without the
  observer, identical diagnostic operation counters, charged work bounds and
  phase receipt integrity.
- `cargo test --release --locked` with those two selected relevance/lambda
  flags completed successfully on C94: all active library and integration
  tests PASS, with ten existing unit tests explicitly ignored. An *unflagged*
  test invocation failed on `checked_relevance_signature` because the current
  experimental relevance route is disabled without the declared flags; this
  is not an observer-on/observer-off comparison and is not promoted as a new
  semantic regression. The baseline/qualification boundary retains the flags.

## Most consequential *single* worklist owner per source

| Owner-local measurement | Magma n7 | Magma n21 |
| --- | ---: | ---: |
| Owner fuel at entry | 65,055 | 65,157 |
| Fuel remaining at exit | 0 | 0 |
| Entered qualified recursor nodes | 235 | 206 |
| Fully completed continuations | 192 | 118 |
| Parent continuation resumes | 144 | 74 |
| Maximum pending continuation depth | 83 | 180 |
| Local resolved-result hits | 0 | 0 |
| Global exact completed-cache hits | 0 | 0 |
| Charged replay-key work | 15,440 | 13,720 |
| Replay-key share of spent fuel | 23.73% | 21.06% |
| Fresh `BVar`-major binding demands | 235 | 206 |
| Repeated `(ExprId, binding-node ID)` among those demands | 0 | 0 |
| Final observed recursor head | `NameId(147)` (`Decidable.rec`) | `NameId(147)` |
| Final observed major expression | `ExprId(11)` (`BVar(2)`) | `ExprId(11)` |

On the full native CLI, the observer-off and observer-on versions of each
unchanged source both returned `UNKNOWN` exit 2. Operations were unchanged:
n7 = 276 declaration checks, 89 inductive signatures, 247 type judgments,
45,551 conversions; n21 = 276, 89, 247, 44,957 respectively.

The owner resumes are counted **separately** from fresh major demands. An
early version of the observer mistakenly counted the same parent `BVar`
again after a resume, producing 144 and 74 apparent repeats. A red test
detected the double count; the final observer excludes established-major
resumes. This matters: identical source `ExprId(11)` in changing captured
environments is not evidence of an identical binding or reusable proof.

There are other, smaller replay worklists in both CLI runs; some of those
have one global cache hit. The zeros above describe the single large
**budget-exhausting owner**, not the complete process. Binding-node identity
is a conservative syntactic test: zero identical nodes does **not** prove
semantic inequivalence of their source values. The diagnostic cannot by
itself prove a new compression is sound.

## Consequence for the North Star / factor-model program

The tempting quotient `(source syntax alone)` is invalid: the same `BVar(2)`
is interpreted under distinct captured, typed binder origins. The stricter
quotient `(source expression, identical immutable binding node)` finds no
repeats in the exhausting chain. Nor can the existing exact completed-result
cache avoid computation that has **not finished**. Eliminating the entire
key-construction charge would recover at most 21–24% of this observed owner
allowance, without proving the rest will complete.

**Next smallest experiment:** source-qualify the dynamic call lineage and split
the **remaining** work (~76–79%) by actual major exposure, checked RHS binder
application, RHS exposure, completed-value clone and continuation advancement,
within *the same* owner. Identify the first source rule responsible for the
growing `Decidable.rec` chain before proposing a semantics-preserving evaluator
algorithm. The older canonical ROS C29 observation of potential
`Nat.decidableBallLT` origins is a *candidate*, not a proven causal chain;
its C89 and exact-captured-variable alias audits already found distinct
pending closures/aliases at the separate 262,144-step boundary. **Do not
repeat those negative alias experiments** under a new name. Any proposed
environment quotient would need a stronger complete observational-equivalence
proof for every dependent binder, universe and rule consequence. Do not raise
fuel or use diagnostic constructor endpoints to select a guessed branch.

The historical C89/C90b `262,144 / 24-flag` campaign is a **different**
boundary. This current C91-style experiment cannot be compared to it as if
the source, budget or execution configuration were identical.
