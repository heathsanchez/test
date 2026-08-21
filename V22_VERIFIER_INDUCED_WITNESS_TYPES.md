# V22 — Verifier-Induced Witness Type Formation

## Frozen residual from V21

V21 established that an intensional existential viability law over a supplied witness type is sufficient and causally necessary in its finite matched-pair setting. The remaining scaffold is the supplied ontology itself.

## Question

Can the system induce the witness type needed by the V21 law from verifier-visible substitutability behavior rather than receiving `Theta_same` / `Theta_other` labels?

## Operational definition

For opaque witness mechanisms `w_i,w_j`, define

`w_i ~dev w_j`

iff substituting them into every frozen developmental context produces exactly the same verifier-visible result.

The finite context carrier is:

- CLOSE
- PRESERVE
- COMPOSE
- ABLATE
- RETAIN

The induced witness types are the quotient classes under `~dev`. Hidden semantic type labels exist only for final audit and are never visible to the learner.

## Preregistered gates

1. Supplied witness type labels are absent from the learner.
2. The verifier-induced substitutability quotient is constructed.
3. The induced quotient matches the hidden semantic substitutability classes.
4. Every declared context is necessary to recover the full quotient.
5. The minimum action policy operates on an induced quotient class, not a mechanism name.
6. Leave-one-positive-mechanism-out transfer is 100%.
7. Every held-out action is independently CompleteCover-verified.
8. Type/context erasure destroys alpha-invariant transfer.
9. Noncausal and preservation-violating controls are rejected.

The umbrella gate is `VERIFIER_INDUCED_WITNESS_TYPE_FORMATION_GATE`.

## Boundary

This is a finite exact test with a supplied substitution-context carrier, exact verifier, finite policy grammar, and finite episode corpus. It does **not** establish automatic discovery of the adequacy map or the context family itself. That remains the next frontier if V22 passes.
