# C157: 407 costly BVar2 calls have distinct binding nodes; 406 bind another BVar2 closure

**WARRANTED_BOUNDED source-qualified diagnostic; candidate forwarding-chain optimization, NOT a graph proof or ACCEPT.** Read-only C157 examined the actual immutable `EnvFrame` binding node at lexical index `2` of all 407 C155 expensive complete N7 source calls, each `ExprId 11 = BVar(2)` by the C156 native source-shape audit. It compared node identities and strict Values without quotienting environments or reusing any result.

Source [commit `3e8eacf`](https://github.com/heathsanchez/test/commit/3e8eacf7e2864e703c342962512b28f64b260352) on `research/nucleus-c157-binding-origin-20261114`; [native Action #43521225157](https://github.com/heathsanchez/test/actions/runs/43521225157) **SUCCESS**; artifact `14083017962` SHA256 `5eafc1ce0a9dc9f2fd51ba000120ecbe01f8bdcd6bdd1e6b2584c0cf527d71bc`. Same recovered exact C125b `d8be1443f2f1352634aaf333a282f32e7ec8a719`, immutable Arena N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Native low 65,536 original UNKNOWN/exit2, high 14,155,776 diagnostic ACCEPT/exit0; observer ON/OFF verdict/stdout and non-observer stderr byte-identical; frozen forgeries non-ACCEPT exits 1/2/1; 341 Rust passed, 0 failed, 17 ignored (39 suites). No semantics changed, full 196/403 not rerun.

## Original high producer, exact immutable binding provenance

| Property | Observed |
| --- | ---: |
| Costly completed `BVar(2)` exposure calls | **407** |
| Distinct immutable binding nodes reached by de Bruijn index 2 | **407** |
| Repeated binding-node IDs among these | **0** |
| Missing, Free, Neutral, or Nat binding | **0** |
| `EnvBinding::Closure` instances | **407** |
| Captured closure source expression `ExprId 11 = BVar(2)` | **406** |
| Captured closure source expression `ExprId 1` | **1** |

This is not 406 repetitions of an identical completed calculation or proof that the 407 nodes lie on one linear path. It shows the **same source-level BVar2-to-BVar2 forwarding pattern with distinct captured origins**; different closure environments and strict results are already known (C155–C156). Grouping by source expression alone is unsafe; grouping by the first binding-node ID also yields **zero** repeated opportunities among the expensive calls.

**Decision:** REJECT a shortcut keyed only by the source expression or by the first immutable binding node as an existing-repeat optimization for this group. **C158 cheapest decisive test:** independently walk the *actual immutable BVar-to-closure edge graph* from each of these 407 original keys, keeping `(source ExprId, environment node id, levels)` identity; measure terminal expressions, chain lengths, shared suffixes, cycle/escape cases and direct binding-node links. Do not change evaluator or fuel. Only if there are lengthy acyclic shared suffixes should we attempt path compression with an explicit source-owned terminal-and-traversal certificate, preserving visited-cycle behavior, pending spine, levels, and forged-proof regressions. This is a candidate route; source chain structure and any budget saving remain UNKNOWN.
