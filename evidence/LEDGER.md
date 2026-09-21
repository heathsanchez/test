# Metatron Kernel Experiment Ledger

This is the readable projection of `ledger.jsonl`. The JSONL file is the
machine-readable authority. Rejected and unknown experiments remain recorded.

## G0-000 — Arena stream parser

- Status: RETAINED
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Implementation: `313fcd92ec629afd0aa82b75156c2e57dcb9d75f`
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
