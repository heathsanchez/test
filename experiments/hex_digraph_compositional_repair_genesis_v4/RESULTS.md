# Hex Digraph Compositional Repair Genesis V4 — Sealed Result

## Verdict

**VERIFIED_COMPOSITIONAL_REPAIR_GENESIS**

Workflow run: 34728202783  
Workflow job: 103646051150  
Head: `e76168cbdadfdef15d580bad8328514470da04f9`  
Evidence artifact: 10309055753  
Artifact ZIP SHA-256: `f1c4e1129e2ecf49f8e15bc4c879e7a7c2f49537118064dd94d234679cfc5ef8`

## What V4 removed

V3 supplied four named repairs, one of which was the full successful identity-channel construction.

V4 no longer supplies that repair.

It supplies only three generic developmental primitives:

1. `ADD_FRESH_ROLE`
2. `COUPLE_OLD0_TO_FRESH`
3. `COUPLE_OLD1_TO_FRESH`

No primitive denotes the complete adapter.

## Starting state

The one/two-role substrate was again exhausted first and remained inadequate.

The canonical least-residual two-role state is the direction split with arc channel `0 -> 1` and no identity couplings. Its residual is nonzero.

## Breadth-first developmental search

Programs were enumerated level-completely from the three primitives.

Depth 1:

- add the fresh role only;
- still fails.

Depth 2:

- `ADD_FRESH_ROLE ; COUPLE_OLD0_TO_FRESH` → **36 disagreements**;
- `ADD_FRESH_ROLE ; COUPLE_OLD1_TO_FRESH` → **36 disagreements**.

No depth-1 or depth-2 state qualified.

Depth 3:

`ADD_FRESH_ROLE ; COUPLE_OLD0_TO_FRESH ; COUPLE_OLD1_TO_FRESH`

produced:

- roles: 3;
- arc channel: `0 -> 1`;
- identity couplings: `0--2`, `1--2`;
- semantic disagreements: **0 / 4,096**.

That state is exactly the adapter independently selected in V2 and downstream kernel-checked through Hex there.

Removing either coupling restores failure.

All eight V4 gates passed.

## Why this matters

The successful repair was no longer present as one supplied move.

It had to be **constructed compositionally** from a smaller developmental basis, and every proper prefix of the winning construction remained semantically inadequate.

The causal chain is now:

`finite failure -> fresh role -> still failure -> one identity link -> still failure -> second identity link -> zero residual`.

## Sealed files

- `PROTOCOL.md`: `c5b01274cde589005b9ff652f755187e99adea91d6302e4a72409a18c93ea2d3`
- `run.py`: `4d3ffbb2cbb22859c7ee2f5e8c16e0c90bb4c9572b3107799848cff15034615b`

## Claim boundary

This establishes bounded compositional repair synthesis from a supplied primitive developmental basis.

It does not establish autonomous invention of that primitive basis.

The remaining human-design boundary has therefore moved again: the human supplies the subject, verifier, and primitive growth language; semantic consequence selects and composes the successful developmental path.
