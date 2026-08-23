# Research Controller V6 — auditable generator boundaries and hard post-success gates

V5 fixed an important overreach: failure to *generate* a separator is not evidence that the representation/frame is inadequate. V6 attacks the remaining loophole in that fix.

In V5, `candidate_generation_exhausted` was still a Boolean supplied by the caller. That means an agent could silently convert search failure into representation failure by declaring the search exhausted. V6 removes that authority.

## 1. Exhaustion is now derived, not asserted

V6 introduces a frozen generator ledger:

- `GeneratorSpec(name, family, quota, required)` declares the candidate-generation boundary before outcomes;
- `GeneratorRun` records attempts, audited candidates, pending candidates, and leakage;
- `generator_boundary_exhausted(...)` is true only when every required generator has met its quota, no generated candidate remains unaudited, no protected-outcome leakage occurred, and no unresolved surprise remains.

Therefore:

`NO_SEPARATOR_IN_CURRENT_POOL` does not imply `REFRAME`.

Only:

`NO_SEPARATOR_AFTER_AUDITED_FROZEN_GENERATOR_EXHAUSTION`

can contribute evidence for a frame change.

This makes the controller adversarial about its own proposal process, not merely about object-level hypotheses.

## 2. Candidate generators become first-class experimental objects

Every `CandidateAction` has a declared `generator`. This allows later prospective comparison of candidate sources such as:

- local exploit/search;
- residual-derived structural maps;
- representation-changing synthesis;
- retained laws/macros;
- outside paper/comment/repo/analogy/observation imports;
- human-injected candidates.

The controller does not reward any source for novelty. Provenance exists so that successful deciding experiments can later be attributed and generators can be ablated under matched budgets.

An action from an undeclared generator is rejected.

## 3. Protected-outcome leakage is an evidentiary disqualifier

A candidate generated with protected-outcome access is excluded from action selection. The same applies to generator-ledger exhaustion: a leaked required generator cannot close the boundary.

This is necessary for the next prospective experiment, where candidate generators must be compared without access to held-out outcomes.

## 4. Discrimination is normalized

V5 ranked raw worst-case hypothesis elimination. Raw counts grow with the number of live hypotheses, so expanding the rival set could change scores simply by changing cardinality.

V6 uses:

`robust_split_fraction = worst_case_elimination / (n - 1)`

with range `[0,1]` for `n>1`. A perfect separator scores `1.0` regardless of rival-set size.

This does not solve semantic duplicate hypotheses by itself; that remains a future hypothesis-canonicalization problem. It does remove the simplest cardinality artifact.

## 5. Success now creates hard gates

V5 preferred ablation/control actions after a green result, but if no control existed it could fall back to ordinary actions. That was too permissive.

V6 makes the lifecycle mandatory:

`VERIFIED -> ATTACK -> TRANSFER -> RECONSTRUCT -> RETAIN`

If the required next-stage action does not exist, the controller emits one of:

- `GENERATE_ATTACKS`
- `GENERATE_TRANSFER_TESTS`
- `GENERATE_RECONSTRUCTION_TESTS`

It cannot continue ordinary exploitation instead.

Retention is available only after all three post-success gates pass.

## 6. Surprise reopens the search boundary

If an observed outcome is compatible with none of the live hypotheses, V6 preserves the current hypothesis set and marks a surprise. An unresolved surprise prevents generator exhaustion.

So an anomalous result cannot coexist with a declaration that the current explanation/search boundary has been fully exhausted.

## 7. Outside material remains an anytime input channel

Papers, comments, conversations, repos, offline observations, analogies, or other outside material may arrive before or after a stall. A new rival enters the hypothesis buffer only when the import supplies both:

- a structural mapping; and
- a differential prediction.

Arrival alone does not trigger a reframe or belief update.

## What V6 now separates

The controller distinguishes at least these failure classes:

- apparatus/infrastructure failure;
- objective/metric misalignment;
- candidate-generation/search failure;
- unsharp residual / mapping failure;
- exhausted same-frame failure suggesting reframe;
- post-success causal attack failure;
- transfer failure;
- reconstruction/retention failure;
- hypothesis-model surprise.

That is much closer to the intended developmental loop than a flat `try harder / reframe` policy.

## Evidence status

The V6 invariant suite is still controller-logic evidence, not prospective evidence that an LLM using V6 solves more real research problems. It closes identifiable logical loopholes exposed by V5.

The next decisive experiment should therefore target the remaining human-looking component rather than add more controller labels.

## Next experiment: frozen candidate-generator tournament

Freeze a set of unresolved episodes before generator outputs are inspected. For every episode, give matched context and budgets to independent candidate generators:

1. ordinary local LLM search;
2. structured residual-derived generation;
3. cross-domain structural retrieval/import generation;
4. retained-law/macro generation;
5. human-injected candidate stream when available.

For each generated candidate, freeze its predicted outcome sets before protected execution and run the same independent critic. Score:

- whether the eventual deciding experiment appeared;
- rank/time/cost at which it appeared;
- audited robust split fraction;
- duplicate and invalid-candidate rate;
- protected verifier success;
- causal survival under attack;
- transfer survival;
- generator ablation and substitution.

The central question is no longer merely whether the controller knows when to change mode. It is:

> Which candidate-generation mechanism puts the missing move on the table, and can that capability be reproduced without privileged human injection?

A positive result here would localize and operationalize a substantially more important part of the research loop than further retrospective mode-fitting.
