# Consequence-Earned Tokenization V36 — Frozen Protocol

## Question

Can the supplied one-symbol-per-encounter boundary used in V35 be weakened so that a raw binary trace arrives with **no macro-event/token boundaries**, and consequence itself selects a reusable variable-length segmentation?

V36 is a bounded event-boundary experiment. It does not remove the binary sampling lattice itself. The raw input is still a finite bit string. What is removed is the assumption that each raw bit already is one semantic encounter.

## Frozen substrate

Each row contains only:

- one raw finite bit string;
- one externally verified consequence label.

There are no supplied:

- token/event boundaries;
- event identifiers;
- absolute position reads;
- fixed windows;
- named motifs;
- latent variables;
- pair/tuple constructors;
- history registers.

The frozen tokenizer hypothesis class is deliberately finite and declared in advance:

- anonymous prefix-free codebooks;
- 1 to 3 anonymous token types;
- each codeword has raw length 1 to 3;
- parsing must consume the entire raw string uniquely.

This is a substantial prior. A pass establishes boundary genesis **inside this declared code class**, not unrestricted segmentation from arbitrary continuous signals.

## Consequence criterion

For each candidate codebook D:

1. uniquely parse every raw training trace into an anonymous token sequence;
2. require the parsed encounter set to be complete over its induced token alphabet through the observed training token depth;
3. construct the minimum recurrent residual consequence machine over those token sequences;
4. verify exact replay of every authoritative consequence;
5. reject the tokenizer if recurrent transition closure cannot be established from the complete table.

Candidate selection is lexicographic:

1. minimum verified recurrent state count;
2. minimum total codeword length;
3. minimum maximum codeword length;
4. minimum token count;
5. canonical lexical tie-break only after the preceding consequence/complexity criteria tie.

Thus a boundary is not retained because it resembles a hand-written motif. It survives only if it yields a smaller verified recurrent consequence state machine within the frozen search class.

## Recurrent residual machine

For a token prefix p and all admitted token suffixes s up to distinguishing horizon h,

    R_h(p) = ( C(p ++ s) )_s.

Prefixes share a present state exactly when their complete admitted future-consequence signatures agree.

Transitions are admitted only when every representative of a residual class reaches one unique residual class under each anonymous token.

The learned machine is therefore a quotient by future consequence after a candidate raw-to-token segmentation.

## Post-freeze challenge family

After the scientific core is frozen, hidden worlds may use different anonymous variable-length prefix codes and different recurrent consequence functions.

The evaluator may test:

- variable-length two-token codebooks;
- raw-bit relabellings;
- event occurrences at different absolute raw offsets;
- longer unseen token sequences;
- recurrent persistence;
- multi-token relations/patterns;
- strong raw-string-to-state contraction;
- fixed-width tokenizer ablation.

The kernel is never told the hidden codebook.

## Frozen gates

T1. Frozen scientific core remains byte-identical after hidden worlds are committed.
T2. Every post-freeze training world is exactly replayed.
T3. Every learned tokenizer+machine transfers exactly to longer held-out latent sequences.
T4. The hidden variable-length codebook is recovered as the minimum verified tokenizer in every primary world.
T5. A constant consequence contracts to one recurrent state.
T6. A last-token consequence yields the expected two-state recurrent machine.
T7. Token parity yields a two-state persistent recurrent machine.
T8. A two-token consequential relation yields the expected three-state machine.
T9. A three-token relation yields the expected four-state machine.
T10. Mod-3 token persistence yields the expected three-state machine.
T11. The same hidden token semantics remains correct when raw codewords are bit-complemented.
T12. Canonical machine structure is invariant to raw bit relabelling.
T13. Variable-length codewords place semantic token boundaries at different absolute raw offsets.
T14. No verified fixed-width tokenizer in the frozen candidate class matches the primary variable-boundary worlds.
T15. Strong contraction occurs from the complete raw encounter table to a small tokenizer+machine.
T16. Incomplete authority remains UNKNOWN.
T17. Verifier ablation authorizes no tokenizer or machine.
T18. The frozen kernel contains no hidden challenge codeword, event name, motif name, or absolute-position read.
T19. Training through five latent tokens transfers exactly through eight.
T20. Independently expected minimum recurrent state counts are recovered.

## Claim boundary

A pass would establish only:

> within a finite binary raw sampling lattice and a frozen bounded prefix-code hypothesis class, future consequence can select variable-length reusable event/token boundaries and a recurrent residual machine without those boundaries being supplied in the encounter.

V36 still supplies:

- raw binary sample boundaries;
- raw temporal order and direction;
- a bounded prefix-code segmentation class;
- deterministic recurrent semantics;
- complete finite training authority;
- an external verifier.

The next step after a pass is therefore to weaken the raw sampling lattice or the prefix-code class itself rather than claiming unrestricted event genesis.
