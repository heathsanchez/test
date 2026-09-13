# Contextual Multigrain Genesis V28 — Frozen Protocol

## Question

Do the papers' common clues actually require one adaptive scale, or a family of consequence-relative grains?

V28 tests the stronger hypothesis:

    grain = quotient by consequential indistinguishability,

and asks whether different admitted futures/contexts can force incomparable quotients on the same underlying presentations.

It also tests the proposed two-sided interval:

    coarsest prediction-sufficient grain
        <= lawful grain
        <= finest independently recordable grain.

No preferred partition, feature axis, PCA direction, or context-specific split is supplied.

## Primitive data

A finite world contains:
- an anonymous carrier X;
- anonymous relevance/measurement/branch contexts C;
- exact future-consequence signatures F_c(x);
- optionally exact independently recordable signatures R_c(x).

The learner receives no latent factors or human names for what each context means.

## Candidate grain language

A grain is an arbitrary set partition Pi of X.

The kernel exhausts every partition of X.

For a context c, Pi is prediction-sufficient iff every block is homogeneous in F_c.

Pi is record-lawful iff it never separates two states that have identical R_c.

Thus, under the refinement order:

    Q_pred(c) <= Pi <= Q_record(c),

where Q_pred(c) is the coarsest prediction-sufficient quotient and Q_record(c) is the finest record-warranted quotient.

The kernel does not assume these quotients; it recovers them by exhaustive partition search and exact verification.

## Multiple grains

For each context, select the globally coarsest sufficient grain by minimum block count.

A single fixed grain for all contexts must be sufficient for the joint consequence vector

    (F_c(x))_{c in C}.

If per-context grains are incomparable and the fixed grain is strictly finer, the system must preserve the contextual family rather than claim one universally privileged scale.

Active complexity is the number of blocks in the grain used for the current context.

This is not a fitted cost.

## Development

The developmental rule remains:

    identify until consequence forces distinction;
    distinguish only as far as consequence requires;
    preserve incomparable lawful grains when different futures require them.

A new context:
- reuses an existing grain if its exact consequence quotient matches;
- otherwise acquires the new coarsest sufficient quotient;
- does not alter unrelated retained grains.

## Required post-freeze gates

G1. Exhaust all partitions of the hidden carrier.
G2. Independently recover each context's coarsest prediction-sufficient grain.
G3. At least two recovered grains are incomparable under refinement.
G4. No grain with the per-context minimum block count is sufficient for both contexts.
G5. The coarsest single fixed grain sufficient for all contexts is strictly finer than each active contextual grain.
G6. Contextual active complexity is strictly lower than fixed-grain complexity in each incompatible context.
G7. Relabelling the carrier preserves the multiset of grain block-size signatures and the refinement/incomparability structure.
G8. If two contexts induce the same quotient, the second context reuses the grain rather than creating a duplicate.
G9. Changing consequence in one context refines only that context's grain; an unrelated context's retained grain is unchanged.
G10. A branch-labelled challenge and a relevance-labelled challenge are handled by the same frozen kernel; context semantics are not hard-coded.
G11. Where record signatures are supplied, exhaustive search recovers a nonempty admissible interval between prediction sufficiency and recordability.
G12. No grain finer than the record quotient is admitted.
G13. The coarsest prediction-sufficient grain lies inside the recordability interval.
G14. Incomplete consequence/record authority returns UNKNOWN_AUTHORITY.
G15. With consequence comparison disabled, no nontrivial predictive grain is certified.
G16. Forcing a single global grain is causally more complex on the incompatible-context challenge.

## Scientific interpretation

A pass establishes only, in bounded finite exact worlds:

> scale need not be a scalar or a single hierarchy. Different future-relevance contexts can induce incomparable minimum sufficient quotients, while independently recordable distinctions place an upper bound on lawful refinement.

This is a finite classical analogue of the shared structural clue in causal-state prediction, multi-relevance coarse graining, information-theoretic RG, and adaptive/branch-dependent coarse graining.

## Claim boundary

A pass does NOT establish quantum decoherence, physical renormalization, natural-world scale discovery, consciousness-dependent reality, or autonomous invention of the context/measurement interface.

The next tests after a pass are:
1. branch-dependent grain updates over time rather than static context labels;
2. interventions that change the state they measure;
3. stochastic rather than exact consequence equivalence.
