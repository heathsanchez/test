# Meta-Repair Constructor Genesis V22 — Frozen Protocol

## Dependency

V21 established bounded transformation-language growth from certified consequence residuals.

Pinned lower-layer result:

- V21 branch: `residual-generated-transformation-language-v21`
- V21 successful run: `34756086567`
- V21 head: `51f32776f118de9be9b3248c6cae28759392d8d4`
- V21 verdict:
  `VERIFIED_RESIDUAL_GENERATED_TRANSFORMATION_LANGUAGE_GROWTH_AND_QUOTIENT_CONTRACTION`

V21 still supplied one generic repair constructor:

    same consequence + different orbit
        -> JOINT_SWAP(a,b).

V22 removes that constructor.

## Question

Can the repair constructor itself be generated from a lower, generic edit substrate?

The target is:

    certified residual
      -> exhaustive edit-program synthesis
      -> minimum verified repair program
      -> recurrence across independent residuals
      -> generic structural anti-unification
      -> compiled anonymous repair schema
      -> zero-search repair on a held-out residual.

No SWAP, TRANSPOSITION, EXCHANGE, CYCLE, PERMUTATION-CONSTRUCTOR, or residual-specific repair macro is supplied to the frozen kernel.

## Current representation and residual

As in V21, the present world is a finite consequence table

    V : X x C -> K

and the current transformation language L0 is exhausted.

A certified residual provides two atomic presentations

    a,b in P = X x C

such that:

    V(a) = V(b)

but the current language keeps them in different orbits.

The developmental obligation is only:

    construct some new consequence-preserving transformation T
    that maps a to b.

The kernel is not told what form T should have.

## Lower edit substrate

A transformation candidate is represented extensionally as a total map

    f : P -> P.

The starting map is identity:

    f_0(p) = p.

The only primitive meta-edit is:

    SET(source, target)

meaning:

    overwrite the image of one source presentation.

A finite edit program is a sequence:

    SET(s1,t1); ...; SET(sk,tk).

Applying a program to identity yields a candidate total map.

No constraint in the edit language itself says:
- bijection;
- swap;
- symmetry;
- inverse;
- cycle.

Those properties, if they arise, are consequences of verification.

## Repair verifier

A synthesized edit program is admitted iff its resulting map T satisfies all of:

1. totality: every presentation has one image;
2. bijection: T is one-to-one and onto;
3. residual discharge:

       T(a) = b;

4. exact consequence preservation:

       V(T(p)) = V(p)
       for every presentation p;

5. novelty:
   T is not representable in the exhausted current transformation language L0.

The verifier is independent of the edit search.

## Exact minimum synthesis

Search edit programs by increasing number of distinct edited sources.

For a fixed k, enumerate all k-source subsets and all target assignments.

Reject duplicate-source programs canonically.

The first verified repair depth k is the exact minimum edit depth.

Preserve every distinct minimum verified repair program.

No lexical preference may erase equal-cost non-canonicity.

## Constructor genesis by generic structural anti-unification

A repair program is represented as a first-order term:

    SEQ(
      SET(source_1,target_1),
      ...
    ).

After minimum repair programs are independently synthesized for at least two residuals with disjoint concrete presentation labels, the frozen meta-compiler computes their least general generalization (LGG) structurally.

Generic anti-unification rules:

- identical symbols remain identical;
- matching constructors recurse position-wise;
- differing constants become variables;
- repeated disagreement pairs reuse the same variable;
- incompatible constructor shapes return NO_SCHEMA.

There is no rule specific to SET order, swaps, residuals, or transformations.

Example shape only:

    instance 1: SEQ(SET(a,b),SET(b,a))
    instance 2: SEQ(SET(c,d),SET(d,c))

may structurally yield:

    SEQ(SET(V0,V1),SET(V1,V0)).

If that happens, the swap-like schema has been discovered rather than supplied.

## Schema admission

An LGG schema is compilable only if:

1. it comes from at least two independently synthesized verified repairs;
2. exact instantiation reproduces every training repair;
3. it preserves variable-equality structure;
4. it has fewer concrete constants than the collected instances;
5. replay on training residuals remains verifier-clean.

The schema receives an anonymous content-derived ID.

No human-readable semantic name is stored.

## Held-out execution

A held-out residual is supplied after schema compilation.

Warm execution:

