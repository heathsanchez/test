# Epistemic Floor V47b — Corrected Final-Boss Protocol

## Question

What remains when complete consequence authority is removed, but the behavioral-floor machinery itself is kept exact?

V47b receives only finite positive encounter evidence plus optional support-closure certificates.

It does not receive a complete consequence table unless the evidence itself closes every relevant history.

The scientific kernel is frozen before hidden evidence streams are committed.

## Evidence semantics

For every bounded encounter history h, let O(h) be the set of consequence tokens actually observed.

If h is OPEN, every nonempty support S(h) satisfying

    O(h) ⊆ S(h) ⊆ Y

remains epistemically possible.

If h is CLOSED, then

    S(h) = O(h)

exactly.

Thus finite evidence induces an exact finite version space of bounded consequence-support laws.

Repeated identical positive observations do not by themselves rule out unseen consequences.

## Behavioral floor for one completed support law

For one completed law S:

- histories are compared by future support signatures;
- the first future depth whose quotient is both right-congruent and stable one step deeper is the bounded behavioral floor;
- encounter-token classes are derived by identical action on every behavioral state.

No state count, memory depth, transition model, deterministic law, or branching law is proposed in advance.

## Epistemic identifiability

V47b asks whether every law still compatible with the finite evidence yields the same behavioral floor.

If two compatible completions disagree, return

    UNKNOWN_IDENTIFIABILITY

with both complete support laws as explicit witnesses.

If all compatible completions agree on:

- floor future depth;
- history equivalence;
- induced transition maps;
- encounter-token classes,

return

    VERIFIED_IDENTIFIABLE_BEHAVIORAL_FLOOR.

UNKNOWN therefore means that the ontology itself is not identifiable from the current evidence.

## Exactness

The kernel first compares minimal-support and maximal-support compatible completions.

If those already disagree, non-identifiability is proved immediately.

If they agree, the kernel exactly enumerates the remaining version space when it contains at most 65,536 laws.

If the exact space is larger, the result is a resource-bounded UNKNOWN rather than an unjustified identification.

## Forced local facts

Some facts may be knowable before the global behavioral floor is identifiable.

In particular:

- observing two different consequence tokens for the same history forces branching support there;
- a CLOSED singleton support forces determinism at that particular history.

These are reported separately.

## Corrected primary finite scope

Primary hidden challenges use:

- two opaque encounter tokens;
- a binary consequence alphabet;
- prefix histories through depth 3;
- possible futures through depth 2;
- all 63 histories of total length at most 5.

The larger prefix window is deliberate: it allows every state of the four-state challenge to have a representative strictly inside the transition-check boundary.

## Post-freeze challenge family

Only after freeze:

1. PARITY OPEN:
   every one of the 63 bounded histories has one conflict-free observed consequence, but every support remains open.
   A deterministic two-state completion and a maximally branching one-state completion must both remain compatible.

2. PARITY REPEATED OPEN:
   the same positive observations repeated many times.
   The epistemic result must remain unchanged.

3. PARITY CLOSED:
   exactly the same positive outcomes, all supports closed.
   The two-state depth-0 behavioral floor becomes identifiable.

4. FUTURE FOUR CLOSED:
   exact closed support evidence from a hidden four-state process.
   The identifiable floor must contain four states and require future depth 1.

5. FUTURE FOUR OPEN:
   identical positive outcomes to (4), no closure.
   The floor must remain non-identifiable.

6. FORCED BRANCHING OPEN:
   both consequence tokens are actually observed at one history while global support remains open.
   Branching there is knowable, but the global floor remains UNKNOWN.

7. CONSTANT CLOSED:
   exact one-state behavioral floor.

8. CONSTANT SINGLE-CLOSURE ABLATIONS:
   remove exactly one closure certificate at a time.
   The experiment does not assume every certificate matters.
   Instead it discovers the closure-critical set.
   For the constant depth-0 floor, histories of total length at most 4 are predicted to be critical because they participate in the horizon-0/stability-to-1 certificate; depth-5 histories are predicted to be irrelevant to that floor.

9. opaque encounter-token relabellings and consequence-token relabellings.

## Frozen gates

F1. Frozen scientific core remains byte-identical.

F2. PARITY OPEN returns UNKNOWN_IDENTIFIABILITY with explicit compatible witnesses:
    - deterministic two-state depth-0 floor;
    - branching one-state depth-0 floor.

F3. PARITY REPEATED OPEN has the same version-space cardinality, status, and witness floor pair as PARITY OPEN despite repeated agreement.

F4. PARITY CLOSED collapses to one compatible law and yields an identifiable two-state depth-0 floor with determinism identifiable.

F5. FUTURE FOUR CLOSED collapses to one compatible law and yields an identifiable four-state floor at future depth 1.

F6. FUTURE FOUR OPEN, with the exact same positive outcomes, returns UNKNOWN_IDENTIFIABILITY.

F7. FORCED BRANCHING OPEN certifies the designated history as branching while the global floor remains UNKNOWN_IDENTIFIABILITY.

F8. CONSTANT CLOSED yields one identifiable state and one encounter-token class.

F9. The single-closure ablation map for CONSTANT CLOSED is discovered correctly:
    histories of length ≤ 4 are closure-critical and restore UNKNOWN_IDENTIFIABILITY;
    histories of length 5 are noncritical for the depth-0 floor and preserve the one-state identifiable floor, while determinism itself becomes unidentifiable.

F10. Opaque encounter-token relabelling preserves identifiability status and transforms identifiable history equivalence/token classes equivariantly.

F11. Consequence-token relabelling preserves identifiability status and every identifiable behavioral structure.

F12. Every bounded history may have been observed at least once while the global ontology remains non-identifiable.

F13. Closed singleton support can identify determinism; open conflict-free repetition cannot.

F14. Positive observations can force branching when conflicting consequences are actually witnessed, but cannot prove absence of unseen branches without closure.

F15. Incomplete evidence-packet authority or verifier ablation authorizes no epistemic conclusion.

F16. No hidden machine state, probability prior, statistical threshold, candidate state count, graph/factor/quotient catalogue, or hidden challenge-family name occurs in the frozen executable kernel.

## Claim boundary

A pass does not solve unrestricted induction.

V47b still supplies:

- a finite encounter alphabet;
- sequence order;
- a finite known consequence alphabet;
- a bounded history/future universe;
- exact positive observation records;
- trusted CLOSED certificates when support exhaustiveness is externally known.

What a pass can establish is the intended epistemic floor:

> finite positive evidence alone generally does not identify a unique behavioral ontology, even when every bounded history has been observed and the observations are perfectly conflict-free. The correct answer is UNKNOWN unless every still-compatible bounded consequence law agrees. What turns a behavioral floor from a model into knowledge is not repetition by itself, but elimination of alternative consequence supports through warranted closure/negative information.

This is the boundary between observed consequence and ruled-out consequence.
