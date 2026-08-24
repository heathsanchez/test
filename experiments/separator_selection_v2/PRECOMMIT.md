# Separator Selection V2 — frozen precommit

Question: once the latent abstraction is supplied, is explicit rival framing enough, or does forcing counterfactual predictions improve selection of the actual deciding intervention?

Six historical cases are frozen as multiple-choice intervention problems. All arms receive identical evidence, latent abstraction, and four candidate interventions. Hidden scoring is exact intervention ID; no lexical semantic scorer is used.

Arms (one call/case, temperature 0, max 180 tokens): GENERIC, RIVAL, COUNTERFACTUAL, VERIFIED_RESIDUAL. 24 calls, seed 20260824.

Primary: COUNTERFACTUAL > GENERIC on exact choice accuracy. Secondary: RIVAL > GENERIC; VERIFIED_RESIDUAL > RIVAL would show value beyond the compressed rival rule. If VERIFIED_RESIDUAL ~= RIVAL, retain the simpler rule. If all arms saturate, this carrier is too easy and should not support a methodological claim.

Claim boundary: retrospective prequential intervention-selection benchmark; it does not establish prospective discovery.