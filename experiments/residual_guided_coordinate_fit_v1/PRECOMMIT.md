# Residual-Guided Coordinate Fit V1 — frozen precommit

Goal: test whether verified iterative residual feedback can fit latent coordinates after the correct law family has already been identified.

Background residual: prior protected runs reliably selected the `add_mod4` family but usually failed to identify latent prefix bases/suffix offsets. This benchmark therefore fixes the executable law family and tests coordinate fitting only.

Frozen cases: the exact eight arbitrary worlds from Law Induction V1d / Latent Coordinate Induction V1. Deterministic Python is the verifier.

Arms:
- ONE_SHOT: one model proposal of latent coordinates.
- RANDOM_RESTART: four independent model proposals with no verifier feedback; external verifier retains the proposal with highest training fit (ties resolved by earliest proposal).
- RESIDUAL_GUIDED: four sequential proposals. After each proposal, deterministic Python returns only exact mismatching observed pairs plus predicted/verified outputs. The next proposal may revise coordinates using that residual.
- CSP_ORACLE: deterministic exhaustive coordinate solver, no LLM; defines achievable ceiling.

All LLM arms use the same model (gpt-4.1-mini), temperature 0, same executable coordinate schema, and maximum four proposals per world except ONE_SHOT, which intentionally measures the one-pass baseline. RANDOM_RESTART and RESIDUAL_GUIDED therefore have matched proposal budgets.

Primary endpoint: exact held-out action accuracy of the retained final/best coordinate law.
Secondary endpoints: fraction reaching 7/7 verified training fit; mean best training fit; proposal number at first 7/7.

Primary scientific prediction: RESIDUAL_GUIDED > RANDOM_RESTART on held-out accuracy. Secondary: RESIDUAL_GUIDED > ONE_SHOT; CSP_ORACLE = 8/8. If RESIDUAL_GUIDED does not beat RANDOM_RESTART, verified mismatch feedback has not shown causal navigation value under this frozen budget.

No changes after protected run begins.