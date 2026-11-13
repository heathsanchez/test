# C146: bounded used-binding projection yields six extra sampled collisions

**Status: WARRANTED_BOUNDED measurement, not an admitted reuse rule.** Corrected exact source [commit `efeb59ea8de21778cc82f4d0ae8aa342a97c6f57`](https://github.com/heathsanchez/test/commit/efeb59ea8de21778cc82f4d0ae8aa342a97c6f57), native [run #43508292032](https://github.com/heathsanchez/test/actions/runs/43508292032) **SUCCESS**, including source parser and whole release Rust regression. Artifact `14076663398` ZIP SHA256 `5ea1ee23a2b343b6301d94fba1227229683a17050137cb08b9d15bd2308786c1`. Original unchanged Arena N7 NDJSON SHA256 `abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`; still **C105-descendant surrogate**, not recovered production C124/C125b.

The first C146 [trial `cafe71174b43489403d809c640a7b77467971693`](https://github.com/heathsanchez/test/actions/runs/43507993285) was natively green but **SUPERSEDED** before promotion: it omitted `Closure.levels` from both sampled-key types. A source audit identified `Closure { expr, env, levels }` in `metatron-kernel/src/value.rs`, and the corrected version retains the structurally compared `LevelSubstitution` in both keys. The measured counts happened to remain equal between trials; that agreement does not remove the requirement to preserve this distinction. Prior C125 native three-forgery controls [#43507993411](https://github.com/heathsanchez/test/actions/runs/43507993411) passed on the first trial source; they were **not rerun as a distinct same-commit gate** after the correction.

## Exact compared keys

- **Full:** `(Closure { ExprId, EnvFrame, LevelSubstitution }, complete pending Vec<Closure>)`.
- **Projected:** `(ExprId, LevelSubstitution, actual immutable EnvBinding node ID at BVar's de Bruijn index, complete pending Vec<Closure>)`.
- Only source BVar expression IDs `1`, `6`, `11`, already decoded against the exact original export in C144. Source identity, transparency, proof authority and projection policy are fixed by the C142/C143 scoped evaluator. This is a bounded observation under diagnostic feature and opt-in flag, never a cache key accepted for proof.
- Deterministic 1/256 selection **depends on the full closure**, not the projected key. Consequently a small measured cross-frame collapse is **not a global upper bound**, and cannot by itself reject a support quotient.

| Exact captured exposure | Low first | Low second | High completed |
| --- | ---: | ---: | ---: |
| Total evaluator head visits | 63,908 | 60,444 | 12,761,384 |
| All BVar visits | 13,772 | 12,955 | 2,694,572 |
| Visits to BVar source IDs 1/6/11 | 12,790 | 12,018 | 2,495,694 |
| Selected sample visits | 45 | 28 | **9,262** |
| Nonempty pending spine in selected sample | 13 | 7 | 2,727 |
| Full unique keys | 45 | 28 | **7,987** |
| Projected unique keys | 45 | 28 | **7,981** |
| Full repeats | 0 | 0 | **1,275** |
| Projected repeats | 0 | 0 | **1,281** |
| **Additional sample collisions after projection** | **0** | **0** | **6** |
| Missing node / key overflow | 0 | 0 | 0 |

The high BVar target total is independently conserved against C143's source-ID counts: `1,095,156 + 896,349 + 504,189 = 2,495,694`. The first source-qualified measurement, silent verdict parity, C145 head census conservation and full Rust release test gate pass. No standard-budget UNKNOWN was closed.

## Decisive residual: C147 full-population optimistic key census

The 6/9,262 additional matches are a weak lead, but selection by full closure can **miss groups** where only one alias is sampled. C147 should count **all** BVar1/2 visits (`Expr6` and `Expr11`) with two deliberately weak keys: `(ExprId, full EnvFrame ID)` and `(ExprId, actual bound-node ID)`, expressly **ignoring universe levels and pending** only to find an optimistic **upper bound on how many BVar visit events could revisit the same projected node**. This is **not** a bound on fuel, CPU savings, or the incremental benefit of an exact context-aware cache, because the deleted pending contexts can multiply the number of distinct safe keys. Count both unique keys and repeat events over the complete producer; cap memory with explicit UNKNOWN on overflow. If even this optimistic quotient has few repeated visits, reject the *simple binding-node quotient as the route to 195× compression* and shift to application/beta graph sharing. If substantial, C148 must restore levels, pending, authority, transparency and proof obligations before any reuse. Never promote the optimistic key as semantically sufficient.

Lineage C143 source closure sample → C144 AST IDs → C145 action/BVar census → C146 complete-level binding sample → C147 proposed full-population upper bound. Historical six original valid standard-budget UNKNOWNs, source-qualified full Mathlib and production selection remain OPEN.
