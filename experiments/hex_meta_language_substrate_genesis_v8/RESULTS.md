# Hex Meta-Language Substrate Genesis V8 — Sealed Result

## Verdict

**VERIFIED_META_LANGUAGE_PRIMITIVE_GENESIS_AND_TRANSFER**

Workflow run: 34732985810  
Workflow job: 103659136380  
Head: `7722d1c3acd9ac26e496c2009bbb9f8467d9701e`  
Evidence artifact: 10310446449  
Artifact ZIP SHA-256: `a5283126481de32e6ac57dcea5a4ed6e5ffcf071efe7698a73acd25b6089954e`

V8 removed the `TRUE` selector atom supplied in V7.

The initial selector language contained only FIRST, LAST, and OR. Its complete nonempty semantic closure had three denotations: FIRST, LAST, and FIRST OR LAST. All three were inadequate on the protected one-, two-, and three-relation semantic worlds.

Only after that inadequacy certificate, V8 exposed a generic binary Boolean-function substrate: all 16 anonymous truth tables over the existing FIRST/LAST observations.

Exactly one of the 16 truth tables qualified over every protected world:

`1111` in input order `00, 01, 10, 11`.

Thus the previously supplied all-selection behavior was reconstructed from generic finite function space rather than provided as a named primitive.

The synthesized table was retained and transferred to a new four-relation world. Cold rediscovery first succeeded on candidate 16; warm reuse required one retained candidate. Under identical replay obligations this was a 16x reduction in candidate evaluations and semantic pair comparisons.

A held-out four-relation, carrier-size-3 problem was then generated and kernel-checked through pinned HexGraphIso:

- positive: `route=witness n=27 nodes=2`
- negative: `route=root n=27`

Claim boundary: the generic binary truth-table substrate itself remains supplied.
