# Residual-OOCR → Verified Jump V1 — frozen precommit

## Question
Can a frozen LLM infer a hidden cross-residual abstraction from distributed pre-discovery evidence, and can requiring a verifier-facing differential prediction improve the quality of the inferred abstraction and next experiment?

This is a retrospective prequential benchmark over real research lineages. Later successful abstractions/tests are used only as protected scoring targets; they are not shown in prompts.

## Scientific target
Test the proposed discovery bridge:

`distributed residual evidence -> latent relational hypothesis -> deciding test -> reusable future-relevant state`

This experiment tests the **proposal + separator** portion only. It does **not** establish unrestricted constructor invention or prospective autonomous discovery.

## Frozen cases
Six source-distinct historical lineages are frozen in `cases.json`:
- Lean parent/projection reuse
- Lean observed-environment identity
- SAIR boundary-context exhaustion
- Triskelion cross-component obstruction
- MathGraph non-unique repair
- ETP future-behaviour quotient

Each case contains only evidence available before the named abstraction/next move, plus hidden protected semantic targets for (a) latent abstraction and (b) deciding experiment.

## Arms
All arms use the same model, one call per case, temperature 0, and max 260 output tokens.

1. `LOCAL` — evidence snippets are presented as independent observations; do not synthesize a hidden common structure.
2. `RAW_GLOBAL` — all snippets are visible together with an ordinary research-next-step instruction.
3. `OOCR_JOIN` — explicitly infer the latent structure jointly implied by the scattered evidence and propose the next move.
4. `OOCR_VERIFY` — infer the latent structure and state the smallest differential experiment that would distinguish it from the strongest simpler rival.
5. `SHUFFLED` — same OOCR_VERIFY instruction, but the evidence for each case is replaced by evidence snippets from other cases under a frozen permutation. This is the anti-coherence control.

The SHUFFLED arm is scored against the original case target. Its purpose is to detect prompt priors or generic answer leakage.

## Frozen model/resource boundary
- model: `gpt-4.1-mini` unless `UVRM_MODEL` overrides in workflow
- temperature: 0
- max output tokens: 260
- one model call per case/arm
- 6 cases × 5 arms = 30 calls
- fixed case/arm ordering seed: 20260824
- no retrieval, tools, or model-side verifier calls

## Protected scoring
For each response, an outcome-blind deterministic scorer computes:

- `abstraction_score`: fraction of hidden abstraction concept groups hit
- `experiment_score`: fraction of hidden deciding-test concept groups hit
- `joint_score = (abstraction_score + experiment_score)/2`
- `joint_pass`: abstraction_score >= 2/3 AND experiment_score >= 1/2 AND no forbidden concept group is hit

Concept groups are disjunctive lexical families frozen in `cases.json`. They are not shown in prompts.

This scorer is intentionally simple and auditable. Any obvious semantic false negative found after the run is a measurement residual for a future benchmark; V1 scores will not be retroactively changed.

## Primary comparison
The primary directional prediction is:

`OOCR_VERIFY > RAW_GLOBAL` on mean joint score,

with the additional anti-sham condition:

`OOCR_VERIFY > SHUFFLED`.

## Secondary comparisons
- `OOCR_JOIN > RAW_GLOBAL` supports benefit from explicit latent-structure inference.
- `OOCR_VERIFY >= OOCR_JOIN` supports value from forcing a differential verifier-facing separator rather than analogy alone.
- `RAW_GLOBAL > LOCAL` measures ordinary benefit of global evidence aggregation.

## Interpretation frozen before outputs
- If OOCR_VERIFY beats RAW_GLOBAL and SHUFFLED: evidence that explicit global latent-structure inference plus separator discipline extracts decision-relevant structure from dispersed residuals beyond ordinary aggregation.
- If OOCR_JOIN beats RAW_GLOBAL but OOCR_VERIFY does not improve: joining helps, verifier-facing discipline adds no measured value here.
- If RAW_GLOBAL matches OOCR arms: the special OOCR framing is unnecessary; ordinary context aggregation explains the effect.
- If SHUFFLED matches correct evidence: target leakage/generic prompt priors remain a serious rival.
- If all arms perform poorly: the evidence carrier or scoring target is inadequate; do not infer an LLM capability failure.

## Claim boundary
A positive V1 result would not prove a literal cognitive 'Aha', grokking, unrestricted abduction, or constructor-language expansion. It would establish only a bounded mechanism: dispersed verified residual evidence can support recovery of a hidden future-relevant abstraction and separator under a frozen model/resource boundary.
