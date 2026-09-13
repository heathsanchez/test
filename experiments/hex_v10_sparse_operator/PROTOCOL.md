# Hex V10 Sparse Operator — Frozen Protocol

## Question

Can the selector learned in V8 be constructed incrementally from unseen-pattern residuals, without supplying the complete library of 16 binary Boolean operators?

## Initial state

Boundary observations are FIRST and LAST.

The developmental object is a partial table over input patterns 00, 01, 10, 11. All four entries begin undefined.

The only generic growth action is to assign 0 or 1 to a currently undefined pattern. Earlier assignments are frozen.

## Stage 0

Complete one-relation world: 64 loopless directed graphs on 3 vertices, 4,096 ordered pairs.

Only pattern 11 occurs. Evaluate both possible assignments for 11 and retain only a zero-disagreement assignment.

## Stage 1

Complete two-relation world: 36 objects, 1,296 ordered pairs.

New patterns 10 and 01 occur. Evaluate all four assignments to those two cells, preserving the Stage-0 cell.

## Stage 2

Complete three-relation world: 8 objects, 64 ordered pairs.

New pattern 00 occurs. Evaluate both assignments, preserving all earlier cells.

## Cost comparison

V8 complete-table search:
16 * (4096 + 1296) + 2 * 64 = 86,400 candidate-level semantic pair comparisons.

V10 sparse completion:
2 * 4096 + 4 * 1296 + 2 * 64 = 13,504 comparisons.

## Controls

For every retained cell, changing its value must cause nonzero disagreement on the stage that earned it.

## Held-out continuation

Instantiate the completed table on six named directed relations over a two-vertex carrier. Generate one positive and one negative held-out pair, compile to pinned HexGraphIso, and kernel-check both.

## Pass

A pass requires unique successful completion at every stage, final table [1,1,1,1], exact match to V8, all cell-flip controls passing, the frozen comparison counts above, and successful held-out Hex checks.

## Claim boundary

This removes the supplied 16-member complete operator library. The remaining substrate is the generic ability to assign a Boolean value to a previously undefined table cell.
