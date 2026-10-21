# V10 post-exposure causality and withdrawal audit (separate from prospective result)

The frozen first native run #39567659722 produced source-backed one-hop cache -> lru_cache(maxsize=None) and bounded no-eviction observations for 33 keys. This protocol is written AFTER the source was seen. It does not upgrade original prospective novelty.

Controls:
1. Build a tiny source-warrant DAG from original verified source identities, with independent source-owner authorization for cache and lru_cache, documented equivalence edge, source-supported no-eviction, and separately retained native observation.
2. Withdraw cache owner: equivalence and derived property lose source warrant. Native observation remains as observation only.
3. Withdraw referenced lru_cache owner: equivalence loses warrant, cache-owned direct no-eviction statement remains warranted ONLY as a direct cache claim, native observation unchanged. Do not erase direct claims merely because equivalence went away.
4. Withdraw equivalence edge: only equivalence and derived-through-equivalence propositions lose authority; direct cache-source no-eviction and native observation remain.
5. Withdraw cache no-eviction source statement: direct source no-eviction loses warrant; independently verified behavior on 33 values is still a native sample, not a universal policy.
6. Independently execute nonconforming native comparator lru_cache(maxsize=8) with 33 distinct keys then reaccess first. It must produce 34 evaluations instead of 33 and be REJECTED for the protected 33-key property. Restored unbounded cache must PASS.

No source text is edited, no statements are added to original prospective source, and this DAG is a deliberately small operational model, not execution of actual MathGraph tracking or R7.2/CLC Lean checker. No general semantic-source confidence promotion.
