# Korovin Global Presentation Certificate V6 — Frozen Protocol

## Developmental inheritance

V5 learned compact verified equations whose contextual closure matched exact semantics through a protected finite horizon.

V6 asks whether that bounded claim can be upgraded to a **global theorem for every finite word** in the generated transformation world.

No new candidate equation may be introduced in V6. V6 may only certify and delete equations from the V5 output.

## Exact external world

For each declared finite transformation world, exact execution supplies the reachable semantic state set and generator transition function. Breadth-first search chooses one shortest canonical word representative `r_q` for every reachable semantic state `q`.

## Finite global certificate

Let `R` be the learned equations and `~_R` the congruence they generate.

V6 requires:

1. **rule soundness**: every retained equation has identical exact semantics on both sides;
2. **start representative**: the empty word is the canonical representative of the initial semantic state;
3. **generator-edge completeness**: for every reachable state `q` and every generator `a`, produce an explicit checked rewrite derivation `r_q a ~_R r_delta(q,a)`.

Every derivation step records the selected relation, direction, context position, before-word, and after-word and is independently replayed by the checker.

## Why the certificate is global

By induction on word length: the empty word is the canonical initial representative. If `w ~_R r_q`, congruence gives `wa ~_R r_q a`, and the certified edge gives `r_q a ~_R r_delta(q,a)`.

Therefore every finite word is congruent to the canonical representative of its exact semantic state. Hence two words with equal semantics are `~_R`-equivalent. Rule soundness gives the converse. Thus generated congruence equals semantic equivalence for **all finite words**, not merely words up to the search horizon.

The finite derivation search bound is only used to find/check the finite generator-edge witnesses; once those witnesses exist, the induction theorem is unbounded in word length.

## Global recompression

Starting from V5's retained equations, repeatedly delete any equation whose removal leaves the full global certificate true. Freeze the resulting rule set.

Then remove each final rule individually. Every final rule must be necessary for the global certificate.

## Frozen worlds

- source: opaque 4-point transformation world;
- independent transfer: opaque 3-point transformation world.

The V5 negative-control and soundness evidence remains inherited; V6 is specifically a completeness upgrade.

## Gates

Source and transfer independently require all final relations semantically sound; every canonical-state × generator edge has a checked derivation; the global completeness theorem hypotheses all hold; every final relation is causally necessary under ablation; and the final theory contains at most three relations.

## Claim boundary

A pass is a global presentation-completeness certificate for the declared finite generated transformation worlds relative to exact external semantics.

It is not evidence of historically novel mathematical objects, an unrestricted automated theorem prover, or completeness for arbitrary infinite structures.
