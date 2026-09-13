# Hex Digraph Adapter Genesis V2 — Sealed Result

## Verdict

**VERIFIED_BOUNDED_ADAPTER_GENESIS**

Workflow run: 34727765985  
Workflow job: 103644868924  
Head: `8e897d6571bf53a35980d8ff635a68652bf81173`  
Evidence artifact: 10309130239  
Artifact ZIP SHA-256: `a384b953d8cf3236255cd104679a3079430ab8d8ce2bbd60a6e2fcc996f24891`

## What changed from V1

V1 manually supplied the successful three-role directed-to-undirected representation and then qualified it.

V2 did **not** supply that adapter. It supplied only an anonymous finite grammar:

- 1, 2, or 3 role copies per source vertex;
- any ordered pair of roles as the directed-arc channel;
- any subset of pairwise identity couplings between roles.

The role identifiers carried no OUT / IN / ANCHOR meaning.

## Exhaustive synthesis

The grammar contains exactly **81 candidates**.

Qualification again exhausted:

- all 64 loopless directed graphs on 3 vertices;
- all 4,096 ordered pairs;
- exact source isomorphism;
- exact colour-preserving target isomorphism.

Cost was frozen as:

1. role count;
2. identity-coupling count;
3. lexical tie-break only after structural cost.

No candidate below cost `(3 roles, 2 identity couplings)` qualified.

Cost-level residuals:

| Cost | Candidates | Qualified | Best disagreement count |
|---|---:|---:|---:|
| 1 role, 0 couplings | 1 | 0 | 1228 |
| 2 roles, 0 couplings | 4 | 0 | 36 |
| 2 roles, 1 coupling | 4 | 0 | 36 |
| 3 roles, 0 couplings | 9 | 0 | 36 |
| 3 roles, 1 coupling | 27 | 0 | 36 |
| **3 roles, 2 couplings** | **27** | **6** | **0** |
| 3 roles, 3 couplings | 9 | 6 | 0 |

The least successful structural cost is therefore **(3,2)**.

## Synthesized adapter

Canonical tie-break selected:

- roles: `3`;
- arc channel: `0 -> 1`;
- identity couplings: `0--2` and `1--2`.

That is exactly the V1 role-split/anchor structure, recovered from anonymous role IDs by semantic qualification rather than supplied role meanings:

- role 0 behaves as arc tail / OUT;
- role 1 behaves as arc head / IN;
- role 2 is the identity anchor tying both copies of the same source vertex together.

There were 12 zero-disagreement candidates in total, of which 6 occur at the least structural cost. These are symmetry-related role assignments / channel orientations; the frozen lexical rule selects one representative.

## Causal controls

Both single-coupling ablations of the selected adapter produced **36 semantic disagreements** on the exhaustive qualification world.

The one-role direction-erasing candidate produced **1,228 disagreements**.

Thus the two identity couplings are not decorative: deleting either destroys the exhaustive semantic match.

All eight V2 precommitted gates passed.

## Held-out compilation

Only after qualification and selection, `generate_lean.py` read the selected adapter and generated `Generated.lean` for unseen n=4 obligations.

Generated Lean SHA-256:

`f1bcdc90c1a2d6671bf39a201c433a00ccacf66a2dcebfa338601bc325140bea`

Hex kernel-check traces:

- positive encoded pair: `route=witness n=12 nodes=2`;
- negative encoded pair: `route=root n=12`;
- lossy direction-erasing control: `route=witness n=4 nodes=6`.

The generated held-out transfer passed.

## Sealed files

- `Generated.lean`: `f1bcdc90c1a2d6671bf39a201c433a00ccacf66a2dcebfa338601bc325140bea`
- `PROTOCOL.md`: `df8215458cbabac961b67bf419c11f16fcda35e2960933463a8d59514bae284e`
- `generate_lean.py`: `fda0fb64c08d3da1ee4a09cf9ddead182b61a497288d2397a69d3fdd14a45e8d`
- `lake-manifest.json`: `4f72d339241e48de027640a70e2cd30c6c5443d290919126af08955be4e8ca0e`
- `lakefile.toml`: `acced4478aedb701b965b691b60b76af7f8c191dbbf6da65734c6f1f596facd5`
- `lean-toolchain`: `8190e75a201741065fe508b28955dd64dd72d090babe5f70ce6848879d68ae88`
- `candidate_ledger.json`: `8dbdf194f0c40055597b77b112b4701a55ce5047efbd88c7754f464ea977ddb5`
- `selected_adapter.json`: `f3bf0adc72eb55f80c14b0f4de1473011b017c6b1e587cdd6901973df099f6f8`
- `run.py`: `278e42091737dc35cc450ee0efe4bb1be142b19071e11a041f8c688c930a3acb`

## Claim boundary

This establishes bounded exhaustive adapter synthesis and held-out verified exaptation **inside the supplied grammar**.

It does not establish autonomous invention of that grammar, an all-n theorem of faithfulness, open-ended representation invention, or unrestricted transfer.

The important new result is narrower and cleaner: once the lawful design space was supplied, semantic consequence recovered the successful representation rather than a human choosing it.
