# Consequence-Earned Tuple Arity V26 — Frozen Protocol

## Dependency

V25 removed total/function/bijection typing from repair generation by exhaustively searching all binary relations.

V26 removes the remaining binary-relation assumption.

## Question

Can the arity of the relational carrier itself be earned from consequence?

The target is:

    atomic presentations
      -> generic tuple construction
      -> arity-1 exhaustively fails
      -> certified expressivity residual
      -> minimally expand tuple arity
      -> arity-2 succeeds
      -> no higher arity is admitted.

## Primitive constructive language

Let P be the finite presentation carrier.

The learner is given only:
- atomic presentation tokens p in P;
- generic ordered tuple construction;
- finite set formation over tuples;
- a current maximum authorized tuple arity D.

No RELATION, EDGE, source, target, function, bijection, permutation, SET, FLIP, swap, or binary-relation primitive is supplied to the candidate generator.

At arity r, the candidate universe is every subset of P^r:

    S subseteq P^r.

The generator therefore exhausts:

    2^(|P|^r)

candidate tuple sets.

## Generic interpretation search

The verifier does not assume tuple coordinates have semantic roles.

For a candidate set S of arity r, it searches every ordered pair of distinct coordinate positions:

    (i,j), i != j.

For each role assignment, it projects every tuple t in S to:

    (t_i, t_j)

and asks whether the projected binary incidence structure is:
- total;
- functional;
- bijective;
- residual-discharging;
- consequence-preserving;
- novel outside exhausted L0.

If no pair of coordinates exists, no relation interpretation is available.

Thus source/target roles are verifier-selected, not candidate-language primitives.

## Developmental arity

Initial authorized arity:

    D = 1.

Search all candidates at arity 1.

If none verifies and the search is complete, emit:

    CERTIFIED_ARITY_INADEQUACY.

Only then may the constructive language expand minimally:

    D -> D+1.

Stop at the first arity with a verifier-clean repair.

No larger arity is searched or admitted once sufficiency is reached.

## Cost

Within a successful arity, compare the verifier-clean projected relation to identity and minimize extensional symmetric-difference distance.

Arity is lexicographically prior:

    (minimum sufficient arity, minimum extensional change).

## Current-language residual

As in V21-V25, L0 is first exhausted on P=XxC.

Tuple-language growth is authorized only if verified consequence-equivalent presentations remain in distinct L0 orbits.

## Required post-freeze gates

### A1 — no binary relation primitive in candidate generation
Frozen candidate generator contains only generic tuples and tuple-set enumeration.

### A2 — L0 residual precedes tuple search
Current transformation language is exhausted and a certified residual exists first.

### A3 — arity 1 is exhaustively inadequate
Every subset of P^1 is checked and no verifier-clean repair exists.

### A4 — arity growth is residual-authorized
Arity 2 is searched only after certified complete failure at arity 1.

### A5 — arity 2 succeeds exactly
Every subset of P^2 is exhausted; at least one verifier-clean repair exists.

### A6 — minimum arity is 2
No arity above 2 is searched once arity 2 succeeds.

### A7 — roles are verifier-selected
The accepted candidate is interpreted by an ordered coordinate-role pair chosen during verification, not by candidate construction.

### A8 — exact minimum change within minimum arity
The globally minimum verifier-clean arity-2 repair has exact extensional distance 4 from identity.

### A9 — non-relational tuple sets are genuinely considered
Search records rejecting arity-2 tuple sets that fail totality/functionality/bijection under every role assignment.

### A10 — independent relabelled recovery
A separately relabelled world again fails arity 1 and succeeds first at arity 2 with the same minimum distance.

### A11 — arity-growth ablation
If arity expansion is disabled, the main challenge stops at CERTIFIED_ARITY_INADEQUACY rather than inventing a binary relation.

### A12 — no residual, no tuple-language growth
If L0 already realizes consequence equivalence, no tuple search occurs.

### A13 — incomplete authority
Missing consequences return UNKNOWN_AUTHORITY.

### A14 — verifier ablation
Without verification, no tuple structure or arity growth is admitted.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> binary relational structure need not be supplied as the repair candidate type. Generic tuple-set construction can begin at arity 1, and certified consequence failure can authorize the minimum arity increase at which a verifier recognizes transformation structure.

This would make binary relation arity a consequence-earned representational commitment.

## Claim boundary

A pass does NOT establish:
- autonomous invention of tuple construction itself;
- unbounded arity growth;
- natural-world relation discovery;
- continuous or quantum structure;
- autonomous invention of the verifier.

The next boundary is tuple formation itself:
can ordered multi-place structure be compiled from repeated lower-level composition rather than supplied as a generic tuple constructor?
