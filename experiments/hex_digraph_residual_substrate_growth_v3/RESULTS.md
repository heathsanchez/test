# Hex Digraph Residual-Guided Substrate Growth V3 — Sealed Result

## Verdict

**VERIFIED_RESIDUAL_GUIDED_SUBSTRATE_GROWTH**

Workflow run: 34728103235  
Workflow job: 103645785353  
Head: `2c81ebc576c2ba938343546dc45ce9b1336c50a5`  
Evidence artifact: 10309060619  
Artifact ZIP SHA-256: `ca22003960053fe5a70f34c7fa5e4ba677fcaad95e77ebe73c78cb147871aa81`

## Developmental sequence

V3 did not begin with the successful three-role grammar.

It began with the complete substrate containing **only one- and two-role representations**.

That initial substrate contains 9 candidates in total and was exhausted over the same complete semantic world used in V1/V2:

- 64 loopless directed graphs on 3 vertices;
- 4,096 ordered graph pairs;
- exact source isomorphism;
- exact colour-preserving target isomorphism.

Result:

- initial qualified candidates: **0**;
- best initial disagreement count: **36**;
- best two-role disagreement count: **36**.

So the system had a finite certificate that its current representational substrate was inadequate before any growth was admitted.

## Residual

The diagnostic two-role candidate used:

- arc channel `0 -> 1`;
- identity coupling `0 -- 1`.

It still produced a false positive.

The target isomorphism witness used different permutations in the two roles. The residual was therefore classified as:

`ROLE_PERMUTATION_DESYNCHRONIZATION`

This is the important structural failure: the two target roles can be rearranged independently even though they are meant to denote two aspects of the same source vertex.

Adding a direct `0--1` identity edge does not solve the problem because that edge occupies the same ordered-colour pair as the encoded source relation itself. Identity evidence and relation evidence remain structurally confounded.

## Frozen one-step growth repairs

Only after the inadequacy gate, four predeclared substrate-growth constructors were evaluated:

| Repair | Qualification disagreements |
|---|---:|
| `ADD_INERT_ROLE` | 36 |
| `ADD_PARTIAL_IDENTITY_CHANNEL_0` | 36 |
| `ADD_PARTIAL_IDENTITY_CHANNEL_1` | 36 |
| **`ADD_FULL_IDENTITY_CHANNEL`** | **0** |

The successful repair adds a third role that does **not** carry source arcs. It serves only as a distinct identity channel:

- arc channel: `0 -> 1`;
- identity coupling: `0 -- 2`;
- identity coupling: `1 -- 2`.

Removing either coupling restores **36 disagreements**.

Thus the third role is not merely extra capacity. It separates identity constraints from the source relation channel and forces the otherwise independent role permutations to correspond to one source-vertex permutation.

## Independent convergence

The V3 repair is exactly:

`roles=3, arc=0->1, couplings={0--2,1--2}`

That is the same adapter independently selected in V2 and already kernel-checked through HexGraphIso on held-out n=4 obligations.

Frozen V2 authority:

- verdict: `VERIFIED_BOUNDED_ADAPTER_GENESIS`;
- run: `34727765985`;
- artifact: `10309130239`;
- Hex kernel check: PASS.

All nine V3 precommitted gates passed.

## Sealed files

- `PROTOCOL.md`: `42b6432d73606b55982d9cf406e02cb8f86caaa6b1282ba635c2695b5ae105e2`
- `initial_ledger.json`: `de2238442351fe378ba4e04cb0a237ff48dd870e778f05de99b0adbe7260e2ca`
- `run.py`: `72301afd1fb92d7b6307a80620e701af6829dbc5fb4e6bedc3ce24130eb3f323`

## Claim boundary

This establishes bounded residual-guided substrate growth under a supplied set of growth constructors.

It does not establish autonomous invention of those constructors or unrestricted grammar growth.

The new causal statement is:

> the old substrate was exhaustively insufficient; its concrete residual exposed desynchronized role identities; only the repair that created a separate identity channel removed that residual; deleting either half of that channel restored the failure.
