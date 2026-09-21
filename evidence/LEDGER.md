# Metatron Kernel Experiment Ledger

This is the readable projection of `ledger.jsonl`. The JSONL file is the
machine-readable authority. Rejected and unknown experiments remain recorded.

## G0-000 — Arena stream parser

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `d8fa825da86b88c8c93ec409b8a4485e4228d298`
- Obstruction: no independent checker source tree can parse an Arena stream.
- Least capability: format 3.1.0 parsing with sparse, out-of-order typed IDs.
- Falsifier: duplicate or missing references pass, or the two static format
  fixtures require inherited checker source.
- Qualification: six parser tests, full Rust suite, strict Clippy, CLI exit 2,
  and byte equality against both pinned upstream fixtures passed.
- Protected behavior: malformed streams exit as `ERROR`; unsupported semantic
  declarations remain preserved and yield `UNKNOWN`.
- Primary metric: retired instructions after semantic qualification.
- Performance: deliberately unmeasured at this stage; parser-only correctness
  does not qualify an official retired-instruction comparison.

## G1-001 — Conservative universe equality

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `2f222bf76e8852d748da1782768f29a64873192b`
- Obstruction: Sort inference needs universe equality, but symbolic `imax`
  cannot be collapsed to `max` without proving its right side nonzero.
- Least capability: canonical max/successor atoms, the two unconditional
  `imax` branches, and a bounded guarded node for every unresolved case.
- Falsifier: disagreement with Lean 4.29.1, guessing symbolic `imax`, or
  failure of the 26-parameter equality within 256 semantic steps.
- Qualification: the pinned Lean reference accepted the commutativity,
  idempotence, successor-right, and concrete zero-right obligations; all six
  Rust tests and the protected suite passed.
- Performance: the non-explosion test passed; official retired instructions
  remain deliberately unmeasured until an end-to-end checker qualifies.
