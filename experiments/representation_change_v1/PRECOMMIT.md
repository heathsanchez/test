# Representation-Change V1 — frozen precommit

## Question
After a separator resolves a live rival, does retaining the resulting distinction as explicit structured state improve later protected decisions compared with retaining only the raw outcome, prose memory, or an ablated structure?

This is a mechanistic follow-up to Separator Construction V1. It does **not** test human subjective insight, weight change, or unrestricted autonomous discovery.

## Scientific target
Test the developmental step:

`separator outcome -> retained representation -> later capability`

The core claim under test is not that memory helps, but that a future-relevant derived distinction can become reusable state whose removal reduces later performance.

## Frozen cases
Six source-distinct historical lineages are frozen in `cases.json`:
- Lean predecessor projection reuse
- Lean canonical observed-environment identity
- SAIR constructor-family exhaustion
- Triskelion carry/interface state
- MathGraph non-unique repair version space
- ETP future-behaviour quotient

Each case contains:
1. a prior separator outcome;
2. a later, previously unseen decision problem from the same structural family;
3. four candidate next actions with exactly one frozen correct action;
4. a prose memory and a typed structured-state representation of the same learned distinction.

The later decision does not literally repeat the separator experiment.

## Arms
All arms receive the same later problem and candidate actions.

1. `RAW_OUTCOME` — only the observed separator result is retained; no derived abstraction is supplied.
2. `PROSE_MEMORY` — the verified lesson is retained as ordinary prose.
3. `STRUCTURED_STATE` — the same lesson is retained as compact typed state (`TYPE/RELATION/SCOPE/ACTION`).
4. `STRUCTURED_ABLATION` — same structured format and comparable length, but the decisive relation/action field is replaced by an outcome-neutral placeholder.

All arms use the same model, temperature 0, one call per case, and max 180 output tokens.

## Protected endpoint
The model must return exactly `CHOICE: <A|B|C|D>` plus one short reason. The primary scorer uses exact frozen choice only. Reasons are stored for audit but do not affect the primary score.

## Primary predictions
A developmental-state signal requires both:

`STRUCTURED_STATE > RAW_OUTCOME`

and

`STRUCTURED_STATE > STRUCTURED_ABLATION`

on exact later-decision accuracy.

## Secondary comparisons
- `PROSE_MEMORY > RAW_OUTCOME` measures whether retained semantic content alone changes later capability.
- `STRUCTURED_STATE > PROSE_MEMORY` would support an additional advantage from explicit typed organization.
- `PROSE_MEMORY ~= STRUCTURED_STATE > RAW_OUTCOME` would support retention/content but not a special graph/state-format claim.
- If `RAW_OUTCOME` is at ceiling, the later decisions are too easy and no representation conclusion is permitted.

## Frozen model/resource boundary
- model: `gpt-4.1-mini` unless workflow overrides `UVRM_MODEL`
- temperature: 0
- max output tokens: 180
- one model call per case/arm
- 6 cases x 4 arms = 24 calls
- fixed ordering seed: 2026082405
- no retrieval, tools, self-verification, or external context

## Claim boundary
A positive result supports a bounded causal claim: retaining a verified derived distinction changes later action selection under a frozen model and budget, and ablating the decisive state removes part of that gain. It would not establish weight-level learning, unrestricted constructor invention, or a literal cognitive epiphany.
