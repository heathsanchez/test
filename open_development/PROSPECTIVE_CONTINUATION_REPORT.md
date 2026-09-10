# Prospective Continuation Genesis V1 — Scientific Report

## Outcome

`UNKNOWN_PROSPECTIVE_CONTINUATION_COVERAGE`

The experiment did not earn `PROSPECTIVE_CONTINUATION_GENESIS_V1_PASS`.
Under the frozen finite substrate, none of the 400 route-neutrally administered
ARC evaluation tasks had a generated realization. No capability was admitted,
so no prospective multigeneration continuation could lawfully be tested or
claimed. This is a principled coverage result, not an implementation failure
and not a version-space ambiguity.

## Authority and chronology

| Item | Identity |
|---|---|
| Repository | `heathsanchez/test` |
| Immutable v4 release-authority parent | `01088c9e67b11cc29342b5150a28050bdef16b29` |
| Experimental branch | `prospective-continuation-genesis-v1` |
| Scientific freeze | `0899dd0dcf52bf17865f5b75f313a9aea9db0233` |
| Freeze nonce | `34462442628:1` |
| Freeze manifest digest | `b0e3a01225aba192afe5e66a28aa5b7bc1606376a2921c8b84cdff4222f0816d` |
| External repository | `fchollet/ARC-AGI` |
| External commit | `399030444e0ab0cc8b4e199870fb20b863846f34` |
| External path | `data/evaluation` |
| External corpus digest | `7da62e79515b43fb2525432bffa519adbb84673c9098bdf5982454f5ad911318` |
| Eligible files | 400 |
| Stream digest | `6022c3d6c18d429c7856ed2a9292045b216d05a8d9e6b25d1bb1ccbd85c41674` |
| Immutable decisions digest | `2531a60a0113fcfe8f5947f06112bdefb4ff6f84315f8b59c6c7a5c29b263f30` |
| Evaluation evidence digest | `c2c2f176d5d33bf5003a7492f332a1c2f8507dc1321e13a40a13e4b66fdb428c` |

The four-stage workflow ran in the required order: freeze, administrator,
developer, evaluator. The freeze manifest records that the external checkout
was absent. The administrator subsequently checked out the pinned corpus and
formed the complete eligible pool in nonce-hash order using only ARC JSON
schema, grid/color, provenance, and resource predicates. Route labels were not
present in the stream. The immutable developer record states
`labels_seen=false` and `hidden_outputs_seen=false`. Hidden outputs were first
used by the independent evaluator after all 400 decisions were committed.

## Frozen developmental language

The experiment retained the eight existing typed `Grid -> Grid` D4
capabilities. The complete old language for each task consisted of those eight
active behaviors and eight old crop-role behaviors: cardinality 16.

The lower substrate was frozen before external checkout:

- node types: input, call-retained, crop, horizontal composition, vertical
  composition, and overlay;
- maximum AST size 5 and maximum depth 3;
- enumeration by increasing size and then canonical JSON;
- normalized AST identity, including identity-call elimination, canonical
  overlay operand order, and duplicate removal;
- exact typed replay against visible training observations only.

The substrate identity was
`5ad5f1f3c5844ab032e63f5e7c94e937337836efa55429b08acd48066520c863`.
The concrete v4 list of 24 NEW formation rules was not supplied to the
developer. Candidate ASTs were generated from the frozen node grammar.

## Exact result

For every one of the 400 tasks:

- direct active-capability survivors: 0;
- old role-only survivors: 0;
- old-language coverage complete: true;
- old-language cardinality: 16;
- generated candidate count: 207, comprising 3 size-3, 40 size-4, and 164
  size-5 normalized ASTs;
- generated training survivors: 0;
- minimum adequate AST size: none;
- admitted capabilities: 0;
- predicted route: `UNKNOWN`;
- warm and restart verdict: unknown;
- residual class: `NO_GENERATED_REALIZATION`;
- residual evidence strength: `finite-exhaustive-inconclusive`.

Across the stream this was 82,800 exact candidate evaluations. It establishes
that the external stream had no qualifying realization inside this declared
finite lower substrate. It does not establish that ARC tasks are impossible,
that no richer generated language could solve them, or that a particular
language extension is necessary.

The initial and final developmental state identity were both
`3a018f07d1a8ed1c2d294e587b6f032e10af6f4b27da65d6dcc90bc2f750d0e6`.
No admission occurred and no hidden repair entered the ledger.

