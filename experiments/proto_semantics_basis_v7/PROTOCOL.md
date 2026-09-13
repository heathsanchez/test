# Proto-Semantics Basis V7 — Frozen Protocol

## Question

What is the smallest declared proto-semantic basis, within a finite candidate universe, that can reproduce the developmental ladder already seen from object-level reasoning through vocabulary, grammar/signature construction, semantic carrier growth, and meta-rule reuse?

The experiment does **not** assume that numbers, vectors, graphs, fields, or programs are primitive.

It tests whether the following lower-level objects are sufficient:

- a seed binary distinction;
- product of distinction spaces;
- quotient/identification of states;
- typed relations between finite spaces;
- composition of relations.

Verified compilation/reification and external authority remain part of the developmental constitution, not the proto-semantic basis under comparison.

## Candidate basis universe

The toggleable candidate primitives are:

1. PRODUCT
   - construct A × B from two finite carriers.

2. QUOTIENT
   - construct a canonical quotient A/~ with any declared finite partition that is independently checked by the authority.
   - in the bounded implementation this is represented by a canonical surjection onto k classes, 1 <= k <= |A|.

3. RELATION
   - construct a finite typed relation R subseteq A × B.
   - functional relations are executable computations.
   - Boolean-valued relations are predicates / proto-logical distinctions.

4. COMPOSE
   - compose typed relations R:A->B and S:B->C.

The fixed seed is BIT, a two-element distinction space.

The fixed developmental constitution supplies:

- independent verifier/authority;
- exact finite search bounds;
- behavior quotienting;
- verified compilation/reification of recurring accepted relations or carrier constructions;
- conservative UNKNOWN when completeness is absent.

Compilation is deliberately not counted as a proto-semantic primitive because it is the same developmental ratchet being tested across all levels.

## Why this candidate family

The hypothesis is:

    BIT + PRODUCT + QUOTIENT + RELATION + COMPOSE

may be enough for the finite regime because:

- arbitrary finite carriers can be represented as quotients of sufficiently large products of BIT;
- predicates are relations into BIT;
- deterministic computation is a functional relation;
- relational composition supplies modular executable composition;
- repeated verified relations or carrier constructions can be reified by the developmental compiler.

Numbers, graphs, type constructors, and meta-rules then become derived representational regimes rather than primitives.

## Required post-freeze challenge ladder

The challenge pack is added only after the basis/kernel freeze.

A full pass requires one generic kernel to support all of:

### L0 — distinction / proto-logic
Construct a nontrivial Boolean predicate over BIT × BIT and verify its full truth table.

### L1 — finite mathematical structure
Construct a three-element carrier from the binary seed using only PRODUCT and QUOTIENT. The authority checks the quotient map and exact carrier cardinality.

### L2 — computation
Construct a nontrivial functional relation between finite carriers and execute it on every input.

### L3 — modular computation
Given two previously verified/reified relations, solve a new transfer obligation under a tight construction budget by COMPOSE. Cold direct relation construction under the same budget must fail; a deeper cold search may recover it.

### L4 — vocabulary
A repeatedly verified relation must be reified as an anonymous relation atom and reused with zero relation-search acquisition.

### L5 — grammar / type formation
A recurring carrier-construction pattern must be reified as a carrier transformer and applied to an unseen base carrier under a tighter formation budget than primitive reconstruction.

### L6 — semantic basis growth
Construct a cardinality-3 carrier that cannot exist in the PRODUCT-only closure of BIT without QUOTIENT; use it with BIT to construct cardinality 6. Ablation of the quotient-derived carrier must restore impossibility.

### L7 — meta-rule
Encode a bounded developmental mapping as a functional relation over finite descriptor carriers. Preserve non-canonicity when partial observations underdetermine the relation; future verified consequence must select; then reify and reuse the selected relation with zero acquisition budget.

## Exhaustive primitive-subset test

After the full basis is tested, run every subset of:

    {PRODUCT, QUOTIENT, RELATION, COMPOSE}

against the same ladder.

Report:

- gates passed by each subset;
- inclusion-minimal subsets that pass all gates;
- for every primitive in each minimal full-pass subset, at least one gate restored to failure by its ablation.

If multiple incomparable minimal subsets pass, preserve all of them. Do not declare one canonical by syntax or arbitrary scalar preference.

## Cost discipline

Direct finite-relation synthesis is charged by extensional table construction cost.

Reified relation calls are cheap atoms.

COMPOSE has a fixed node cost.

This means COMPOSE is not claimed necessary for finite extensional expressivity: arbitrary finite relations can in principle be tabulated directly. Its necessity, if observed, is a claim about bounded modular synthesis / prospective construction economics.

Similarly, QUOTIENT is tested as a representation primitive that can generate non-power-of-two carriers from the binary seed.

## Temporal protocol

1. Commit this protocol.
2. Commit basis.py and kernel.py.
3. Freeze exact commits/hashes.
4. Only after freeze add challenge_pack.py, runner, and CI.
5. CI proves the frozen core is byte-identical to the freeze commit.

## Claim boundary

A pass establishes only:

> within the declared finite candidate universe and challenge ladder, one small distinction/relation calculus is sufficient, and exhaustive primitive ablation identifies the inclusion-minimal basis or bases.

It does **not** establish that this is the unique metaphysical foundation of logic, mathematics, computation, physics, or cognition.

It also does not establish continuous fields, natural-world grounding, infinite structures, unbounded recursion, or autonomous authority.

Those become later stress tests if the finite proto-semantic basis survives.
