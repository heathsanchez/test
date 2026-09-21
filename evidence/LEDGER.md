# Metatron Kernel Experiment Ledger

This is the readable projection of `ledger.jsonl`. The JSONL file is the
machine-readable authority. Rejected and unknown experiments remain recorded.

## G0-000 — Arena stream parser

- Status: OPEN
- Arena authority: `f5e1bce6e2dc9c60479b3001b76e01722b403799`
- Obstruction: no independent checker source tree can parse an Arena stream.
- Least capability: format 3.1.0 parsing with sparse, out-of-order typed IDs.
- Falsifier: duplicate or missing references pass, or the two static format
  fixtures require inherited checker source.
- Primary metric: retired instructions after semantic qualification.