1. bind schema variables using only the held-out residual obligation T(a)=b;
2. instantiate the learned schema;
3. run the same repair verifier;
4. if verified, accept with zero edit-program acquisition search.

Cold zero-search execution must return UNKNOWN_REPAIR_SCHEMA.

Cold execution with search enabled may rediscover a minimum repair program.

## Minimal Developmental Algorithm

The governing law remains:

    EXECUTE
    -> VERIFY
    -> DIAGNOSE
    -> CONSTRAIN
    -> RESTRUCTURE
    -> CHOOSE
    -> COMPILE
    -> UPDATE.

### EXECUTE
Use the current transformation language.

### VERIFY
Exhaust it and verify the residual.

### DIAGNOSE
Produce the same-consequence / different-orbit witness.

### CONSTRAIN
Expose only the generic SET edit substrate plus the residual obligation.

### RESTRUCTURE
Exhaust minimum edit programs and independently verify them.

### CHOOSE
Preserve the full minimum repair frontier.

### COMPILE
After independent recurrence, anti-unify verified programs into an anonymous schema.

### UPDATE
Use the schema prospectively, subject to replay verification.

## Required post-freeze gates

### M1 — no swap constructor in frozen core

The executable frozen core contains no SWAP/EXCHANGE/TRANSPOSITION/CYCLE repair primitive or helper.

The only transformation-edit primitive is SET(source,target).

### M2 — exact minimum repair synthesis

On the first hidden residual, exhaustive edit search must prove the minimum edit depth.

At least one valid repair must require depth > 1.

### M3 — minimum repair is not pre-shaped

The successful repair must emerge from enumeration over generic source/target assignments.

No residual-specific target program is inserted by the challenge.

### M4 — independent verification

Every synthesized candidate accepted as a repair must independently satisfy:
- bijection;
- residual discharge;
- exact consequence preservation;
- novelty outside L0.

### M5 — independent second repair

A second, independently relabelled residual must synthesize a structurally corresponding minimum repair without reusing the first program.

### M6 — generic LGG schema emerges

Anti-unification of the two independently synthesized programs must produce a non-ground schema with repeated variable structure.

The frozen anti-unifier must be generic first-order structural anti-unification.

### M7 — schema is strictly more abstract than instances

The compiled schema must contain fewer concrete presentation constants than either training instance and must exactly instantiate back to both.

### M8 — held-out warm zero-search transfer

On a third relabelled residual:
- warm schema instantiation succeeds;
- the repair verifier accepts it;
- edit-program acquisition search count is zero.

### M9 — cold zero-search control

Without the learned schema and with acquisition search disabled, the same held-out residual returns UNKNOWN_REPAIR_SCHEMA.

### M10 — cold search control

Without the learned schema but with acquisition search enabled, the held-out residual rediscovers a minimum verifier-clean repair.

### M11 — schema ablation

Deleting the compiled schema restores UNKNOWN_REPAIR_SCHEMA under zero-search conditions.

### M12 — wrong binding fails

Binding the learned schema to endpoints with unequal consequence must fail replay verification.

### M13 — shape-mismatch control

A verified repair program with a different edit-program shape must not be forced into the learned schema; generic anti-unification may return a broader schema or NO_SCHEMA, but replay must prevent false constructor transfer.

### M14 — no residual, no constructor growth

If the current transformation language already realizes the complete consequence quotient, no edit synthesis or schema acquisition is authorized.

### M15 — incomplete authority

Missing consequence values return UNKNOWN_AUTHORITY.

### M16 — verifier ablation

Without consequence/bijection verification, no repair program or schema may be admitted.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> a repair constructor need not be predeclared at the transformation level. Generic pointwise edit programs can be synthesized from certified residuals, and repeated verified repair structure can be abstracted into a reusable constructor schema by generic structural anti-unification.

This would move the developmental boundary from:

    generate transformation instances

to:

    generate a reusable transformation-construction rule.

## Claim boundary

A pass does NOT establish:
- unrestricted program synthesis;
- autonomous invention of SET itself;
- universal meta-learning;
- natural-world repair schemas;
- continuous transformations;
- quantum structure;
- that first-order anti-unification is the final meta-language.

The next boundary after a pass is lower still:

    can SET / pointwise editing itself be generated
    from a more primitive relation-construction substrate?
