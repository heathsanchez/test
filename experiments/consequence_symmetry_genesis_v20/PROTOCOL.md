# Consequence-Symmetry Genesis V20 — Frozen Protocol

## Question

Can symmetry, identity classes, symmetry breaking, and consequence-table compression emerge from a generic transformation language plus verified consequence, without supplying geometry, rotations, reflections, groups, orbit labels, objects, boundaries, or named invariants?

V20 tests the reduction:

    transformation + verified consequence
        -> symmetry
        -> orbits / identity classes
        -> quotient compression
        -> broken symmetry / new distinction.

The developmental law remains the Minimal Developmental Algorithm:

    EXECUTE -> VERIFY -> DIAGNOSE -> CONSTRAIN
    -> RESTRUCTURE -> CHOOSE -> COMPILE -> UPDATE

with the standing rule:

    preserve the largest consequence-invisible transformation structure
    that replay verification permits;
    break it only when consequence detects a difference.

## Primitive world interface

A complete finite world is only:

- an anonymous present carrier X with |X| = n;
- an anonymous continuation/test carrier C with |C| = m;
- a finite consequence alphabet K;
- a complete table

      V : X x C -> K.

No coordinates, geometry, adjacency, object IDs, group names, or human feature labels are visible to the learner.

## Primitive transformation language

The only transformation atoms are generic label transpositions:

    SWAP_X(i,j)
    SWAP_C(p,q)

for arbitrary distinct anonymous labels.

A composite transformation acts as a pair of bijections:

    T = (sigma_X, sigma_C)

and is built by composition of transpositions.

No ROTATE, REFLECT, TRANSLATE, SCALE, PERIOD, OBJECT, BOUNDARY, GROUP, or ORBIT primitive exists.

The generic structural cost of a transformation is the minimum number of arbitrary transpositions needed to realize both permutations:

    cost(T)
      = n - cycles(sigma_X)
      + m - cycles(sigma_C).

The identity has cost 0.

## Consequential symmetry

A transformation T is authorized as a symmetry iff exact complete authority verifies:

    for every x in X and c in C,

        V(sigma_X(x), sigma_C(c)) = V(x,c).

This definition is operational and consequence-relative.

Nothing is called symmetric because of visual, geometric, algebraic, or naming information.

## Developmental process

### EXECUTE

Begin with only the identity transformation.

Thus every table cell is initially its own consequential presentation.

### VERIFY

Enumerate generated transformations by increasing generic structural cost.

Replay each against the complete consequence table.

### DIAGNOSE

A verified non-identity transformation proves that distinctions in raw presentation are redundant for admitted consequence.

A previously compiled transformation that fails replay is a certified symmetry-breaking residual.

### CONSTRAIN

For contraction:
retain only exact consequence-preserving transformations.

For symmetry breaking:
remove every retained transformation that fails the new complete consequence table.

### RESTRUCTURE

Close verified transformations under composition and inverse.

Construct:
- state orbits;
- continuation/test orbits;
- cell orbits under simultaneous action

      (x,c) -> (sigma_X(x), sigma_C(c)).

### CHOOSE

Search exhaustively for minimum generator sets whose closure equals the full verified automorphism group.

