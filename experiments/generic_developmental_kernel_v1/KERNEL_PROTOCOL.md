# Generic Developmental Kernel V1 — Frozen Kernel Protocol

## Question

Can one frozen developmental kernel, written before the challenge pack exists, correctly route a heterogeneous sequence of finite obligations without being told which internal level is inadequate?

The kernel must distinguish and handle, through one unchanged control law:

- no change when the present already suffices;
- compositional constructor/representation repair;
- higher-order relational binding repair;
- non-canonical repair selection by independently frozen future consequence;
- stateful scope relaxation with preservation of prior consequences;
- reuse of previously retained repairs on reset contexts;
- conservative UNKNOWN when the admitted search is explicitly not complete.

## Kernel constitution

The kernel receives only:

1. an initial state, or a previously retained state for the same context;
2. opaque state-transforming actions;
3. an external evaluator returning `accepted`, `loss`, `protected_ok`, and an optional witness;
4. optional future evaluators;
5. optional held-out evaluator;
6. a finite search depth and a completeness flag.

It is not given:

- an expected repair;
- a repair category;
- a challenge type;
- a target action sequence;
- a preferred internal level to modify.

The kernel law is frozen as:

1. Verify the current state.
2. If it already passes, make no change.
3. Try retained mechanisms before rediscovery.
4. Otherwise enumerate reachable states level-completely by edit cost.
5. Admit only externally accepted states that preserve protected consequences.
6. If multiple minimum states survive, use only frozen future consequence to eliminate them.
7. If exactly one state survives, retain its repair program.
8. If multiple survivors remain, return `UNKNOWN_NONCANONICAL`.
9. If no repair is found, return `CERTIFIED_NO_REPAIR_IN_CLASS` only when completeness is supplied; otherwise return `UNKNOWN_SEARCH`.
10. Run held-out checks only after selection; they never participate in choosing the repair.

Equivalent syntactic programs are collapsed to the same semantic state.

## Temporal freeze

`kernel.py` is committed and hashed before any challenge-pack code is added.

Subsequent workflow execution must verify the exact SHA-256 of the frozen kernel before running any challenge.

The challenge pack may use heterogeneous finite domains, but the kernel cannot be modified after seeing them.

## Claim boundary

A pass would establish a bounded, finite, challenge-blind developmental control kernel over a supplied action substrate.

It would **not** establish unrestricted action invention, unrestricted completeness, designerless subject selection, or open-ended general intelligence.

The remaining designed boundary would be the generic edit substrate and the external verifiers.
