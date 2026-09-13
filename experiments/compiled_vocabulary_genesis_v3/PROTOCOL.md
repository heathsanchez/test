# Compiled Vocabulary Genesis V3 — Frozen Protocol

## Question

Can one frozen typed generative basis **create a new reusable language atom from a verified composite**, then use that atom causally inside a different later program?

V2 showed that one frozen basis can construct several task languages by selecting and combining supplied primitive semantics. V3 removes a useful semantic atom from the primitive basis and asks whether repeated verified construction can compile it into the vocabulary.

## Frozen primitive basis

The V3 primitive semantics are intentionally small:

- Bool
- finite product types
- constants
- variable
- pair / fst / snd
- NOT
- AND
- OR
- IF

**XOR is not a primitive and no challenge may introduce an XOR host-language repair or named XOR operator.**

The frozen basis additionally contains one generic mechanism:

> any repeatedly verified finite program of sufficient construction cost may be promoted to a content-addressed macro atom carrying its complete finite extensional table, signature, provenance, and warrant.

The promotion mechanism is generic. It does not know the semantic name or intended use of a promoted behavior.

## Promotion rule

For a verified program p : A -> B:

1. compute its complete finite behavior table over A;
2. independently replay p on every input in A;
3. key recurrence by (A, B, extensional behavior), not syntax;
4. after the frozen recurrence threshold is met, and the program exceeds the frozen minimum promotion cost, construct a macro atom

       m_h : A -> B

   where h is a content digest of the signature and full behavior table;
5. the macro evaluator is only the frozen finite-table interpreter;
6. record provenance, origins, source program digests, full table, and replay certificate.

No semantic name such as XOR may be assigned by the developmental kernel.

## Causal transfer requirement

A pass requires more than reproducing the same task faster.

After promotion, a **different post-promotion task** must require the learned behavior as a proper sub-computation.

The warm kernel must solve that task under a program-cost bound that a cold kernel with the same frozen primitive basis cannot satisfy.

Then ablation of the promoted atom must restore failure under the same bound.

This establishes bounded causal vocabulary acquisition:

    repeated verified composite
        -> promoted anonymous atom
        -> new reachable program under fixed bound
        -> ablation restores obstruction.

## Search law

Programs are enumerated by nondecreasing AST cost and quotient-collapsed by exact finite behavior at every type/cost layer.

Search completeness claims are only relative to the frozen type grammar, primitive semantics, current promoted vocabulary, and declared cost bound.

## Temporal protocol

1. Commit this protocol.
2. Commit basis.py and kernel.py.
3. Freeze exact commits/hashes.
4. Only after freeze add the challenge pack and CI.
5. CI proves the core files are unchanged from the freeze commit.

## Required post-freeze gates

- primitive XOR absent;
- first XOR-like obligation resolved only by primitive composition;
- second recurrence resolved and triggers exactly one anonymous promoted atom for that behavior;
- promoted atom has complete finite replay certificate and provenance;
- later structurally different transfer task succeeds warm under a strict bound;
- cold kernel fails the same transfer task under the same bound;
- explicit macro ablation restores the cold failure;
- warm solution actually contains the promoted macro as a proper subexpression;
- warm search requires lower minimum program cost than cold search;
- UNKNOWN remains conservative when a bound is declared incomplete;
- no challenge-specific semantic operator is added post-freeze.

## Claim boundary

A pass establishes bounded **vocabulary genesis by verified compilation** over a supplied finite basis.

It does not establish invention of new primitive operational semantics outside the basis, unrestricted abstraction discovery, universal macros, unbounded self-extension, or autonomous revision of the promotion law itself.

The next boundary after a pass is whether a promoted composite can become not merely a callable macro, but a new **formation/type constructor** that changes what languages can be generated.
