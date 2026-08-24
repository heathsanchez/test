# Separator Selection V1 — frozen precommit

## Residual from Residual-OOCR V1
Residual-OOCR V1 showed that coherent global evidence matters, but explicit OOCR framing did not beat ordinary global evidence on latent-abstraction recovery. The main weakness was downstream: experiment-selection scores were much lower than abstraction scores.

## Question
Given the same already-correct latent abstraction, can a frozen LLM choose a more genuinely discriminating next experiment when it is given progressively stronger separator discipline?

This isolates the map:

`known latent structure -> smallest deciding experiment`

It does not test abstraction discovery, constructor invention, or unrestricted scientific discovery.

## Cases
Six historical research lineages are frozen in `cases.json`. Each prompt reveals:
- the relevant pre-discovery evidence;
- the correct latent abstraction;
- a strongest simpler rival.

Protected targets encode the historical differential experiment and the outcome distinction it was meant to expose.

## Arms
Same model, one call per case, temperature 0, max 280 tokens.

1. `GENERIC` — simply ask what to try next.
2. `VERIFY` — ask for a test of the supplied abstraction.
3. `RIVAL` — require a test that distinguishes abstraction from the supplied simpler rival.
4. `INFO_GAIN` — require the smallest experiment whose possible outcomes most change which hypothesis survives.
5. `VERIFIED_RESIDUAL` — additionally require frozen boundary/budget, explicit outcome->next-action mapping, closure-before-invention, and preservation of surprise as a new residual.

6 cases × 5 arms = 30 protected calls. Fixed ordering seed 20260824.

## Scoring
Outcome-blind deterministic semantic-family scoring computes:
- `experiment_score`: fraction of protected experiment concept groups hit;
- `separation_score`: fraction of protected rival/outcome-discrimination groups hit;
- `discipline_score`: fraction of protected freeze/outcome-action groups hit;
- `joint_score = (experiment_score + separation_score)/2`.

Primary scientific endpoint is `joint_score`; discipline is reported separately so the VERIFIED_RESIDUAL arm is not rewarded merely for repeating methodological vocabulary.

## Primary prediction
`VERIFIED_RESIDUAL > GENERIC` on mean joint score.

Stronger mechanistic prediction:
`INFO_GAIN > VERIFY` and `RIVAL > VERIFY` on mean separation score.

If VERIFIED_RESIDUAL improves discipline only, without improving joint score, then the extra methodology is procedural overhead rather than better separator selection on this benchmark.

## Claim boundary
A positive result would establish only that explicit rival/information-gain/residual discipline improves next-experiment selection on these bounded retrospective cases. It would not establish autonomous discovery or human-level experimental design.
