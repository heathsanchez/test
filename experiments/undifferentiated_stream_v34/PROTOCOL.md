# Undifferentiated Stream Residual-Machine Genesis V34 — Frozen Protocol

## Question

Can the separately addressable input atoms used in V33 be removed?

V34 gives the developmental kernel no banks, channels, coordinate names, history register, joint-system register, tuple constructor, Boolean operator, relation constructor, or random-access input primitive.

Each encounter is a single finite anonymous binary stream.

The synthesized executable object has only:

- OUT(label), the external consequence boundary;
- STEP(next_if_0, next_if_1), a generic transition that consumes the next anonymous symbol.

There is no instruction for "read position i". A machine can only begin at its current residual state and apply that state to the next symbol in sequence.

The hidden challenge pack is committed only after the scientific kernel is frozen.

## Developmental construction

For a complete finite encounter table, the verifier supplies authoritative consequences.

The kernel works backwards from those verified consequences.

At the end of a stream, equal consequences share the same OUT state.

For every earlier prefix, the residual state is determined solely by the pair of verified successor residuals reached after the next symbol is 0 or 1:

    residual(prefix) = STEP(
        residual(prefix + 0),
        residual(prefix + 1)
    )

Identical STEP pairs are hash-consed globally.

If both successors are already the same terminal consequence, the transition is unnecessary: that terminal absorbs the remaining stream.

Thus a reference to a later event is not supplied as a coordinate. It can only be realized as a chain of states that remains consequence-neutral until a later symbol becomes relevant.

Likewise, persistence is not supplied as memory storage. It can only appear when different prefixes must occupy different residual states because their future verified consequences differ.

## Exact authority and claim of minimality

The primary V34 worlds require the complete finite binary stream table of their declared stream length.

Incomplete tables remain UNKNOWN_AUTHORITY.

Within this declared model class — deterministic one-pass finite residual machines whose only executable transition consumes the next binary symbol, with consequence terminals permitted to absorb irrelevant suffixes — the canonical residual construction is exact.

Distinct residual states correspond to distinct future consequence functions. Such states cannot be merged without changing at least one verified future consequence. Repeated identical residuals are merged.

Therefore the generated machine is the quotient by verified future consequence within this bounded sequential substrate.

## Post-freeze tests

The challenge harness will use several independently permuted/relabelled flat streams. Semantic source variables are permuted to different stream positions after freeze; the kernel is never told that those variables exist.

The evaluation will test whether the same frozen mechanism exhibits structures later interpretable as:

- no required distinction;
- dependence on an early event;
- dependence on a delayed event, requiring neutral transition persistence before branching;
- dependence on two events, requiring distinct intermediate residual states;
- multi-class relational coding;
- dependence on three events;
- conditional/context-like and intervention-like branching;
- dependence on widely separated events;
- strong contraction relative to raw stream identity.

These names exist only in the post-freeze evaluation harness.

## Frozen gates

S1. Frozen scientific core is byte-identical after the challenge is committed.
S2. One frozen kernel exactly replays every post-freeze world under multiple independent stream permutations.
S3. A constant-consequence world contracts to a single OUT state.
S4. A one-event world needs exactly one branching transition plus two terminals when the relevant event is first.
S5. Moving that same semantic event later in the stream causes neutral transition states to appear before the decisive branch, without any coordinate-address instruction.
S6. A two-event Boolean relation requires distinct internal residual states and exact replay.
S7. A four-class two-event relation produces four consequence terminals and a nontrivial transition graph.
S8. An eight-class three-event relation produces eight consequence terminals and a larger exact residual graph.
S9. Conditional/context-like and intervention-like worlds require internal prefix distinctions whose structures change when the relevant source variables are permuted.
S10. A widely separated two-event world preserves both distinctions through intervening anonymous symbols.
S11. A contraction control maps 2^n raw streams to a much smaller consequence machine.
S12. Independent relabelling of consequence labels preserves structural signature.
S13. Incomplete encounter authority remains UNKNOWN_AUTHORITY.
S14. Verifier ablation authorizes no machine construction.
S15. No bank/channel/history/joint/ATOM/READ/indexed-input constructor occurs in the frozen executable machine language.
S16. Every executable nonterminal state has exactly the single generic STEP form.

## Claim boundary

A pass would not establish presuppositionless cognition or unrestricted ontology invention.

V34 still supplies:

- a binary symbol alphabet;
- sequential encounter order;
- a finite complete table in the primary tests;
- deterministic one-pass state transition semantics;
- an external consequence verifier.

Those are substantial priors.

What V34 can test is narrower and sharper:

> whether explicit input variables and separately addressable atoms can be removed, so that reference to an event, persistence of a distinction, and relational dependence arise only as verified residual transition structure over one undifferentiated stream.

The next irreducible question, if V34 passes, is whether even the supplied sequential symbolization can be weakened.
