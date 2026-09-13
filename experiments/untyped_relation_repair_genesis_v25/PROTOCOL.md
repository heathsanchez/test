# Untyped Relation Repair Genesis V25 — Frozen Protocol

## Dependency

V24 removed all edit primitives and constructed candidate repairs directly as total maps.

V25 removes that remaining candidate type.

## Question

Can totality, functionality, and bijection be left entirely to verification rather than supplied as the candidate language?

The target is:

    unrestricted finite relations
      -> certified residual
      -> exhaustive relation construction
      -> verifier recognizes transformation structure
      -> minimum consequence-preserving repair
      -> recurring difference schema
      -> prospective held-out prediction.

## Primitive candidate language

Let P be the finite presentation carrier.

A candidate is any finite binary relation

    R subseteq P x P.

No total-map, function, bijection, permutation, SET, FLIP, assignment, redirect, or swap type is built into candidate generation.

The frozen constructor exhausts every relation bitmask:

    2^(|P|^2)

relations.

An EDGE(source,target) is only a relation fact.

## Independent verifier

Only after a relation has been constructed does verification ask whether it is:

1. total: every source has at least one target;
2. functional: every source has at most one target;
3. bijective: every source has exactly one target and every target exactly one preimage;
4. residual-discharging;
5. consequence-preserving;
6. novel outside the exhausted current transformation language L0.

Thus transformation structure is an admitted property, not a generation type.

## Current language and residual

As before, first exhaust

    L0 = Perm(X) x Perm(C)

on P=XxC.

Only a certified same-consequence/different-orbit residual authorizes relation search.

## Cost

The current relation is identity I.

After construction, candidate distance is measured extensionally:

    d(R,I)=|R symmetric_difference I|.

This does not guide relation generation; all relations are exhausted.

Among verifier-clean repairs, retain the globally minimum distance frontier.

## Derived recurring structure

For an admitted relation R, derive:

    Diff(I,R)=I symmetric_difference R.

Represent it as:

    DIFF(EDGE(...), ...).

Two independent relabelled training worlds are structurally anti-unified with the same generic first-order LGG discipline as V22-V24.

The learned schema is evaluated prospectively on a third world before its unrestricted relation search.

## Minimal Developmental Algorithm

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE.

## Required post-freeze gates

### U1 — unrestricted relation universe
The frozen candidate generator enumerates all 2^(|P|^2) binary relations.

### U2 — no transformation candidate typing
Candidate generation contains no total/function/bijection/permutation constraint.

### U3 — current language exhausted before growth
L0 is exhausted and a certified residual exists before unrestricted relation search.

### U4 — verifier recognizes structure
The accepted minimum relation is total, functional, bijective, residual-discharging, consequence-preserving, and novel.

### U5 — exact global minimum
All unrestricted relations are exhausted and the minimum extensional repair distance is proved exactly.

### U6 — non-transformations are genuinely considered
The search must record rejecting relations that fail totality/functionality/bijection, demonstrating that those properties were not prefiltered.

### U7 — independent relabelled recovery
A second independently relabelled world repeats the unrestricted search and recovers the same minimum distance.

### U8 — recurring difference schema
Generic anti-unification produces a non-ground schema with repeated variable structure.

### U9 — prospective held-out prediction
The schema predicts a held-out difference signature before held-out unrestricted relation search.

### U10 — held-out exhaustive confirmation
The held-out unrestricted search confirms the predicted difference as globally minimum and verifier-clean.

### U11 — wrong consequence binding fails
Unequal-consequence endpoints admit no verifier-clean repair.

### U12 — no residual, no unrestricted repair search
If L0 already realizes consequence equivalence, no repair search is authorized.

### U13 — composition exact
The recovered transformation relation composes exactly and preserves consequence.

### U14 — incomplete authority
Missing consequence cells return UNKNOWN_AUTHORITY.

### U15 — verifier ablation
Without verification, no relation is admitted as a repair.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> total/function/bijection structure need not be supplied as the repair search space. It can be recognized after unrestricted relation construction by independent verification, while consequence and minimum extensional change select the repair.

This would make even V24's total-map typing a convenience rather than a necessary developmental primitive.

## Claim boundary

A pass does NOT establish:
- unrestricted infinite relation search;
- autonomous invention of EDGE/relation itself;
- continuous or physical transformations;
- quantum structure;
- autonomous invention of the verifier.

The next boundary is the relational carrier itself:
can relation facts / arity be generated from a still lower distinction-and-composition substrate?
