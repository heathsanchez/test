# Obstruction-Driven Probe-Arity Genesis V1 — Frozen Candidate

**Status:** FROZEN BEFORE TEST  
**Date:** 2026-09-14

Purpose: test whether probe-language expansion can be driven by certified
inadequacy rather than hand-selecting the successful arity.

## Algorithm

For a finite relation-discrimination task with external ground requiring two
hypotheses to remain distinct:

1. start with probe arity k=1;
2. exhaustively enumerate all coordinate-projection probes of arity <= k;
3. if any probe separates the hypotheses, stop and retain the smallest
   separating arity;
4. if exhaustive closure contains no separator while external ground still
   requires distinction, record CERTIFIED_OBSTRUCTION_CURRENT_T and increment k;
5. repeat.

If ground does not require a distinction, do not expand merely because no
separator exists.

## Frozen family

Even-vs-odd parity relations for n=3..8.

Prediction: the generic loop should discover minimum separating arity n for
each task, producing exactly n-1 certified arity-expansion steps from k=1.

Controls:
- identical relation vs itself: no expansion authorized;
- a pair distinguishable by unary projection: stop at k=1.

## Falsifier

The candidate fails if the generic loop:
- expands before exhaustive failure at the current arity;
- fails to discover the exact minimum arity;
- expands when ground does not require distinction;
- requires a parity-specific rule.
