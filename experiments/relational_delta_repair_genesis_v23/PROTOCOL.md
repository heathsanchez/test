# Relational Delta Repair Genesis V23 — Frozen Protocol

## Dependency

V22 established that a reusable repair constructor can be compiled from generic pointwise edits:

    SET(source,target)

via exact repair synthesis and generic structural anti-unification.

V23 asks whether SET itself is fundamental.

## Question

Can the V22 repair behavior be recovered with no pointwise assignment primitive at all, using only a lower relational-difference substrate?

The target is:

    identity relation
      -> anonymous relation-incidence differences
      -> exact verified transformation
      -> repeated repair structure
      -> compiled anonymous repair schema
      -> zero-search held-out reuse.

If successful, SET is not required as a primitive of development.

## Primitive substrate

Let P be the finite presentation carrier.

A candidate transformation is represented by its graph:

    R subseteq P x P.

The current transformation begins as the identity relation:

    I = {(p,p) : p in P}.

The only edit-level primitive is a relation-incidence bit:

    FLIP(p,q)

meaning toggle membership of the ordered pair (p,q) in the current relation graph.

A finite delta program is simply a set/sequence of such incidence flips, applied by symmetric difference:

    R_D = I triangle D.

No primitive names or operations corresponding to:
- SET;
- assignment;
- redirect;
- swap;
- exchange;
- transposition;
- cycle;
- row rewrite

exist in the frozen executable core.

## Generic transformation verifier

A synthesized relational delta is admitted only if the resulting relation graph is:

1. total and functional:
   every source has exactly one target;
2. bijective:
   every target has exactly one preimage;
3. residual-discharging:
   the residual source maps to the residual target;
4. consequence-preserving:
   V(source)=V(target) for every graph edge;
5. novel:
   its mapping is outside the exhausted current transformation language L0.

The verifier is independent of delta search.

## Current language and residual

As in V21/V22, the current language is the exhausted factorized language

    L0 = Perm(X) x Perm(C)

acting on P = X x C.

A certified residual is:

    V(a)=V(b)
    but
    orbit_L0(a) != orbit_L0(b).

Only such a residual authorizes relational-delta synthesis.

## Exact minimum delta synthesis

Let B = P x P be the relation-incidence universe.

Search delta subsets D subseteq B by increasing cardinality.

For each D:
- form R_D = I triangle D;
- run the independent transformation verifier.

The first accepted depth is the exact minimum relation-bit repair depth.

Preserve every distinct equal-depth accepted repair.

No repair shape is supplied.

## Generic structural compilation

Each verified delta is represented as a first-order term:

    DELTA(
      BIT(source_1,target_1),
      ...
    ).

After at least two independently synthesized repairs on independently relabelled worlds, compute the least general generalization using the same generic first-order structural anti-unification discipline used in V22:

- same constructors recurse;
- equal atoms remain equal;
- unequal atoms become variables;
- repeated disagreement pairs reuse variables;
- incompatible shapes return NO_SCHEMA.

No rule knows any transformation semantics.

A successful learned schema may therefore discover repeated relation-incidence structure without a supplied assignment macro.

## Held-out use

For a held-out residual:

1. bind schema variables from the residual obligation using matching relational BIT subterms;
2. instantiate the delta schema;
3. reconstruct the relation by symmetric difference from identity;
4. replay the independent transformation verifier.

Warm accepted execution uses zero acquisition search.

Cold zero-search returns UNKNOWN_RELATIONAL_SCHEMA.

## Composition

Verified transformation relations are composable by ordinary relational/function composition.

Composition is not used to smuggle repair structure into the search.

A compiled repair must remain an exact transformation relation under replay and may participate in later composition.

## Minimal Developmental Algorithm

The governing loop remains:

    EXECUTE
    -> VERIFY
    -> DIAGNOSE
    -> CONSTRAIN
    -> RESTRUCTURE
    -> CHOOSE
    -> COMPILE
    -> UPDATE.

## Required post-freeze gates

### R1 — no SET-like primitive in frozen core
Executable frozen code contains no SET/assignment/redirect/swap/exchange/transposition/cycle repair primitive.

### R2 — certified residual precedes growth
L0 is exhausted before relational delta synthesis.

### R3 — exact minimum relation-bit repair
The first hidden residual requires a minimum delta depth strictly greater than 1.
All smaller depths are exhausted.

### R4 — repair is verifier-derived
Every accepted minimum delta yields a total functional bijection, discharges the residual, preserves consequence, and lies outside L0.

### R5 — independent second synthesis
A separately relabelled world independently rediscovers a same-depth repair with full acquisition search.

### R6 — generic anti-unification generates a reusable non-ground relational schema
The two independently synthesized ground deltas compile to a variable-bearing first-order schema.

### R7 — schema is more abstract
The schema contains fewer concrete presentation constants than either training delta and re-instantiates both exactly.

### R8 — held-out warm zero-search transfer
A third relabelled residual is repaired by schema replay with zero delta acquisition search.

### R9 — cold zero-search control
Without compiled schema and with acquisition disabled, held-out returns UNKNOWN_RELATIONAL_SCHEMA.

### R10 — cold search control
Cold search rediscovers an exact minimum relational delta.

### R11 — schema ablation
Removing compiled schema restores UNKNOWN_RELATIONAL_SCHEMA at zero acquisition budget.

### R12 — wrong consequence binding is rejected
Binding schema to endpoints with unequal consequence fails replay.

### R13 — composition is exact
The learned held-out transformation composes through the generic relation/function composer without loss of totality or verifier semantics.

### R14 — no residual, no relational repair growth
If L0 already realizes complete consequence equivalence, no delta synthesis or schema growth is authorized.

### R15 — incomplete authority
Missing consequence cells return UNKNOWN_AUTHORITY.

### R16 — verifier ablation
Without transformation verification, no delta or schema is admitted.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> the pointwise SET edit used in V22 is not required as a primitive. A repair can be synthesized one relation-incidence difference at a time, and repeated verified relational repair structure can compile directly into a reusable constructor.

This would support the stronger reduction:

    relation + distinction + composition + consequence

rather than:

    assignment + consequence.

## Claim boundary

A pass does NOT establish:
- that FLIP / symmetric difference is fundamental;
- unrestricted relation invention;
- continuous transformations;
- physical or quantum symmetry;
- autonomous invention of the verifier.

The next boundary is lower again:

    can relation-incidence change itself be generated from the earlier
    distinction/relation/reification substrate rather than supplied as FLIP?
