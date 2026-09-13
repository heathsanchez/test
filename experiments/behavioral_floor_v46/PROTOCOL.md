# Behavioral Floor V46 — Frozen Protocol

## Question

Can we jump below the remaining representational handholds and derive the smallest lawful predictive world directly from future distinguishability?

V46 receives only:

- a finite alphabet of opaque encounter tokens;
- an exact verified consequence for every finite token history up to a fixed bounded depth.

It receives no:

- objects;
- coordinates;
- state variables;
- memory variables;
- transition law;
- action/world distinction;
- deterministic/nondeterministic model class;
- factor, quotient, graph, relation, or algebra candidate language.

The scientific kernel is frozen before hidden challenge generators are committed.

## Behavioral equivalence

For a history h and bounded future horizon k, define its consequence signature as the vector

    Sig_k(h) = ( Consequence(h ∘ s) )

over every continuation s of length at most k.

Two histories are equivalent at horizon k exactly when these signatures are equal.

No candidate state representation is proposed.

The quotient is induced directly by verified future consequence.

## Finding the floor

The kernel does not receive a required memory depth.

It tests k = 0,1,2,... in order.

A horizon-k quotient is authorized as a bounded behavioral floor only when both conditions hold:

1. RIGHT CONGRUENCE:
   histories currently merged at horizon k remain merged after appending the same encounter token;

2. STABILITY:
   increasing the future horizon from k to k+1 creates no additional history distinction.

The first k satisfying both is retained.

If no such k is found within complete authority, the result is:

    UNKNOWN_FUTURE_HORIZON_INSUFFICIENT

rather than an invented state ontology.

## Derived state and dynamics

Once a stable right congruence is found:

- its equivalence classes are the derived predictive states;
- appending an encounter token induces the transition map between those states;
- histories are memory-equivalent exactly when they occupy the same class.

Thus state, memory, and transition dynamics are all compiled from the same future-consequence equivalence.

## Minimality

For every pair of distinct derived states, the kernel retains an explicit continuation suffix whose verified consequence differs.

Therefore any attempt to merge those two states destroys an authorized future consequence.

Within the bounded authority, this certifies that the retained states are pairwise behaviorally necessary.

## Encounter-token compression

Encounter-token labels are not assumed semantically distinct.

After the state quotient is derived, two opaque tokens are equivalent exactly when they induce the same transition on every derived state.

The kernel therefore also derives the minimal token-action classes supported by predictive consequence.

## Primary finite scope

Primary post-freeze challenges use:

- three opaque encounter tokens;
- prefix histories through depth 4;
- verified futures through depth 4;
- complete consequence authority for every token string through total depth 8.

The hidden challenge generators may use finite machines internally. Those hidden states are never supplied to the frozen kernel.

## Post-freeze challenge family

After freeze, the harness will include:

- a constant-consequence world: all histories and all encounter tokens should collapse;
- a two-state parity world: two predictive states should emerge immediately, while two raw token labels remain behaviorally identical;
- a four-state world where present consequence is too coarse and one-step future consequence is required before the right-congruence stabilizes;
- a delayed four-state world where horizons 0 and 1 produce unlawful/coarse quotients and horizon 2 is the first stable predictive floor;
- a six-state hidden generator whose observable behavior has only four future-distinguishable states, so the behavioral floor must contract the hidden generator rather than recover it;
- independent permutations of the opaque encounter alphabet;
- consequence-label relabellings.

## Frozen gates

B1. Frozen scientific core remains byte-identical.

B2. Constant consequence stops at future depth 0 with one predictive state, one token class, right congruence, stability, and zero nontrivial distinguishing witnesses.

B3. Parity world stops at future depth 0 with exactly two predictive states and exactly two token classes: one toggling class and one behaviorally inert two-token class.

B4. Four-state future-dependent world rejects the horizon-0 quotient by right-congruence/refinement obstruction and first stabilizes at horizon 1 with exactly four predictive states.

B5. Delayed world produces the developmental sequence:
    horizon 0 -> two classes, not a lawful stable floor;
    horizon 1 -> three classes, not a lawful stable floor;
    horizon 2 -> four classes, right congruent and stable.

B6. Restricting the delayed world to available future horizon 1 or 2 returns UNKNOWN_FUTURE_HORIZON_INSUFFICIENT; allowing horizon 3 recovers the four-state floor at k=2.

B7. Every pair of distinct delayed-world floor states has an explicit distinguishing continuation witness, and the largest minimum witness depth is exactly 2.

B8. Six-state hidden generator contracts to exactly four behavioral states at future depth 1; hidden generator cardinality is not recovered merely because it exists.

B9. The six-state generator's four behavioral states are pairwise future-distinguishable and right-congruent.

B10. Encounter-token compression is derived from state consequence: redundant token labels merge in parity/delayed worlds, while the future-dependent four-state world retains three distinct token classes.

B11. Independent opaque-token relabelling transforms history equivalence and token classes equivariantly.

B12. Consequence-label relabelling preserves future-depth floor, history equivalence, state count, token classes, and transition structure up to state-label isomorphism.

B13. Maximum-state bound 1 preserves the constant world but is explicitly inadequate for every world whose behavioral floor contains multiple pairwise-distinguishable states.

B14. Removing verification authorizes no behavioral quotient search; incomplete trace authority remains UNKNOWN_AUTHORITY.

B15. No hidden machine state names/cardinality, object/graph/factor/quotient candidate catalogue, or transition model class occurs in the frozen executable kernel.

B16. The only primitive ordering retained by the experiment is finite encounter sequence plus verified consequence; every returned state distinction has a future-consequence witness.

## Claim boundary

A pass would not derive reality from literal nothing.

V46 still supplies:

- an opaque finite encounter alphabet;
- sequential composition/order of encounter tokens;
- exact complete consequence authority through a bounded depth;
- a finite maximum future horizon.

What a pass can establish is much stronger than the previous one-handhold-at-a-time experiments:

> within complete bounded encounter authority, state, memory depth, transition dynamics, and encounter-token distinctions can all be derived at once from future consequential distinguishability. The retained predictive ontology is the first stable right-congruence of histories, and every retained state distinction is certified by a future consequence that forbids merging it.

This is the operational floor being tested: distinctions that no authorized continuation can witness are erased; distinctions with a verified future witness survive.
