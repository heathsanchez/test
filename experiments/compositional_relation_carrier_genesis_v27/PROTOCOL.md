# Compositional Relation-Carrier Genesis V27 — Frozen Protocol

## Dependency

V26 established that binary relational arity can be consequence-earned from a generic tuple-set language: arity 1 was exhausted, certified inadequate, and only then did arity 2 become authorized.

V27 removes the generic tuple constructor itself.

## Question

Can the binary carrier required for a transformation repair arise from repeated composition of atomic presentation symbols, rather than from a supplied tuple/pair constructor?

The target is:

    atomic symbol
      -> complete failure at one-symbol facts
      -> certified compositional inadequacy
      -> authorize one more generic composition
      -> two-symbol facts
      -> verifier recognizes a relation
      -> stop.

## Primitive construction language

Let P be the finite anonymous presentation carrier.

The only syntax is:

    Expr ::= ATOM(p) | CAT(Expr, ATOM(p))

where p is an anonymous presentation token.

There is no:
- tuple constructor;
- pair constructor;
- RELATION or EDGE primitive;
- source/target role;
- function/bijection/permutation candidate type;
- SET/FLIP/swap repair operation.

CAT is the same generic finite sequential composition idea already used for phrase formation. It has no relational semantics.

The width of an expression is the number of atomic leaves.

At authorized width d, the construction engine generates every expression of exactly width d by repeated CAT from atoms.

A candidate present is any finite set of those expressions.

For |P|=n the candidate count at width d is therefore:

    2^(n^d).

## Verifier interpretation

Only after a candidate expression-set has been constructed does the verifier inspect it.

For width d, the verifier flattens each expression to its ordered atomic leaves and tries every ordered pair of distinct leaf positions:

    (i,j), i != j.

For each role assignment it projects every expression e to:

    (leaf_i(e), leaf_j(e))

and tests whether the induced incidence structure is:
- total;
- functional;
- bijective;
- residual-discharging;
- consequence-preserving;
- novel outside the exhausted current transformation language L0.

The generator knows none of these roles or properties.

## Developmental width

Initial authorized width:

    d = 1.

Exhaust every one-symbol candidate set.

If none verifies, emit:

    CERTIFIED_COMPOSITIONAL_INADEQUACY.

Only then may CAT be used one additional time:

    d -> d+1.

Stop at the first sufficient width.

No width above the first sufficient width is searched or admitted.

## Current-language residual

As in V21-V26, first exhaust:

    L0 = Perm(X) x Perm(C)

on the reified presentation carrier P=XxC.

Compositional growth is authorized only if a complete same-consequence / different-L0-orbit residual exists.

## Cost

Width is lexicographically prior.

Within the first sufficient width, minimize the verifier-recognized transformation's extensional symmetric-difference distance from identity.

## Required post-freeze gates

### C1 — no tuple/pair/relation constructor
The frozen candidate generator contains only ATOM and CAT expression construction plus finite set enumeration.

### C2 — L0 residual precedes construction growth
L0 is exhausted and a certified consequence residual exists before compositional widening.

### C3 — width 1 is exhaustively inadequate
All 2^|P| sets of atomic expressions are checked and none can be interpreted as a repair.

### C4 — CAT growth is consequence-authorized
Width 2 is generated only after complete width-1 failure.

### C5 — width 2 is exhaustively sufficient
All 2^(|P|^2) sets of two-atom composed expressions are checked; verifier-clean repairs exist.

### C6 — minimum sufficient width is 2
No width >2 is searched after width 2 succeeds.

### C7 — relational roles are verifier-selected
The candidate language does not designate source/target; verifier chooses an ordered pair of leaf positions.

### C8 — exact minimum repair within minimum width
The globally minimum verifier-clean width-2 repair has extensional distance 4 from identity.

### C9 — non-relational compositions are genuinely considered
Width-2 search records candidates rejected for failing totality/functionality/bijection under all role assignments.

### C10 — independent relabelled recovery
A separately relabelled world again fails width 1 and first succeeds at width 2 with the same minimum distance.

### C11 — composition ablation
If CAT growth is disabled, the main world stops at CERTIFIED_COMPOSITIONAL_INADEQUACY.

### C12 — no residual, no composition growth
If L0 already realizes consequence equivalence, no expression-set search is authorized.

### C13 — incomplete authority
Missing consequence returns UNKNOWN_AUTHORITY.

### C14 — verifier ablation
Without verification, no composed carrier is admitted.

### C15 — agreement with tuple semantics is derived, not assumed
For the accepted width-2 expression set, flattening the composed syntax yields exactly the verifier-recognized binary incidence structure; no tuple object is stored in the candidate language.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> the ordered two-place carrier needed for relation-like repair need not be supplied as a tuple primitive. It can be realized by generic composition of atomic symbols, with consequence authorizing the first composition depth at which independent verification recognizes transformation structure.

This would connect the phrase/grammar branch and the relation/symmetry branch through the same generic operation:

    compose atoms -> verify recurring consequence -> reify useful structure.

## Claim boundary

A pass does NOT establish:
- autonomous invention of CAT itself;
- unbounded syntax growth;
- natural-language or natural-world relation discovery;
- continuous or quantum structure;
- autonomous invention of the verifier.

The next boundary is CAT itself: whether generic composition can be selected/generated from an even weaker transition/relation substrate rather than supplied.
