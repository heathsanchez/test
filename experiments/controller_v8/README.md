# Research Controller V8 — generator attribution tournament

V7 made same-frame exhaustion auditable. V8 attacks the remaining question: where does the useful new move actually come from?

The main risk is attribution error. A human may notice a move first that another generator would have found shortly afterwards; two generators may emit syntactically different versions of the same mechanism; a leaked import may appear prescient; or one generator may simply receive more search opportunity.

V8 therefore separates **first arrival**, **independent rediscovery**, **substitutability**, and **unique causal contribution**.

## Frozen tournament arms

Recommended generator families:

- LOCAL — nearby continuation, deeper search, parameter sweeps;
- RESIDUAL — moves derived from a sharp residual/obstruction;
- STRUCTURAL — analogies, cross-domain mechanism maps, changed decompositions;
- RETAINED — laws/macros/constructors compiled from earlier episodes;
- IMPORT — papers, comments, repos, conversations, offline observations;
- HUMAN — manually injected candidate moves, timestamped separately.

Each generator declares a finite slot basis and matched budget before protected outcomes.

## Canonical move identity

Attribution is over `canonical_move`, not proposal text. If HUMAN says “splice cached parent tail” and RESIDUAL independently proposes a behaviorally equivalent splice, they count as the same move with multiple provenance records.

Canonicalization must be frozen before protected evaluation where possible, or decided by an outcome-blind equivalence procedure. Otherwise identity itself becomes hindsight leakage.

## Four different claims

1. **First discovery:** which generator first put the deciding move on the table?
2. **Independent rediscovery:** did another generator later produce an equivalent move without seeing the first generator's proposal?
3. **Substitutability:** after removing one generator, does some other generator still produce an equivalent verified deciding move within its frozen budget?
4. **Unique contribution:** does removing the generator eliminate all verified deciding moves under the matched tournament boundary?

These must never be conflated.

A human-first result with later independent RESIDUAL rediscovery is evidence about timing, not unique human necessity. A HUMAN-only deciding move under matched frozen budgets is much stronger evidence that candidate generation remains the missing automated capability.

## Leakage and opportunity controls

- protected-outcome proposals receive zero attribution and cannot define candidate identity;
- undeclared generator slots are excluded;
- per-generator budget is enforced before attribution;
- equivalent moves are deduplicated rather than inflating proposal counts;
- first-arrival ties receive shared credit;
- verified success, attack survival and transfer survival are recorded separately from generation.

## What to score

For each generator and episode record:

- valid unique moves generated;
- deciding moves generated;
- first discovery of deciding moves;
- verified moves;
- attack survivors;
- transfer survivors;
- duplicate/invalid/leaked proposal rate;
- time/rank/cost to first deciding move;
- substitutable deciding moves;
- unique deciding moves after generator ablation.

Do not collapse these immediately into one weighted score. The vector is more informative.

## Strongest next experiment

Run this prospectively on untouched episodes. Candidate streams must be isolated until their proposals are frozen so that rediscovery is genuinely independent. After freezing, pool candidates, apply the same prediction critic and V7 controller selection policy, and execute under matched verifier/resource budgets.

The key comparisons are:

- HUMAN vs RESIDUAL/STRUCTURAL/IMPORT first-discovery latency;
- HUMAN ablation reachability;
- automated-generator union vs HUMAN;
- individual automated-generator ablations;
- RETAINED vs RAW_HISTORY reconstruction where retained state contributes a move.

The outcome taxonomy is deliberately graceful:

- automated generators routinely rediscover human moves -> human contribution is mostly search timing;
- automated union finds the moves but later/more expensively -> candidate-generation efficiency gap;
- only HUMAN finds critical moves -> human reframing/import generation remains an unsolved capability;
- STRUCTURAL/IMPORT/RETAINED generators uniquely find critical moves -> evidence that explicit meta-search adds reach beyond local continuation;
- retained structures generate later unique moves that RAW_HISTORY cannot reconstruct within budget -> stronger cumulative-development evidence.

V8 is still a protocol/invariant implementation, not evidence that automated generators already match human injection. Its purpose is to make the next prospective result interpretable.