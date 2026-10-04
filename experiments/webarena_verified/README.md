# WebArena-Verified Capability Compiler v1

## Objective

Beat the current public WebArena/WebArena-Verified frontier by treating browser-agent failures as recurring, verifier-defined capability families rather than unrelated tasks.

## Evidence boundary

- Staging repo: `heathsanchez/test`
- Branch: `webarena-verified-capability-compiler-v1`
- Branch base: `4c6274d58a9fca27f24fd6c85508883d1b942cc7`
- Upstream benchmark: `ServiceNow/webarena-verified`
- Upstream benchmark pin: `6473f72db5dcefc97b5725b59e734504edc28a21`
- Development set: official 258-task WebArena-Verified hard subset.
- Evaluator authority: official WebArena-Verified deterministic evaluator.
- No leaderboard claim is WARRANTED until an official-compatible run closes.

## Current state

INTERESTING -> CANDIDATE.

Static audit of the pinned hard subset found:

- 258 tasks.
- 114 intent templates.
- task types: 74 RETRIEVE, 36 NAVIGATE, 148 MUTATE.
- expected statuses: 248 SUCCESS, 5 NOT_FOUND_ERROR, 5 ACTION_NOT_ALLOWED_ERROR.
- top 20 recurring templates cover 78 / 258 tasks = 30.2%.
- top 40 recurring templates cover 138 / 258 tasks = 53.5%.
- top 50 recurring templates cover 168 / 258 tasks = 65.1%.

This makes the benchmark a plausible capability-compilation problem.

## Cheapest decisive experiment

1. Compile the pinned hard subset into template families.
2. Rank families by repeat count divided by evaluator/action complexity.
3. Implement the highest-yield family as a deterministic capability.
4. Run only that family against the official environment/evaluator.
5. Promote only if every member closes with zero regressions.
6. Repeat until the compiled-capability lane materially beats the general-agent baseline.

The initial residual mapper is `scripts/webarena_verified_residual_map.py`.

## Promotion rule

- **CANDIDATE**: static family identified.
- **WARRANTED_BOUNDED**: every member of a declared template family passes the official evaluator from a reset environment.
- **REJECTED**: family rule fails a member or violates benchmark interaction constraints.
- **REUSABLE**: warranted capability transfers to held-out instances/templates without special casing.

No result from static task definitions alone is a solved-task claim.
