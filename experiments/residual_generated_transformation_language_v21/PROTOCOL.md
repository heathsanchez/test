# Residual-Generated Transformation Language V21 — Frozen Protocol

## Dependency

V20 established that, in a bounded finite world, consequence-preserving transformations generate symmetry, orbit quotients, exact compression, and symmetry breaking.

Pinned lower-layer result:

- V20 branch: `consequence-symmetry-genesis-v20`
- V20 run: `34753020515`
- V20 head: `db65569ce47b73d67ee96e69765c157a0977f244`
- V20 verdict:
  `VERIFIED_CONSEQUENCE_SYMMETRY_ORBIT_QUOTIENT_AND_SYMMETRY_BREAKING_GENESIS`

V20 still supplied the transformation carrier class:
independent bijections of X and C.

V21 asks whether a certified residual can force the transformation language itself to enlarge.

## Question

Suppose the current transformation language is exhausted and still distinguishes two presentations that verified consequence cannot distinguish.

Can the system synthesize a new transformation primitive directly from that residual, verify it, integrate it compositionally, and contract the representation further?

The target is:

    current language exhausted
        -> certified residual
        -> minimally synthesized transformation primitive
        -> verified language enlargement
        -> new symmetry orbit
        -> tighter consequence quotient.

No geometric or named transformation class is supplied.

## Initial transformation language L0

A finite consequence world is:

    V : X x C -> K.

The initial transformation language is exactly the V20 factorized language:

    T(x,c) = (sigma_X(x), sigma_C(c))

where sigma_X and sigma_C are generated from anonymous label transpositions.

This class is searched exhaustively.

Let G0 be the complete consequence-preserving subgroup representable in L0.

Its induced cell-orbit quotient is Q0.

## Certified language residual

Define complete consequence equivalence on presentation cells:

    (x,c) ~V (x',c')
    iff
    V(x,c) = V(x',c').

If two cells are equivalent under ~V but lie in different G0-orbits, then the current transformation language is certified too weak to realize the maximum consequence quotient.

A residual witness is therefore:

    rho = (a,b)

such that:

    V(a) = V(b)
    but
    orbit_G0(a) != orbit_G0(b).

This is not search failure.
L0 has already been exhausted.

## Generic repair constructor

V21 does not preload a list of higher transformation types.

Given a certified residual witness rho=(a,b), the developmental constitution may synthesize exactly one new primitive:

    JOINT_SWAP(a,b)

which transposes those two atomic presentations in the reified carrier:

    P = X x C

and fixes every other presentation.

The primitive is admitted only if independent replay verifies:

    V(a) = V(b).

Thus the new transform is generated from the obstruction itself.

No JOINT_SWAP instance exists before a residual earns it.

## Why this is genuinely outside L0

For |X|>1 and |C|>1, a nontrivial transposition of exactly two cells of X x C while fixing every other cell is not representable in general as:

    sigma_X x sigma_C.

V21 must independently verify that every admitted generated repair primitive is absent from the exhausted L0 transformation set.

Therefore the developmental transition is a type-level enlargement:

    Perm(X) x Perm(C)
        ->
    < Perm(X) x Perm(C), residual-generated swaps on X x C >.

## Composition without enumerating the full enlarged group

The enlarged permutation group on X x C may be enormous.

For quotient purposes, only its action orbits are required.

Given:
- the complete G0 cell orbits; and
- admitted JOINT_SWAP edges,

the cell orbits of the generated enlarged group are exactly the connected components obtained by joining G0-orbits with the generated swap edges.

Because every generator preserves consequence, every resulting component is consequence-homogeneous.

## Minimum language growth

Let the current G0 quotient induce components O1,...,Or.

For each consequence value k, consider the components whose cells all have value k.

To realize the full consequence quotient, those components must become connected.

A residual-generated swap can merge exactly two such components.

Therefore the exact minimum number of new primitives required is:

    sum_k (number_of_current_components_with_value_k - 1).

V21 must also enumerate every equal-cost minimum repair frontier at the declared finite bound.

No lexical or positional preference may erase non-canonicity.

## Developmental algorithm

The Minimal Developmental Algorithm remains:

    EXECUTE
    -> VERIFY
    -> DIAGNOSE
    -> CONSTRAIN
    -> RESTRUCTURE
    -> CHOOSE
    -> COMPILE
    -> UPDATE.

