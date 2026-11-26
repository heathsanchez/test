# Nucleus

```text
                     .-"""""""-.
                  .-'  n  p  n  '-.
                 /  p  .-----.  p  \
                |  n  / p n p \  n  |
                |  p  \ n p n /  p  |
                 \  n  '-----'  n  /
                  '-.  p  n  p  .-'
                     '-._____.-'

                  N U C L E U S
```

**An independent Rust proof checker for Lean 4 exports.**

Nucleus checks serialized declarations against its own implementation of
Lean's typing and conversion rules. It returns an explicit **UNKNOWN** when
the input exceeds its supported fragment or resource allowance. Developed by
[Metalogic Labs](https://mathgraph.org/).

[Quick start](#quick-start) · [Scope](#supported-scope) ·
[Evidence](#qualification) · [Contributing](CONTRIBUTING.md)

## Why Nucleus?

- **Independent implementation.** The runtime uses its own Rust checker and
  does not invoke Lean or another proof checker.
- **Source-derived checks.** The supported renovation fragment reconstructs
  inductive families and recursors from source types, checking feature flags,
  constructor telescopes, universe constraints and computation rules.
- **Explicit limits.** Unsupported declarations and conversions are declined.
  Errors retain their own exit code.
- **Reproducible lineage.** The initial standalone import preserves the
  qualified checker, frozen configuration and development history. See
  [source provenance](docs/PROVENANCE.md).

## Quick start

Requires [Rust](https://www.rust-lang.org/tools/install) **1.99.1**, Python
**3.10 or newer**, and Git. The Rust version is pinned in `rust-toolchain.toml`.

```sh
git clone https://github.com/metalogiclabs/nucleus.git
cd nucleus
cargo build --locked --release --features diagnostics
python3 arena.py < tests/fixtures/good-beta-definition.ndjson
```

Use `arena.py` for the qualified launch configuration. It passes the original
input bytes to the binary, clears inherited `NUCLEUS_` and `METATRON_`
configuration, and applies the checked-in [capability flags](arena-flags.json).
The release uses one worker with a 128 MiB stack and declines inputs larger
than 10 MiB. Process time limits are supplied by the caller or Arena.

### Exit codes

| Code | Verdict | Meaning |
| ---: | --- | --- |
| `0` | ACCEPT | The input passed the implemented checks. |
| `1` | REJECT | The checker established an invalidity within its supported checks. |
| `2` | UNKNOWN / DECLINE | Unsupported input, unresolved check or resource allowance. |
| `3` | ERROR | Parsing or internal failure; inspect stderr. |

The launcher also preserves abnormal process termination. Treat every code
other than `0` as a failed verification attempt in an accepting pipeline.

## Supported scope

Nucleus has a legacy format **3.1.0** path and a bounded format **3.2.0**
renovation path. The latter admits supported single, nonrecursive inductive
families and their recursors, plus a bounded projection fragment with
dependent field substitutions. A contradiction of a necessary condition can
warrant rejection even when complete admission is unsupported.

General renovated inductives, every Lean conversion, and full Mathlib
acceptance are **not established**. The current entry's explicit size declines
also exclude large environments. See [qualification and limits](docs/QUALIFICATION.md)
for the exact tested boundary.

The [portable Lean model](formal/README.md) establishes limited environment
laws under abstract typing assumptions. It is not a soundness proof of the
Rust implementation.

## Qualification

The imported snapshot was qualified against exact, hash-verified input bytes:

| Frozen source qualification | ACCEPT | REJECT | UNKNOWN |
| --- | ---: | ---: | ---: |
| 356 downloadable beta inputs | 59 | 51 | 246 |
| 138 renovation inputs, included above | 29 | 34 | 75 |
| 212 legacy regression inputs, a separate replay | 122 | 84 | 6 |

No incorrect decisive verdicts or crashes were observed in that qualification.
These are bounded test results; the rows overlap and must not be added.

- [Original source qualification](https://github.com/heathsanchez/test/actions/runs/45681083460)
- [Merged Nucleus Arena entry](https://github.com/leanprover/lean-kernel-arena-beta/pull/3)
- [Lean Kernel Arena preview](https://leanprover.github.io/lean-kernel-arena-beta/)
- [Standalone migration checks](docs/QUALIFICATION.md#standalone-migration)

## Development

```sh
python3 scripts/verify_source_import.py
RUST_MIN_STACK=67108864 cargo test --locked
python3 -m unittest discover -s tests_py
```

The import check compares runtime files to the original qualified snapshot.
A deliberate checker change requires a new qualification and an explicit
update of that baseline. The test workflow exercises the supported Rust and
Python tests and the frozen launcher.

The next technical objective is to reduce the renovation UNKNOWNs, one
minimized unsupported input at a time, while preserving established decisions.
See [contribution guidance](CONTRIBUTING.md).

## Project layout

| Path | Contents |
| --- | --- |
| `src/` | Rust parser, typing, conversion and inductive checks |
| `arena.py`, `arena-flags.json` | Frozen public launch configuration |
| `tests/`, `tests_py/` | Regression tests and fixtures |
| `evidence/` | Historical research records and import identity |
| `formal/` | Limited, explicitly scoped Lean semantics model |
| `scripts/` | Qualification and research tools; historical dependencies are documented |

Nucleus is separate from [MathGraph Flash](https://github.com/metalogiclabs/mathgraph-lean-kernel),
the sokonanoda-derived implementation evaluated on the main Arena. Lean 4,
lean4export and the Arena provide the upstream theory, exchange format and
test infrastructure.

## License

[MIT](LICENSE). Copyright 2026 Heath Sanchez and Nucleus contributors.
