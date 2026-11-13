# C158: expensive N7 BVar forwarding paths are short and disjoint, not a shared chain

**WARRANTED_BOUNDED NEGATIVE:** C157's 406 BVar2-to-BVar2 first-step captured source shapes do **not** imply a long reusable binding path. C158 followed each of the 407 C155 expensive completed original source `BVar(2)` closure keys through actual immutable `EnvFrame` binding nodes, preserving the `(ExprId, env ID, levels)` visit distinction. It recorded individual path lengths, all traversed immutable nodes, strict terminal closure keys, non-BVar/other/unknown/cycle termination, and shared binding-node visits across paths. This was read-only and never used to decide ACCEPT.

Native [source commit `2d04886`](https://github.com/heathsanchez/test/commit/2d048869282ffba5cd2b9fbf84560ec76c53597b), [Action #43522026795](https://github.com/heathsanchez/test/actions/runs/43522026795) **SUCCESS**, artifact `14083346541` ZIP SHA256 `c35bf79859a5b61bf498c4b91bd24f2709c6fb18a033de0e54bfc351092be057`. Recovered exact C125b core `d8be1443f2f1352634aaf333a282f32e7ec8a719`; original frozen Arena N7 SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`. Standard 65,536 UNKNOWN exit2; 14,155,776 diagnostic ACCEPT exit0. C158 ON/OFF all other stderr, stdout and verdict identical. Frozen three forgeries exit1/2/1, none ACCEPT. 341 Rust pass/0 fail/17 ignored across 39 suites. No semantic change, no source-wide 196/403 or Mathlib rerun.

## Original source, same 407 expensive completed call keys

| Exact native traversal measure | Result |
| --- | ---: |
| Full starting closures | **407** |
| Sum of BVar-to-binding lookups across all 407 | **928** |
| Distinct immutable binding nodes traversed | **928** |
| Repeated node visits across *all* paths | **0** |
| Maximum path length | **4** |
| Distinct strict terminal closures | **407** |
| Distinct terminal source expression IDs | **4** |
| Largest single terminal source-ID class | **293** |
| Paths ever reaching source `ExprId 1` | **58** |
| Terminal non-BVar source expressions | **407** |
| Unbound/nonclosure exits, cycles, capped paths | **0** |

Every selected path terminates in a distinct full closure after at most four BVar binding lookups. C157's 406 shared *source expression IDs* were an identical **syntactic forwarding shape**, not overlapping **immutable binding paths**. The claimed structural equivalence was never strong enough for source value reuse. These 928 *additional diagnostic traversals* are **not** a census of all 2.69 million original BVar head visits from C152; the observation rejects the specific hypothesized **shared forwarding suffix** among the 407 expensive entry keys, not every possible binding-related optimization.

**Decision:** REJECT path compression of these expensive BVar forwarding paths as sufficient for N7, alongside C153's leaf-completion caching and C155's expensive full-exact-call caching. **This is not an impossibility theorem for a different evaluator.** The residual is App/Lam/BVar computation over *genuinely distinct captured contexts*, not hidden identity among the sampled large completed work units.

**Next consequential experiment (C159 CANDIDATE, algorithmic rather than another key):** On the immutable N7 source, isolate one sound, typed *relevance/recursor-major* simplification that turns a repeated semantic obligation into a smaller checked obligation. Specify the exact type-side precondition and operational rewrite, test it first on minimal native constructor/proof-erasure positives and adversarial negatives, then run original 65,536 N7 and three forged controls. If improved, rerun all six original good UNKNOWNs, the protected 403 and Mathlib; if no improvement or unsafe, withdraw it. Do not count mere repeated expressions, binding IDs, or weaker output classes as soundness certificates. The full Nucleus mission remains **OPEN**.
