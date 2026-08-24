# Target Quotient Right Question V1 — frozen precommit

## Residual
Right Question Transfer V1 showed that observation-only target-information-gain prompting transferred only partially across mod-2/3/5 latent families: 31.25% exact optimal-query rate, despite a deterministic 100% ceiling. The capstone also showed that dumping explicit latent worlds can hurt.

## Hypothesis
The missing object is a quotient of the surviving hypothesis space by future target consequences. Query selection should improve when the model receives, for each allowed query and each possible query outcome, only the induced distribution of TARGET values among surviving hypotheses—not latent coordinates or full worlds.

## Arms
- OBS_ONLY: observations + target + allowed queries; target-information-gain instruction.
- TARGET_QUOTIENT: same, plus query-outcome -> target-value count tables computed from surviving hypotheses.
- SHAM_MARGINAL: same token-level style of tables, but gives only query-outcome counts and the current marginal target counts, removing the outcome-to-target coupling needed to choose a separator.
- RANDOM_QUERY: deterministic random allowed query.
- OPTIMAL_QUERY: deterministic exact minimum-expected-target-entropy query.

## Frozen benchmark
Recreate the same generator family used by Right Question Transfer V1: additive latent worlds modulo 2, 3, and 5; gauge X=0; 16 protected tasks per family; fixed seed 2026082507 and identical task-generation acceptance criteria.

## Primary
TARGET_QUOTIENT must exceed OBS_ONLY on exact optimal-query rate and downstream target accuracy, and achieve pooled optimal-query rate >= 0.90.

## Secondary
TARGET_QUOTIENT should beat SHAM_MARGINAL, have lower mean target entropy/regret than OBS_ONLY, and remain strong in each modulus family. OPTIMAL_QUERY defines the 100% external ceiling.

No protected result will be used to alter these criteria.