# Epistemic Floor V47 — Frozen Protocol

## Question

What remains when complete consequence authority is removed?

V47 receives only finite positive encounter evidence:

- opaque encounter histories;
- observed consequence tokens;
- an optional finite set of histories certified CLOSED, meaning the observed consequence support at those histories is exhaustive;
- a finite known consequence alphabet.

It does not receive a complete consequence table.

The scientific kernel is frozen before hidden evidence streams and closure patterns are committed.

## Version-space semantics

For every bounded encounter history h, let O(h) be the set of consequences actually observed.

If h is OPEN, every nonempty support S(h) satisfying

    O(h) ⊆ S(h) ⊆ Y

remains epistemically possible.

If h is CLOSED, then

    S(h) = O(h)

exactly.

Thus the evidence induces a finite version space of complete bounded consequence-support laws.

No probabilistic sampling model, confidence threshold, prior, or frequency heuristic is supplied.

Repeated positive observations of the same consequence do not by themselves rule out an unseen consequence.

## Behavioral floor of one completed law

For any completed support law S, define behavioral equivalence exactly as in V46, except that the verified consequence of one history is now its full support set S(h).

Two histories are equivalent at future depth k iff every continuation up to k yields the same support set.

The first horizon whose quotient is both:

- a right congruence under encounter extension; and
- stable at one deeper future horizon

is the bounded behavioral floor of that completion.

## Epistemic identifiability

V47 does not choose one completion.

It asks whether every law still compatible with the finite evidence induces the same behavioral floor.

If two compatible completions disagree, the result is:

    UNKNOWN_IDENTIFIABILITY

and the kernel returns both complete support tables as explicit witnesses.

If all compatible completions agree exactly on:

- floor future depth;
- history equivalence;
- derived transition maps;
- encounter-token classes,

the result is:

    VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR.

Thus UNKNOWN is not model uncertainty after choosing an ontology.
It means the ontology itself is not yet identifiable from the evidence.

## Exactness and resource bound

The kernel first compares two compatible extreme completions:

- minimal allowed supports;
- maximal allowed supports.

If they disagree, non-identifiability is already proved.

If they agree, the kernel exhaustively enumerates the finite version space when it contains at most 65,536 completions.

If the version space is larger and the two extremes happen to agree, it returns:

    UNKNOWN_COMPLETION_SPACE_RESOURCE_BOUND

rather than claiming identifiability.

No Monte Carlo approximation is used.

## Forced epistemic facts

Some facts may be identifiable even when the whole behavioral floor is not.

In particular:

- if two different consequence tokens have actually been observed for the same history, genuine branching support is forced at that history;
- if a history is CLOSED with exactly one observed consequence, singleton support is forced there.

The kernel reports these separately from global floor identifiability.

## Primary finite scope

Primary hidden challenges use:

- two opaque encounter tokens;
- a binary consequence alphabet;
- prefix histories through depth 2;
- possible futures through depth 2;
- the 31 encounter histories of total depth at most 4.

A positive-only dense evidence stream may contain at least one observation for every one of those 31 histories while still leaving all histories OPEN.

That is intentionally not equivalent to complete authority.

## Post-freeze challenge family

Only after freeze, the harness will instantiate:

1. DENSE PARITY, OPEN:
   one observed deterministic consequence for every bounded history, but no closure certificates.
   A deterministic two-state completion and a maximally branching one-state completion must both remain compatible, forcing UNKNOWN_IDENTIFIABILITY.

2. REPEATED PARITY, OPEN:
   the same positive evidence repeated many times.
   The epistemic result must remain exactly the same as DENSE PARITY, OPEN.

3. PARITY, CLOSED:
   the same observed outcomes with all 31 supports certified exhaustive.
   The two-state parity behavioral floor must become identifiable.

4. FUTURE-DEPENDENT FOUR-STATE, CLOSED:
   complete closed support evidence whose floor requires one future step and four predictive states.

5. FUTURE-DEPENDENT FOUR-STATE, OPEN:
   exactly the same positive outcomes as (4), but without closure.
   It must remain non-identifiable.

6. FORCED-BRANCHING, OPEN:
   at one history both binary consequences are observed, while the global floor remains underdetermined.
   Branching at that history must be certified even though the ontology remains UNKNOWN.

7. CONSTANT, CLOSED:
   one-state behavioral floor.

8. CONSTANT SINGLE-CLOSURE ABLATIONS:
   remove exactly one closure certificate at a time.
   Each ablation must restore non-identifiability, testing whether negative/exhaustive evidence is actually required to certify total behavioral sameness.

9. opaque encounter-token relabellings and consequence-token relabellings.

## Frozen gates

E1. Frozen scientific core remains byte-identical.

E2. Dense positive-only parity evidence returns UNKNOWN_IDENTIFIABILITY with two explicit compatible completions: one deterministic two-state floor and one branching one-state floor.

E3. Repeating every parity observation many times leaves the epistemic result and completion space unchanged.

E4. Closing the exact same parity evidence collapses the version space to one completion and yields an identifiable two-state, depth-0 behavioral floor.

E5. Closed future-dependent evidence yields an identifiable four-state floor at future depth 1.

E6. Removing closure from exactly the same future-dependent positive outcomes restores UNKNOWN_IDENTIFIABILITY.

E7. The forced-branching open world reports the designated history as forced branching while the global behavioral floor remains UNKNOWN_IDENTIFIABILITY.

E8. Closed constant evidence yields one identifiable behavioral state and one encounter-token class.

E9. Removing any single closure certificate from the closed constant world produces UNKNOWN_IDENTIFIABILITY; every bounded history's negative/exhaustive information is necessary to certify universal sameness in this challenge.

E10. Opaque encounter-token relabelling preserves identifiability status and transforms the identifiable history quotient/token classes equivariantly.

E11. Consequence-token relabelling preserves identifiability status and every identifiable behavioral structure.

E12. Positive-only parity and future-dependent worlds remain non-identifiable even though every bounded history has been observed at least once.

E13. Closed singleton supports identify determinism; open singleton observations do not identify determinism.

E14. A conflict-free finite sample stream and a genuinely branching support law can be observationally compatible; repeated agreement alone is not a proof of impossibility of unseen outcomes.

E15. Incomplete evidence-packet authority or verifier ablation authorizes no epistemic conclusion.

E16. No hidden machine state, statistical threshold, probability prior, candidate state count, graph/factor/quotient catalogue, or hidden challenge-family name occurs in the frozen executable kernel.

## Claim boundary

A pass would not solve induction in an unrestricted universe.

V47 still supplies:

- a finite encounter alphabet;
- finite sequential order;
- a finite known consequence alphabet;
- a bounded history/future horizon;
- exact positive observation records;
- optional trusted CLOSED certificates when exhaustive support is known.

What a pass can establish is the intended epistemic floor:

> without an additional assumption that turns non-observation into evidence of impossibility, finite positive observations alone do not generally identify a unique behavioral ontology. The correct result is an explicit version space or UNKNOWN. A behavioral floor becomes knowledge only when every still-compatible consequence law agrees on it.

This experiment therefore tests not another representational primitive, but the boundary between consequence that has been observed and consequence that has been ruled out.
