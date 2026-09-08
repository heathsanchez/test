# MathGraph: independent fluid-proof audit

This is an evidence-gathering experiment, not a predetermined refutation or an allegation about authorship.

## Frozen inputs

- OpenAI: `openai/NavierStokesAndEuler` at `8937a8f4cbc7abaab5e9e97d1cc7f5d2319d9538`.
- Alpöge–Buckmaster: `tristanbuckmaster/fluid_lean` at `d0124689230b58b4f86e7b90ac59de06404b3b6b`.
- OpenAI's own Lake manifest pins Lean/Mathlib/Comparator to `v4.34.0-rc2`.

## Questions and evidence levels

1. Does the published OpenAI theorem replay with the stated toolchain? A successful build establishes only the formal theorem, relative to its dependencies and axioms.
2. Does the final theorem depend on any axioms beyond `propext`, `Quot.sound`, and `Classical.choice`? A transitive axiom check, not a text search for `sorry`, decides this.
3. Does an independently supplied challenge statement agree with the solution's definitions? Comparator is the intended check. A successful check of an author-supplied challenge does not by itself establish correspondence to the Clay statement.
4. What exact source files, declarations and import dependencies overlap between the two projects? Source fingerprints and import graphs give reproducible candidates. They do not establish semantic equivalence, originality, or plagiarism.
5. Does a mathematical counterexample invalidate a required theorem or a bridge to Clay's statement? Only an actual proof/counterexample or independently verified formal mismatch supports such a conclusion.

The official Clay alternatives (C) and (D) permit smooth forcing. The presence of forcing alone is not an obstruction. The original `ProblemStatement.candidateStatement` being labelled OPEN also is not an obstruction if the later construction supplies its witness.

## Execution

The isolated GitHub Actions workflow is `.github/workflows/navier-stokes-audit.yml`. It produces source-comparison artifacts and an independent replay/axiom report. Upstream commits are pinned; no upstream source is modified. Infrastructure failures, incomplete verification, and genuine mathematical obstructions must be reported separately. A green workflow is never labelled a Clay Prize decision.
