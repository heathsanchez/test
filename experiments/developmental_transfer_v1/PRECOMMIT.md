# Developmental Transfer V1 — frozen precommit

## Question
Does retaining a verifier-induced law change later reachable capability on arbitrary episode-specific worlds where the later task is not solvable from general semantic priors alone?

## Design
Eight fixed synthetic worlds. Each world has an arbitrary four-way action law over a symbolic state. The earlier episode reveals the law; later queries use new symbols and instances from the same hidden law. Five arms receive the same later query but different retained state:

- COLD: no earlier episode state.
- RAW_EPISODE: opaque outcome records only; no distilled law.
- PROSE_LAW: the induced law in natural-language form.
- STRUCTURED_LAW: the same induced law as explicit typed state.
- WRONG_LAW: a matched, incorrect permutation of the law.

One call per case/arm, temperature 0, max_tokens 48, gpt-4.1-mini. Exact action choice is the only performance metric.

## Primary predictions
1. STRUCTURED_LAW > COLD.
2. STRUCTURED_LAW > RAW_EPISODE.
3. STRUCTURED_LAW > WRONG_LAW.

Primary pass requires all three inequalities in mean accuracy.

## Secondary
- PROSE_LAW vs STRUCTURED_LAW tests whether semantic retention is sufficient or typed structure adds value.
- WRONG_LAW < STRUCTURED_LAW is the causal ablation/control against generic extra-context benefit.
- COLD accuracy >= 0.75 is a ceiling warning; interpret any primary failure under that condition as insufficient task difficulty.

## Boundaries
This establishes bounded causal transfer in arbitrary symbolic worlds only. It does not by itself establish human-like insight, neural representation change, or constructor invention.