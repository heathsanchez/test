# Research Controller V7 — slot-complete search and observational rival classes

V6 made candidate-generation exhaustion auditable, but it still had two exploitable weaknesses.

First, its generator boundary used attempt quotas. An agent could satisfy a quota with repeated, near-duplicate or trivial attempts and then incorrectly claim that same-frame search was exhausted.

Second, discrimination still counted raw hypothesis labels. If the rival set contained duplicate or observationally indistinguishable explanations, merely adding labels could alter information scores.

V7 closes both loopholes.

## 1. Search exhaustion is coverage over frozen slots, not attempt count

Each generator now declares a finite set of required search slots before outcomes:

- `GeneratorSpec(name, family, required_slots)`
- examples: `depth1`, `depth2`, `countermodel`, `residual_map`, `operator_synthesis`, `closure_inspection`

A `GeneratorRun` records which frozen slots were actually attempted, which remain pending, and whether protected-outcome leakage occurred.

The boundary is exhausted only when every required slot has been attempted with no pending or leaked slot.

This means ten repetitions of the same search move do not equal ten units of coverage.

The stronger rule is:

> Exhaust a declared search *basis*, not a counter.

This is the controller analogue of distinguishing breadth of operator coverage from repeated local effort.

## 2. Every candidate must name the slot that generated it

`CandidateAction` now carries both `generator` and `generator_slot`.

An action from an undeclared generator or undeclared slot is rejected. This makes the candidate-generation trace auditable enough for later ablation and causal credit assignment.

It also lets the future generator tournament ask not only which source found the deciding experiment, but which search operator within that source did so.

## 3. Rivals are scored by observational equivalence classes

V7 computes each live hypothesis's signature across the current audited action language. Hypotheses with identical signatures are collapsed into one observational class for action scoring.

So if two differently named explanations make exactly the same predictions under every currently available experiment, they do not receive double weight merely because they have two labels.

For a candidate action, V7 computes its worst-case surviving **observational classes**, not raw hypothesis count, then normalizes the split to `[0,1]`.

This prevents the simplest form of hypothesis-cardinality gaming while preserving the distinction when a later candidate action actually separates the two rivals.

## 4. Protected leakage cannot define the action language

An action with protected-outcome access is excluded both from selection and from the language used to form observational rival classes.

Otherwise a leaked experiment could retrospectively make two hypotheses appear distinguishable and contaminate the information score of innocent actions.

## 5. V6's hard lifecycle gates remain

A green result still cannot flow directly into retention:

`VERIFIED -> ATTACK -> TRANSFER -> RECONSTRUCT -> RETAIN`

Missing post-success actions emit explicit generation directives rather than allowing ordinary optimization to continue.

## 6. Outside material remains an anytime source

A paper, comment, repo, conversation, analogy or offline observation may arrive at any point. It enters the rival buffer only when it supplies both a structural mapping and a differential prediction.

Outside provenance does not itself earn or lose score.

## Why V7 is materially stronger

The path from repeated failure to representation change now requires all of the following:

1. the apparatus and objective are valid;
2. the residual is represented sharply enough to test;
3. the relevant generator families and search slots were frozen before protected outcomes;
4. every required slot was actually attempted;
5. no slot remains pending;
6. no protected leakage contaminated the generator boundary;
7. no unresolved surprise remains;
8. the audited action language still cannot separate the live observational rival classes.

Only then is `REFRAME` warranted.

That is substantially harder to fake than `we tried many things and none worked`.

## Evidence status

The V7 invariant suite passes locally before commit. This remains logic-level evidence. It does not yet show that a real LLM operating under V7 generates better scientific or mathematical moves.

The next evidence should therefore be prospective rather than another retrospective replay.

## Next decisive experiment — frozen generator tournament

For unresolved real episodes, predeclare generator slots and budgets before any generator sees protected outcomes. Example arms:

- **LOCAL**: direct continuation, deeper search, parameter sweep, nearby proof/solver/operator moves;
- **RESIDUAL**: moves constructed from the sharp residual or named obstruction;
- **STRUCTURAL MAP**: analogies and cross-domain correspondences induced from known successful mechanisms;
- **RETAINED**: laws/macros/constructors compiled from earlier episodes;
- **IMPORT**: candidate moves induced from external papers, comments, repos, conversations or observations;
- **HUMAN INJECTION**: separately logged when a human supplies the move.

Freeze each candidate's predicted outcome sets, apply the same independent widening critic, then execute under matched verifier/resource budgets.

Score at least:

- whether the eventual deciding move appears at all;
- generator and slot that first produced it;
- rank, verifier cost and wall cost when produced;
- audited observational-class split;
- duplicate/invalid proposal rate;
- protected success;
- attack survival;
- transfer survival;
- reconstruction from retained state;
- generator ablation and substitution.

The key empirical question is now extremely sharp:

> When progress depends on a move absent from ordinary continuation, which generator actually puts that move on the table?

If structured residual, retained-state or cross-domain generators reliably recover moves previously supplied by human intervention, then the remaining developmental mechanism has become much more operational rather than merely descriptive.
