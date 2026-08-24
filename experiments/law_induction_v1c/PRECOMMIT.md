# Law Induction V1c — measurement repair only

Same eight worlds, scientific arms, hypotheses, model, and induction budgets as V1/V1b. V1 and V1b were measurement-invalid because the application boundary failed even for the oracle.

Only measurement changes:
- application calls may reason internally and receive 160 output tokens;
- scorer accepts the final `CHOICE: J|K|L|M` occurrence anywhere in the response;
- an oracle gate must achieve 8/8 before any scientific arm runs.

Scientific arms: RAW_RECONSTRUCT, JOIN_DOTS, RIVAL_SEPARATOR, VERIFIED_RESIDUAL. Primary remains VERIFIED_RESIDUAL > RAW_RECONSTRUCT on held-out exact accuracy. Secondary comparisons unchanged.

Frozen model gpt-4.1-mini, temperature 0, induction max_tokens 180, application max_tokens 160, eight unchanged worlds. No scientific interpretation if oracle gate fails.