### EXECUTE
Use L0 and its verified orbit quotient.

### VERIFY
Exhaust L0 and independently verify every admitted transformation.

### DIAGNOSE
Compare L0 orbits with complete consequence equivalence.

If they coincide, growth is not authorized.

If they do not, emit an explicit same-consequence / different-orbit witness.

### CONSTRAIN
Generate only JOINT_SWAP instances whose endpoints lie:
- in different current orbits; and
- in the same consequence-equivalence class.

### RESTRUCTURE
Search exact minimum sets of generated swaps whose induced connectivity realizes the complete consequence quotient.

### CHOOSE
Preserve every equal-cost minimum repair set.

### COMPILE
Compile:
- the residual-to-swap repair rule;
- the selected active generated swaps;
- exact provenance;
- the pre-growth and post-growth orbit signatures.

### UPDATE
The new transformation language becomes current.

Replay remains mandatory.

## Required post-freeze gates

### L1 — initial language is exhausted before growth

The main challenge must exhaust every L0 factorized bijection.

A residual may authorize growth only after exact L0 completeness is established.

### L2 — current language is provably too weak

At least one pair of presentation cells must:
- have exactly equal verified consequence; but
- lie in different L0 orbits.

### L3 — repair primitive is synthesized from residual

No post-L0 primitive may be admitted unless its endpoints occur in a certified same-consequence/different-orbit residual.

### L4 — generated primitive is genuinely new

Every admitted nontrivial JOINT_SWAP must be independently shown not to equal any transformation representable in L0.

### L5 — minimum language enlargement

The number of generated primitives must equal the exact graph-theoretic lower bound:

    sum_k (components_k - 1).

If multiple minimum repair sets exist, preserve them.

### L6 — final quotient reaches complete consequence equivalence

After language growth, cell orbits must equal the consequence-value classes exactly.

No same-consequence pair may remain separated.

No different-consequence pair may be merged.

### L7 — exact consequence reconstruction

One representative value per final orbit must reconstruct the full consequence table exactly.

### L8 — representation contracts while language grows

The number of quotient cells must strictly decrease after transformation-language growth.

This demonstrates that mechanism growth can support representational contraction.

### L9 — relabelling transfer

An independently relabelled copy must require the same:
- initial L0 structural signature;
- minimum number of generated repair primitives;
- final orbit-size/value multiset.

The literal residual witnesses may differ by relabelling.

### L10 — no-growth control

A world whose L0 symmetry orbits already equal complete consequence equivalence must not generate any JOINT_SWAP.

### L11 — growth-rule ablation

If residual-generated primitive synthesis is disabled, the main challenge must remain at the certified L0 residual rather than silently merging consequence-equivalent cells.

### L12 — wrong generated primitive is rejected

A cross-orbit swap whose endpoint consequences differ must fail independent replay and never enter the language.

### L13 — symmetry breaking revokes generated transformations

After a post-freeze consequence perturbation, at least one previously generated JOINT_SWAP must fail replay.

The system must revoke it and recompute a lawful quotient.

### L14 — heterogeneous transfer

The same frozen developmental kernel must generate the required transformation-language extension for a structurally different consequence world, or correctly retain L0 if no extension is earned.

### L15 — incomplete authority

Missing consequence cells must return UNKNOWN_AUTHORITY.

### L16 — consequence ablation

Without consequence comparison, no residual-generated transformation may be synthesized.

## Scientific interpretation

A pass establishes, in a bounded finite setting:

> when an exhausted transformation language leaves verified consequence-equivalent presentations artificially distinct, the residual itself can specify a minimal new transformation primitive; integrating those primitives enlarges the mechanism while contracting the representation to the maximum consequence quotient.

This is stronger than merely searching a predeclared richer transformation class.

The individual new transformations are constructed from the certified obstruction.

## Claim boundary

A pass does NOT establish:
- unrestricted transformation invention;
- continuous transformations;
- physical symmetry groups;
- autonomous invention of the generic JOINT_SWAP repair constructor;
- that consequence-value equivalence is sufficient in open-ended worlds;
- natural-world objecthood;
- quantum structure.

The next boundary after a pass is meta-transformation genesis:

    can the generic repair constructor itself
    be selected/generated from a lower edit substrate
    rather than supplied to the developmental constitution?