## Cost record

The recorded aggregate vector over 400 tasks was:

| Component | Total |
|---|---:|
| `C_construction` | 0 |
| `C_verification` | 400 |
| `C_activation` | 0 |
| `C_execution` | 10,904 |
| `C_memory` | 2,951,200 |
| `C_recovery` | 400 |
| `C_external_interaction` | 1,363 |
| Candidate evaluations | 82,800 |
| Verifier calls | 400 |
| CPU seconds | 575.160 |
| Wall seconds | 576.201 |
| Maximum recorded peak RSS | 68,244 KiB |

These are implementation-relative accounting values, not a universal economic
comparison.

## Tests and formal authority

The freeze job passed 62 Python tests, including the generated-constructor
fixture, dependent G1 -> G2 acquisition, qC zero-acquisition execution through
the learned ancestry, restart, exact revocation/restoration, cold, sham,
wrong-operation, fixed-policy, raw-history, ambiguity, chronology, and tamper
controls. Those fixtures validate the mechanism but are not external scientific
scoring tasks.

The job also passed the existing pinned Lean core gate. No new Lean theorem was
added. Lean supports the pre-existing generic semantics only; ARC parsing,
candidate enumeration, Python execution, independence checks, and this UNKNOWN
result remain Python-qualified. No claim of end-to-end Lean verification is
made.

## Workflow evidence

Scientific run:
https://github.com/heathsanchez/test/actions/runs/34462442628

| Stage | Job | Artifact | Artifact SHA256 |
|---|---|---|---|
| Freeze | https://github.com/heathsanchez/test/actions/runs/34462442628/job/102823157078 | https://github.com/heathsanchez/test/actions/runs/34462442628/artifacts/10146106813 | `1e958a5ba4c3ed259ed54924663244cd3734f24cc48e59d787ef75db1de5cd7d` |
| Administrator | https://github.com/heathsanchez/test/actions/runs/34462442628/job/102823335405 | https://github.com/heathsanchez/test/actions/runs/34462442628/artifacts/10146113860 | `dca51d0dd3f1c7d636a1629bc8f7793a9750bed8440fd332a5ff098f63471399` |
| Developer | https://github.com/heathsanchez/test/actions/runs/34462442628/job/102823401949 | https://github.com/heathsanchez/test/actions/runs/34462442628/artifacts/10146565086 | `b93e5f4ff39ac780d6827c6826e8953dbb7d5c42f678ffdc65c8f5b2554b0bfb` |
| Evaluator | https://github.com/heathsanchez/test/actions/runs/34462442628/job/102826991830 | https://github.com/heathsanchez/test/actions/runs/34462442628/artifacts/10146571815 | `10edc9918acf47075aa624c6dac6e459e6e1fb322741e72dc23d4237e8943102` |

All four outer jobs completed successfully. More importantly, their internal
markers bind the freeze, 400-task stream, 400 immutable decisions, and final
`UNKNOWN_PROSPECTIVE_CONTINUATION_COVERAGE` result. The final artifact was
downloaded independently and its ZIP SHA256 matched the GitHub artifact
metadata.

## Causal controls

The scientific stream generated no G1. Consequently there was no claimed G1 ->
G2 -> qC chain on which post-disclosure ancestor-removal controls could be
meaningfully run. Reporting those fixture controls as if they were external
causal evidence would be a false positive. The correct causal statement is the
negative one: because nothing was admitted, the state did not change and no
future continuation was attributed to learning.

## Strongest supported claim

Under a frozen, route-neutral administration of all 400 pinned ARC evaluation
tasks, the existing developer completely tested a declared 16-behavior old
language and a frozen 207-program bounded generated language per task. Neither
contained a training-consistent realization for any task. The protocol
therefore abstained on every task, admitted nothing, preserved the initial
state exactly, and correctly withheld the prospective-continuation claim.

This does not establish prospective continuation genesis. It establishes a
clean substrate/corpus coverage mismatch and demonstrates that the gate fails
closed when the supplied generative basis is too weak.

## Next smallest separator

The developmental kernel should remain unchanged. A successor must create a
new scientific freeze with a more expressive but still finite and auditable
lower substrate whose primitives can describe object selection, color/value
transformation, spatial mapping, and controlled iteration. Its external stream
must again be fixed route-neutrally before development, and its complete
bounded enumeration/minimality policy must be frozen before external checkout.
The present post-observation run must not be patched or retrospectively
broadened.

