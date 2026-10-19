# Prospective source selection — pre-outcome freeze, 2026-10-19

This file was written before opening the selected source file or running candidate formalizations.

- Upstream repository: leanprover-community/mathlib4
- Upstream source version: tag v4.34.0 (resolve to immutable commit and record SHA before opening source; if tag unavailable STOP)
- Unopened selected source path: Mathlib/Data/Nat/Choose/Basic.lean
- Selection basis: a combinatorial-number-theory source different from the previously exposed prime-infinitude calibration.
- First eligible tasks: the first eight theorem declarations in textual source order with a contiguous preceding natural-language docstring stating a mathematical proposition, excluding notation/definition-only declarations. No replacements based on whether a task is easy or difficult.
- If fewer than eight eligible declarations, record INSUFFICIENT_SOURCE and STOP, without choosing a new source.
- Mutant families, fixed before outcomes: domain restriction, quantifier weakening, hypothesis deletion, strict/non-strict boundary, swapped equality/inequality, and harmless definitional reformulation; mark inapplicable families UNKNOWN rather than customizing.
- Exact native compilation, baseline and independent mathematical adjudication required before any performance comparison.
- A human-written mutant is a controlled case, not AI-generated or automatically discovered.
- Do not claim a prospective win if the observer uses a hand-coded expected outcome or a source-specific translation not available to the comparator.
- The earlier PrimeIntent.lean and Fin4 controls are exposed calibration, never held-out evaluation.
