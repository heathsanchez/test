# G3 source-blind operation invention — preregistration, 2026-10-30

Status: DESIGN / NOT A RESULT. No G3 promotion is implied.

## Deterministic target and censorship
- Before reading any target source, search GitHub repository metadata with exact query `topic:cache language:Go stars:>1000 archived:false sort:stars-desc`, first page 10.
- Select result rank 1: `patrickmn/go-cache`, default branch `master`. Current source SHA from commit metadata: `46f407853014144407b6c2ec7ccc76bf67958d93`.
- No target README, issue list, PR, release notes, changelog, test files, or historical diffs may be used to propose operations. Limit design input to Go source AST plus build metadata. The SHA lookup inadvertently exposed the HEAD commit *message* about a test benchmark. This contaminates absolute history blindness. Report it; do not conceal or re-select the target.
- All source/native assertions must execute against exactly that SHA.

## Question
Can a repo-generic proposer produce a useful, *non-exported* environment operation by noticing a dependency in source, and can that operation reveal state distinctions hidden from an API-only trace observer, with an independent native check?

## Frozen source-adaptive proposer
- Use Go AST only to scan *non-test* sources for clock reads (`time.Now`, `time.Since`, `time.Until`) and exported public methods + signatures.
- If and only if a clock dependence is present, emit candidate primitive `ELAPSE` (wall-clock delay) as an environmental action, not an API method. Do not manually choose target-specific methods after seeing code.
- Construct bounded candidate grammar by matching string-key / generic-value write methods to string-key read methods by Go signature; emit `WRITE(key,value,expiry)`, `READ(key)`, optional `DELETE(key)`, and `ELAPSE`.
- Fixed input family: keys `k` and `j`, values `v` and `w`, short expiry 80ms, elapsed delay >=250ms, no expiry where available. Bound trace length <=4 and generated source-native probes <=96.
- If method matching/instantiation cannot be performed without a target-specific adapter or special constructor, report UNKNOWN_ADAPTER instead of claiming autonomous success.

## Comparisons, controls, and boundaries
- B0: exported API operations only, same key/value budget and trace horizon; no invented external action.
- B1: fair time-aware direct metamorphic oracle (`WRITE; ELAPSE; READ`) with identical budget, even if manually given `ELAPSE`. If B1 obtains the same result, no superiority claim.
- Independent replay: re-execute emitted native trace on exactly the pinned commit and compare observed outputs; reject forged observation and wrong SHA.
- Negative controls: zero-time/no-expiry and deliberately broken elapsed-clock premise. No accidental natural-language repair claim.
- A result is *WARRANTED_BOUNDED* only if source extraction, native transfer, controls, exact pin and independent replay pass in CI. Even then strict G3 remains UNKNOWN unless a genuinely novel, non-templated action is created and a fair source-aware baseline cannot reach the same evidence.
- Failures, trivial baselines, test greens, or missing Go runtime become explicit UNKNOWN/REJECTED records.

## Why this falsifier matters
Prior go-chi witness grammar was human-declared, though its source-native quotient and 8 green upstream checks were real. Here we test whether environmental operations beyond an API call alphabet can be generated from actual source. The cheapest possible negative result is that source-derived `ELAPSE` is an obvious predefined template and fair B1 matches it: then it is reusable transfer, *not* autonomous invention.

Lineage: `research/g3-gochi-response-observer-falsifier-20261030` @ `9160767e27069cba8cb7d03dcc00d3eead468077`, CI `40979738227`.
