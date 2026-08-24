# Law Induction V1b — frozen measurement-repair precommit

Status of V1: scientifically invalid because ORACLE_LAW scored 0/8 after the application response was truncated before the required `CHOICE:` token. V1b changes only the measurement/application boundary; the eight worlds, observations, hidden laws, arms, hypotheses, held-out queries, model, and induction budget are unchanged.

Goal: validly test the bridge from verified episode evidence to a reusable law that changes held-out capability.

Arms:
- RAW_RECONSTRUCT
- JOIN_DOTS
- RIVAL_SEPARATOR
- VERIFIED_RESIDUAL
- ORACLE_LAW (ceiling)

Measurement repair:
1. Application prompts require exactly `CHOICE: <J|K|L|M>` and explicitly forbid explanation.
2. Application max_tokens is 20.
3. Before any scientific arm runs, all eight ORACLE_LAW applications are executed using the same application function and must score 8/8. If not, abort as `MEASUREMENT_INVALID`; no scientific interpretation is permitted.
4. Oracle-gate responses are retained as the ORACLE_LAW rows; they are not rerun.
5. Induction text is never scored. Only held-out exact action accuracy is scored.

Primary scientific prediction, unchanged from V1: VERIFIED_RESIDUAL > RAW_RECONSTRUCT. Secondary: RIVAL_SEPARATOR > RAW_RECONSTRUCT; JOIN_DOTS > RAW_RECONSTRUCT. ORACLE_LAW must equal 1.0 by construction of the validity gate.

Frozen model: gpt-4.1-mini; temperature 0; induction max_tokens 180; application max_tokens 20; same eight worlds; exact scoring; fixed seed. No scientific changes after this precommit.