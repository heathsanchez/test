# Generation 2 — frozen before implementation (2026-10-21)

Target: pinned go-ini/ini@e2db55b0e088fa4ee0c128aa4ade263cdc1d7f08; no replacement on failure.

New obligation (distinct from first roundtrip): serialize→load→serialize→load should preserve the named key's decoded string across a second generation, for the *same previously declared nine representable strings*; test output byte equality only as diagnostic, not a required property.

Candidate: retain Generation-1 fixture list and adapted native Go test machinery. Comparator: equally informed conventional Go test author given the identical fixture list, generator, API adapters and native tooling. Both are allowed to reuse the Generation-1 code. For matched executable tests, expected result is a **tie**; no fictitious discovery-time gain.

Negative: after producing first serialization, deliberately corrupt exactly the `Value` field before second decode. Independent assertion must reject its altered meaning. Fail closed on parser ambiguity.

Measurement: separately measure generation-2 targeted native compilation/execution in repeated alternating arms, including process costs. Retained-method acquisition costs from generation 1, human authorship, and API adaptation remain unmeasured and MUST NOT be represented as net lifetime savings.

Gate: native acceptance, negative rejection, exact SHA, all fixture outcomes, paired comparator. Qualify only bounded behavior, not cross-source capability compounding or commercial advantage.
