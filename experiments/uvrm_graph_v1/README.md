# UVRM Research Graph V1

This is the first concrete test of the proposal that a typed external research graph can replace narrative reconstruction of an experimental lineage.

## Source lineage

The graph encodes the Lean-kernel RGRS sequence E0031-E0034 only. It uses the frozen E0031/E0032 residual record and the E0033 evidence quoted in the E0034 precommit. The historical next move, E0034 parent-tail projection splice, is stored only as the protected expected answer for the reconstruction test.

The graph contains typed evidence, residual, hypothesis, candidate-action, and relation objects. Relevant edge types include `DERIVED_FROM`, `SUPPORTS`, `REFUTES`, `SHARPENS`, `RIVAL_OF`, `DISCRIMINATES`, `MOTIVATES`, and `PRECEDES_IF_NULL`.

## Test question

Given only the typed graph state, can a simple UVRM frontier selector reconstruct:

1. the sharp residual frontier;
2. live and refuted rival explanations;
3. the historically chosen next discriminator;
4. a changed decision when crucial evidence is ablated;
5. reopening of a rejected branch when its negative evidence is removed?

## Frozen historical target

The historical precommit for E0034 states that E0031 found 59.4% late canonical-frame reuse but only ~1.4% exact raw-pair repetition; E0032 found only ~2.39 mean Cons scan depth, rejecting an immediate heavyweight indexed/DAG redesign; and E0033 found exact usable parent-tail projection knowledge on 19.43% of nonzero Cons tails. The historical next experiment therefore tested composition of existing suffix knowledge before quotient-fingerprint invention.

V1 asks whether the graph can recover that decision without reading the prose precommit as an instruction.

## Scope boundary

This is not yet an LLM-vs-transcript experiment and not evidence that graphs improve research generally. The candidate action set is still supplied. V1 tests whether typed evidence and negative laws are sufficient to reconstruct the correct frontier choice and whether the choice is causally sensitive to graph evidence.

The next stronger test removes the supplied candidate-action set: candidate generators (LOCAL, RESIDUAL, STRUCTURAL, RETAINED, IMPORT, HUMAN) receive only the graph and must propose actions before the controller ranks them. A transcript-driven arm receives the same source information in chronological prose under a matched model/tool budget.
