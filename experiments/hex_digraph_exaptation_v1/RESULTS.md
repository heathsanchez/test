# Hex Digraph Exaptation V1 — Sealed Result

## Verdict

**PILOT_PASS**

Workflow run: 34727216924  
Head: `e1c58399c92355cd50e82b9e55075c7e0dfaa7a2`  
Evidence artifact: 10308475502  
Artifact ZIP SHA-256: `aaaca375e2d858e9d4a63b4f1f2c8e5320a1188320f129e382eb75b609c481e7`

## Finite semantic qualification

The declared qualification world was exhausted:

- 64 loopless directed graphs on 3 vertices;
- 4,096 ordered graph pairs;
- exact source directed-isomorphism oracle by exhaustive vertex permutation;
- exact target colour-preserving isomorphism for each declared adapter.

Results:

- `ROLE_SPLIT_ANCHOR`: **0 semantic disagreements / 4,096 pairs**.
- `SYMMETRIZE`: **1,228 semantic disagreements / 4,096 pairs**.

All eight precommitted finite gates passed.

## Held-out n=4 transfer through Hex

The selected role-preserving encoding was transported into pinned HexGraphIso and checked by the Lean kernel.

Hex traces:

- positive encoded pair: `route=witness n=12 nodes=2`;
- negative encoded pair: `route=root n=12`;
- lossy-control pair: `route=witness n=4 nodes=6`.

The positive directed-isomorphism obligation closed, the negative directed-isomorphism obligation was refuted after the role-preserving encoding, and the deliberately lossy direction-erasing encoding produced the expected false positive.

## External authority

- `leanprover/hex-graph-iso` tag `v0.6.0`
- commit `f247c0898414ca29c502691e3a8ad0b3ce0b4f6a`
- Lean `v4.34.0-rc2`

The CI built `HexGraphIso.Tactic` successfully before checking the held-out obligations.

## Sealed experiment hashes

- `Main.lean`: `020ef72bcebf1e48921ca9ee663b28068af5260ec1111ffbd188de549fbfcdb1`
- `PROTOCOL.md`: `656ae59904103d59d58ffe5ea07d40696923dd655a509d32364e44dd39b6c3e5`
- `lake-manifest.json`: `1359531684a28ab9f82bb460860767d81bb1a372f752197ddfc61dfbeeeea3e8`
- `lakefile.toml`: `666fd8da1e82c387676c6db2f9d038ed99fc50761ab6a80037e0151434764670`
- `lean-toolchain`: `8190e75a201741065fe508b28955dd64dd72d090babe5f70ce6848879d68ae88`
- `run.py`: `29f2197f59cfd1100ec436064f2620728e7f3836c231b682b354adf26381b727`

## Claim boundary

This result supports bounded finite semantic qualification plus held-out verified exaptation into an independently developed capability.

It does **not** establish:

- an all-size theorem for the adapter;
- autonomous invention of the adapter grammar;
- open-ended adapter discovery;
- broad natural-domain transfer;
- general developmental intelligence.

The next experiment therefore removes the manually selected adapter and asks whether a bounded adapter grammar can itself be searched, falsified, selected, compiled, and passed to Hex on held-out obligations.
