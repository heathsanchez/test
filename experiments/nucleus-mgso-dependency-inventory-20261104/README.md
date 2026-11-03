# Nucleus source-stable candidate declaration identities

This isolated research experiment builds *source-level candidate* identities
on the real Lean 4 `lean4export` 3.1.0 NDJSON syntax used by independent Rust
Nucleus. **It has no authority to skip kernel checking.** A candidate match
is not an authenticated prior kernel acceptance, a complete environment
snapshot, a proof of claim fidelity, or an Arena benchmark gain.

The observer recursively resolves names, universe levels, and expressions
from their exporter-local integer IDs. Every declaration has a canonical
source shape ID and a separate transitive *candidate support* ID computed
over direct constant references. Unknown/malformed structures fail closed.
Strong `Name` identities are encoded as ordered typed segments, not ambiguous
pretty-printed text. The inventory includes an explicit UNKNOWN global-checker
closure because Nucleus's actual implementation performs export-global
quotient, recursor, capability and universe preflights before declarations.

The seven native mutation arms include an exporter ID renumbering, later
theorem rename, earlier binder change, theorem-to-axiom replacement, forged
self-reference and a later forged `Quot` declaration. In the last case, both
prior theorem IDs remain identical but native Nucleus rejects the export.
This is a decisive *negative* control for naive selective proof skipping.

`corpus_inventory.py` also surveys every native fixture, including those that
the actual checker rejects or leaves UNKNOWN. It never promotes candidate
source matching into a positive proof verdict. No Rust kernel source, MGSO
receipt semantics, or default Arena path is changed.

## Reproduce

```bash
cargo test --release --locked --manifest-path metatron-kernel/Cargo.toml \
  --test mgso_golden --test mgso_graph --test mgso_shadow --test mgso_process
cargo build --release --locked --manifest-path metatron-kernel/Cargo.toml
NUCLEUS_DEPENDENCY_BINARY="$PWD/metatron-kernel/target/release/metatron-kernel" \
  python3 -m unittest discover \
  -s experiments/nucleus-mgso-dependency-inventory-20261104 -p 'test_*.py' -v
```

The branch-scoped GitHub Actions workflow preserves native source/build pins,
all seven source-arm outcomes, two exact MGSO read-only inspections and the
complete 55-fixture source-inventory/native verdict observations. Outputs are
bounded source observations; they are not reusable proof certificates.

## Current boundaries

The local inventory intentionally caps individual inputs at 20 MiB, so the
6.18 GiB Mathlib export is **not** covered. It neither restores a verified
Nucleus environment nor authenticates a producer's cached verdict. A future
warm strategy must first account for all Nucleus global preflight and runtime
environment dependencies, its exact checker identity/configuration, the
compiler's source semantics, provenance and revocation. Until then, even an
identical candidate ID leads to a new independent kernel execution.