Cost is lexicographic:

    (# generators, total transposition cost).

If several minimum generator bases remain, preserve all.

No syntactic name decides between equal lawful bases.

### COMPILE

Compile:
- anonymous minimum generator frontier;
- exact group closure;
- cell-orbit representative consequences;
- provenance / verification evidence.

### UPDATE

Use the compiled symmetry description to reconstruct the complete consequence table from orbit representatives.

Replay verification remains mandatory.

## Consequence quotient / compression

If G is the verified transformation group, two cells are equivalent iff they lie in the same G-orbit:

    (x,c) ~_G (x',c')
    iff
    some g in G maps (x,c) to (x',c').

Because every g preserves consequence, every cell orbit must have one consequence value.

The quotient representation stores one value per cell orbit.

Compression ratio:

    raw cells / orbit representatives.

This is a consequence-preserving compression, not a visual pattern score.

## Broken symmetry

Given a new world with the same anonymous interface but modified consequence:

1. replay the previously compiled generators;
2. reject every generator whose transformation changes verified consequence;
3. recompute the lawful closure;
4. recompute state/test/cell orbits.

If a formerly equivalent pair now has different consequence, the old symmetry must break and the quotient must refine.

Thus:

    verified change -> symmetry breaking -> new distinction.

## Post-freeze gates

### S1 — no named symmetry ontology

Frozen core contains only:
- anonymous finite carriers;
- consequence table;
- generic transpositions;
- composition / inverse;
- exact replay.

No geometry or named symmetry operation is supplied.

### S2 — nontrivial symmetry is generated, not named

A hidden post-freeze world must possess a nontrivial consequence-preserving transformation group.

At least one required non-identity symmetry must have transposition cost > 1, proving it requires composition of primitive swaps rather than being a supplied atom.

### S3 — exact automorphism group

Exhaustive generated search must recover exactly all consequence-preserving transformation pairs in the declared finite universe.

Independent brute-force replay must confirm every member and reject every nonmember.

### S4 — minimum generator frontier

The learner must find a minimum generator set for the full verified group.

If multiple equal-cost minimum bases exist, preserve the entire frontier.

### S5 — symmetry orbits compress consequence

Cell-orbit representative values must reconstruct the complete consequence table exactly.

The number of cell orbits must be strictly smaller than the raw cell count.

### S6 — state identity is consequence-relative

At least two raw-present labels must lie in the same state orbit even though their labels differ.

No state label is privileged.

### S7 — relabelling invariance

A separately relabelled copy of the same hidden world must yield the same canonical structural signature:
- automorphism-group order;
- state-orbit size multiset;
- continuation-orbit size multiset;
- cell-orbit size/value multiset;
- minimum generator count/cost.

Raw permutations themselves may differ by conjugation.

### S8 — symmetry breaking

A post-freeze consequence perturbation must invalidate at least one previously lawful generator.

The repaired lawful group must be strictly smaller or its orbit partition strictly finer.

At least one previous cell orbit must split.

### S9 — no false symmetry after breaking

The repaired quotient must reconstruct the perturbed table exactly.

The old compiled quotient must fail exact replay.

### S10 — causal compression ablation

With nontrivial transformation retention disabled, only the identity remains.

Then the number of cell orbits must return to the raw number of cells.

### S11 — composition ablation

If transformation composition is disabled, the learner may use identity and primitive single transpositions only.

The hidden world must require at least one higher-cost composite symmetry for full group recovery, so the full symmetry group cannot be reconstructed.

### S12 — heterogeneous transfer

The same frozen kernel must recover a different automorphism group and orbit structure on a structurally different hidden consequence table.

### S13 — incomplete authority

If any consequence cell is unavailable / authority is incomplete, return UNKNOWN_AUTHORITY rather than certify a symmetry group.

### S14 — consequence ablation

If consequence comparison is disabled, no non-identity transformation is authorized.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> symmetry can be operationally constructed as the set of generic transformations that verified consequence cannot detect; identity classes and quotient compression then arise as transformation orbits, while changed consequence forces symmetry breaking and representational refinement.

This would support the reduction:

    sameness = invariance under consequence-preserving transformation

and

    distinction = broken consequential symmetry.

## Claim boundary

A pass does NOT establish:
- symmetry as a metaphysical primitive;
- Lie groups or continuous symmetry;
- Noether's theorem;
- physical spacetime symmetry;
- quantum symmetry;
- natural-world objecthood;
- that permutation/transposition is the final transformation language;
- autonomous invention of the verifier.

The next boundary after a pass is transformation-language growth:
can certified residuals force the system to invent a new class of transformation rather than receiving finite bijections as its declared transformation substrate?
