# Law Induction V1d — frozen precommit

Goal: isolate law formation itself by removing the second-LLM application confound.

Use the same eight frozen arbitrary symbolic worlds as V1/V1b/V1c. Each exposes seven verified observations and one held-out combination. The candidate law must be returned in a small executable DSL and is evaluated deterministically by Python.

Allowed DSL kinds:
- `add_mod4`: `{kind:"add_mod4", base:{A:0..3,B:0..3,C:0..3,D:0..3}, offset:{X:0..3,Y:0..3}}`; action codes are frozen J=0,K=1,L=2,M=3 and prediction is `(base[prefix]+offset[suffix]) mod 4`.
- `lookup`: `{kind:"lookup", map:{"AX":"J",...}}`; predicts only explicitly stored pairs. A missing held-out pair is a failure.

No other law kind is executable. This intentionally tests whether an arm induces the reusable compositional law rather than merely restating the observed table.

Arms:
- RAW_RECONSTRUCT
- JOIN_DOTS
- RIVAL_SEPARATOR
- VERIFIED_RESIDUAL
- ORACLE_LAW (deterministic true law, no model call)

For each induced candidate, deterministic scoring records: parse validity, training consistency (7/7 observations), held-out correctness, and law kind. Primary endpoint is exact held-out accuracy. Primary prediction: VERIFIED_RESIDUAL > RAW_RECONSTRUCT. Secondary: RIVAL_SEPARATOR > RAW_RECONSTRUCT; JOIN_DOTS > RAW_RECONSTRUCT. Oracle must be 8/8 by deterministic evaluator before scientific calls run.

Frozen model: gpt-4.1-mini; temperature 0; one induction call per case/arm; max_tokens 220; same eight worlds as V1. No application LLM. No changes after protected run begins.