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

## Governing law

The active representation should preserve exactly the distinctions that can change a warranted future:

```
x ~_F y  iff  no protected lawful continuation lets the official evaluator distinguish x and y.
```

For WebArena this means `intent_template_id` is only a syntactic proxy. The stronger unit of reuse is a verifier-relevant obligation/capability family. Static evaluator signatures may nominate such families, but they do not prove behavioral equivalence; only live official-evaluator separators can warrant the merge.

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

A first evaluator-obligation-shape quotient produced 136 CANDIDATE consequence signatures. It is deliberately coarser than concrete expected values and therefore is not a proof of equivalence. It does reveal cross-template reuse opportunities:

- largest candidate family: 11 Reddit mutation tasks spanning 7 intent templates;
- next: 9 Shopping Admin retrieval tasks spanning 6 templates;
- another: 9 Shopping Admin mutation tasks spanning 4 templates;
- another: 8 Shopping retrieval tasks spanning 4 templates;
- another: 8 GitLab/Reddit mutation tasks spanning 2 templates.
- top 5 candidate consequence families cover 45 / 258 = 17.4%.
- top 20 cover 102 / 258 = 39.5%.
- top 40 cover 155 / 258 = 60.1%.

These are candidates for shared capabilities, not warranted equivalence classes.

## Development rule

Encounter -> Verify -> certified residual -> necessary constraint -> least lawful capability change -> Verify -> Compile -> Reclose.

Concretely:

1. Use the official evaluator to define the protected consequence.
2. Cluster tasks only as a CANDIDATE when their evaluator obligations and site/action structure suggest a common capability.
3. Choose the cheapest separator inside that candidate family.
4. Implement the smallest capability that removes the residual.
5. Replay every already-warranted member.
6. Promote a family merge only when all protected continuations tested by the declared boundary remain indistinguishable.
7. Split immediately when a separator exposes a consequential distinction.
8. Compile the passing capability and reclose every other candidate family that can reuse it.

## Cheapest decisive experiment

The first live target remains Shopping Admin template 270 (tasks 108, 110, 111): a three-member RETRIEVE family with no NetworkEventEvaluator requirement and a shared structured month/count response schema.

The experiment is not "hard-code three answers." It is:

- learn one deterministic capability for the underlying order-history aggregation;
- run it from reset state on all three tasks;
- score with the official evaluator;
- require 3/3;
- then test whether that capability requalifies adjacent Shopping Admin retrieval candidate families.

## Promotion rule

- **CANDIDATE**: static family identified.
- **WARRANTED_BOUNDED**: every declared member passes the official evaluator from a reset environment under the stated boundary.
- **REJECTED**: a separator shows the family merge is too coarse or the capability violates benchmark interaction constraints.
- **REUSABLE**: a warranted capability transfers to held-out tasks/templates without special casing.
- **SUPERSEDED**: a later, smaller capability preserves the same protected future at lower prospective cost.

No result from static task definitions alone is a solved-task claim.

The residual mapper is `scripts/webarena_verified_residual_map.py`.
