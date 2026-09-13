# Typed Generative Basis V2 — Frozen Protocol

## Question

Can one frozen **generative basis** construct different finite typed languages after the challenge pack is hidden, instead of merely synthesizing programs inside one fixed language?

The key V1 residual was that the frozen program language could build programs and some Code→Code edits, but its type/signature boundary was fixed. V2 moves the freeze downward.

## Frozen object

The scientific object is not a task language. It is a small basis B of:

- finite type constructors;
- grammar/operator atoms;
- generic rules for forming language specifications from those atoms;
- a typed program evaluator;
- exact bounded program enumeration;
- behavioral quotienting over complete finite domains;
- a generic developmental search over language specifications.

A task language is data:

    L = (input_type, output_type, admitted_operators, program_cost_bound)

and must be constructed from B.

No challenge may add a new type constructor, operator semantic, language-edit primitive, or special repair route after the freeze.

## V2 claim if successful

A pass establishes only:

> one frozen finite typed basis and one frozen generic developmental kernel constructed multiple different task languages after freeze because different externally verified obligations required different types, signatures, grammars, or contractions.

This is bounded language construction, not unrestricted language invention.

## Constitutional rules

1. Execute the current language/program first.
2. Verification authority is external to the basis.
3. Search failure is never expressive inadequacy unless the declared finite class was exhaustively searched.
4. A certified failure constrains continuation but does not pre-label the broken layer.
5. Candidate languages and programs are generated only from the frozen basis.
6. Programs are quotient-collapsed by complete finite extensional behavior within a signature.
7. If the current realization already works, contraction is still allowed when a strictly cheaper realization preserves all protected consequence.
8. If multiple behaviorally distinct cost-minimal candidates survive, preserve the lawful frontier; do not select by hash.
9. The basis may change input/output type, grammar/operator set, and program together.
10. Every admitted candidate must be independently replayed by the authority.

## Required post-freeze challenge families

At minimum:

- NO_CHANGE: current language already minimal and sufficient.
- GRAMMAR_GROWTH: same signature, current grammar cannot express the target within the declared complete bounded class; a new operator must be admitted.
- SIGNATURE_GROWTH: the current input type is inadequate; a product/signature must be constructed.
- STATEFUL_LANGUAGE: both interface and grammar must change to express a finite-state transition.
- CONTRACTION: a sufficient but over-rich language/program must shrink.
- BEHAVIORAL_QUOTIENT: syntactically distinct equivalent programs must collapse to one behavior class rather than create false non-canonicity.
- UNKNOWN_SEARCH: incomplete bounded search must stop conservatively.
- CERTIFIED_NO_LANGUAGE: the complete declared basis region contains no resolving language.
- AUTHORITY_CONFLICT: incoherent authority must stop before development.
- REUSE: a previously constructed language/program may be retained and reused if the same verified obligation recurs.

The kernel is not told which family it is facing.

## Temporal protocol

1. Commit this protocol.
2. Commit basis.py and kernel.py.
3. Freeze exact commits/hashes.
4. Only then add challenge_pack.py and CI.
5. CI must prove the frozen files are byte-identical to the freeze commit.

## Claim boundary

Even a pass leaves fixed and externally supplied:

- the primitive basis semantics;
- the verifier/authority;
- finite resource bounds;
- encounter selection;
- the developmental cost ordering.

The next boundary after a pass is whether the basis constructors themselves can be generated, replaced, or revised under the same verified developmental law.
