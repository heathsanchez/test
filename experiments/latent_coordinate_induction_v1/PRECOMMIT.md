# Latent Coordinate Induction V1 — frozen precommit

Goal: test the residual from Law Induction V1d: the model found the correct compositional law family (`add_mod4`) but usually failed to identify a latent coordinate assignment that satisfies the verified observations.

Use exactly the same eight frozen arbitrary worlds as Law Induction V1d. The evaluator remains deterministic Python. No LLM is used to apply or judge a proposed law.

Arms, with matched model/temperature/token budget:
- RAW: infer the best reusable executable law.
- JOIN_DOTS: explicitly connect the observations into a latent common structure.
- RIVAL: compare simple rival explanations and retain the best verified predictive law.
- VERIFIED_RESIDUAL: use the existing verified-residual induction instruction.
- LATENT_CONSTRUCT: explicitly permit unobserved latent coordinates / gauge choices when they compress all observations; construct coordinates, test them against every verified observation, and output the surviving executable law.
- ORACLE_LAW: deterministic true law, evaluator ceiling only.

All scientific arms must output one executable JSON law in the same frozen language: `lookup` or `add_mod4`. Action codes are J=0,K=1,L=2,M=3. Python scores parse validity, training consistency (7/7), and the unseen held-out pair.

Primary endpoint: held-out exact accuracy. Primary prediction: LATENT_CONSTRUCT > RAW. Secondary predictions: LATENT_CONSTRUCT > JOIN_DOTS, LATENT_CONSTRUCT > RIVAL, and LATENT_CONSTRUCT > VERIFIED_RESIDUAL. Oracle must be 8/8.

Mechanistic interpretation frozen before run:
- If LATENT_CONSTRUCT improves while the law family remains the same, explicit latent-representation construction closes part of the parameter-identification residual.
- If all arms remain low, the remaining bottleneck is not permission to invent latent coordinates; map whether search, constraint solving, identifiability, or output parameterization is failing.
- If all arms reach ceiling, the explicit instruction is unnecessary on this family.
- If oracle fails, measurement is invalid.

Frozen model: gpt-4.1-mini; temperature 0; max_tokens 260; eight worlds; deterministic evaluator; fixed shuffled order. No changes after the protected trigger begins.