# C125 projection target: source-pinned surrogate preflight

Status: **CANDIDATE / native UNKNOWN** (2026-11-14 NZ). This is a research-only,
diagnostic change, **not** a source-qualified completion of C125 on C124.

## Objective and authority

The C124 Research OS checkpoint reports 80 distinct captured projection-root
major calls consuming 26,132 source-work units. C125 asks whether their actual
`BVar(0)` projection targets can be transported across contexts without losing
source authority or binder meaning. The frozen original Arena
`magma-list-pair-n21.ndjson` has SHA256
`b8279fa9189a203c6c11b04702c27c0f99a650b37f2b0165dd260b1d14e9ef84`.

Independent static inspection of that exact NDJSON confirms:

- Expr 1: `BVar(0)`.
- Expr 811: projection index 0, structure Expr 1.
- Expr 7194: `App(Proj 811, Lam 7193)`.
- Expr 7198: `App(Expr 7194, Lam 7197)`.

The present source branch is based on recovered **C105**
`4fb6b4f8ff60ce1ed17782127734d1a3f4c98ba6`, itself the exact C104 child
of published C97 `bd05ea33425e560d17b40784a8afc79b46b55ec5`.
The original C106–C108 commits have not been recovered, so thin Git bundles
for C109–C124 cannot yet be imported with their exact parent chain.
Accordingly, neither the instrumentation nor its eventual runtime receipts
should be called the original C124 descendant.

## Instrument and decisive gate

`NUCLEUS_C125_PROJ_BINDING_TRACE=1` enables a read-only, source-ID-pinned
receipt at the real native recursor-major consumption point. For every terminal
Expr 7198, it records owner fuel, actual charged cost and depth, the two-link
BVar closure walk, terminal frame and level context, immutable BVar(0) binding
node ID, captured binding kind, closure payload expression/frame/levels, full
debug payload, and whether the major was nested/proven/unresolved. It does not
alter the evaluator, soundness rules, fuel accounting or verdict.

`probe_c125_projection_target_surrogate.py` independently checks the source
SHA and AST, original-versus-observer verdict/operation equality, and three
SHA-pinned forged proof controls. It **refuses to promote** results unless the
actual nested 128–511-unit projection population matches the C124 reference
of exactly 80 calls and 26,132 charged units. Its output distinguishes the
number of real binding nodes, payload kinds and full payload fingerprints.
These debug fingerprints may include run-local environment identities: either
equality or inequality is **observational**, not a proof of semantic equality
or a formal contextual transport law.

Suggested native command from the repository root (requires Rust Cargo and a
diagnostics binary):

```sh
cd metatron-kernel
cargo build --features diagnostics --bin metatron-kernel
cd ..
python3 experiments/nucleus-logos-support-20261108/probe_c125_projection_target_surrogate.py \
  metatron-kernel/target/debug/metatron-kernel \
  experiments/nucleus-coverage-evidence-20261104/inputs/magma-list-pair-n21.ndjson.zst
```

## Completed preflight, residual, and promotion rule

- Frozen source SHA and the four listed source nodes: **PASS**.
- Python probe compilation and synthetic receipt parsing: **PASS**.
- Git whitespace/diff check: **PASS**.
- Rust native compilation, exact 80-call trace, operation equivalence and
  forged-proof replays: **NOT RUN**, because this environment lacks `cargo`
  and network access to install the Rust toolchain.
- Unchanged original standard-budget verdict: last independently qualified
  C124 evidence still **UNKNOWN**; no new verdict is claimed.
- C124 exact lineage: **UNRECOVERED** (missing unpushed C106–C108 objects).

The cheapest next action is to run this surrogate on native CI, then inspect
the 80 actual captured binding/payload results. If the 80/26,132 gate fails,
the source lineage differs materially and the surrogate remains UNKNOWN. If it
passes, promote only that *bounded observation*. A sound optimizer still
requires a type/binder/authority/level/fuel-preserving continuation proof and
full protected regression, with no forged ACCEPT.
