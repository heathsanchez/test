# Branch-Conditioned Grain Dynamics V29 — Frozen Protocol

## Question

V28 showed that different contexts can require incomparable minimum sufficient grains. V29 asks whether the active grain can change prospectively as history itself selects which future is relevant.

The target is:

    unresolved branch set
      -> finest grain needed to preserve all possible branch futures
      -> branch observation
      -> branch-conditioned future
      -> coarser or otherwise different active grain
      -> exact prediction preserved.

No semantic branch names or branch-specific feature axes are supplied.

## Primitive data

A finite world contains:
- anonymous present states X;
- anonymous observed history tokens H;
- exact future signatures F_h(x).

Before a branch token is observed, the learner must preserve all branch-contingent futures jointly.

After a concrete history token h is observed, only F_h is relevant to the active grain.

## Grain construction

The candidate grain language is every partition of X.

Pre-branch grain:
    coarsest partition sufficient for the joint vector
    (F_h(x)) across all possible h.

Post-branch grain for observed h:
    coarsest partition sufficient for F_h(x).

All partitions are exhaustively searched.

## Developmental interpretation

The branch token is not a hand-written semantic context. It is simply an observed history record.

The same hidden present state may therefore require a different quotient before and after the branch becomes known.

Observation can make the active grain:
- finer, if a realized branch reveals distinctions that were previously irrelevant;
- coarser, if learning which future applies makes other distinctions unnecessary;
- incomparable to another branch's grain.

V29's hidden challenge is designed to test the second and third cases.

## Required post-freeze gates

B1. Exhaust all state partitions for pre-branch and every post-branch analysis.
B2. Before branch observation, the coarsest sufficient grain must preserve all possible branch futures jointly.
B3. Each observed branch must recover its own coarsest sufficient grain.
B4. At least two branch-conditioned grains must be incomparable.
B5. The pre-branch grain must be strictly finer than each post-branch grain on the main challenge.
B6. Exact future prediction must be preserved after branch-conditioned contraction.
B7. Ignoring history after the branch must force retention of the more complex pre-branch grain.
B8. Anonymous relabelling of states and branch tokens must preserve structural signatures.
B9. If two branches induce the same future quotient, the second branch reuses the same grain.
B10. Perturbing one branch future must change only that branch-conditioned grain.
B11. A missing branch record must not guess a branch-specific grain; it must retain the pre-branch grain.
B12. Incomplete future authority returns UNKNOWN_AUTHORITY.
B13. With consequence comparison disabled, no predictive branch grain is certified.
B14. The branch-conditioned active block count must be strictly lower than the branch-ignorant block count in every main branch.
B15. No semantic string in the branch token is consulted by the frozen kernel.

## Scientific interpretation

A pass establishes only, in a bounded exact classical setting:

> the warranted grain can be history-dependent. Learning which branch was actually realized can lawfully remove distinctions that were needed only while several futures remained possible.

This is a finite classical analogue of branch-dependent adaptive coarse graining, not a quantum-decoherence result.

## Claim boundary

A pass does NOT establish quantum branching, decoherence, collapse, many-worlds, or physical measurement disturbance.

The next required experiment is active observation:
the measurement operation must itself change the state whose future grain is being inferred.
