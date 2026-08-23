# Research Controller V5 — generation failure is not frame failure

V5 addresses the hardest remaining confound in V4: **the controller can only select among candidate experiments that somebody generated.** If the current candidate pool contains no separator, that may mean the frame is inadequate — or merely that proposal search was weak. V5 refuses to infer the former from the latter.

## Core separation

The controller now distinguishes:

`candidate-generation failure != evidence of representation/frame failure`.

When all currently available actions have zero robust discrimination:

- if the declared candidate-generation boundary is still open -> `EXPAND_CANDIDATES`;
- only after that boundary is prospectively declared exhausted may the controller use the null pool as evidence to MAP/REFRAME.

This is the same anti-overreach principle used at the object level: not found is not not reachable.

## Adversarial prediction audit

Candidate actions are still scored by robust worst-case rival elimination over uncertain outcome sets. V5 adds a proposer/critic asymmetry:

- the proposer may predict possible outcomes for each live rival;
- an independent critic may **widen** those outcome sets by identifying plausible omitted outcomes;
- the critic may not narrow them.

Therefore an overconfident proposer cannot create artificial information value simply by writing perfectly separated point predictions. If a rival outcome is plausibly shared, the discrimination score falls.

This is a software-level mechanism; the prospective experiment must freeze how proposer and critic are instantiated so the critic cannot see protected outcomes.

## Import channel correction

V4 was too restrictive about outside material: it required an internal stall before an import could even add a hypothesis. That does not faithfully model real research. Useful outside material can arrive before the local process is visibly stuck.

V5 separates **arrival/admission** from **activation**:

- a paper, comment, repo, conversation, offline observation, analogy, or tool may arrive at any time;
- if it has a concrete structural mapping and generates a measurable differential prediction, its proposed rival may enter the hypothesis buffer;
- arrival does not force belief, REFRAME, or selection;
- an import-derived experiment competes with local experiments under the same robust discrimination, gate, scaffold, risk, and budget rules.

Thus a strong imported idea can be used early if it genuinely offers a better deciding experiment, while a merely interesting analogy remains inert.

## Goal/metric gate

V5 adds one upstream strategic check: if the measured objective is not established as aligned with the actual target, the controller returns `AUDIT_GOAL_METRIC` before optimizing it further. This prevents highly disciplined research from becoming highly efficient Goodharting.

This gate should be used sparingly and must itself be evidenced; ordinary difficulty is not evidence that the objective is wrong.

## Current controller stack

The operational stack is now:

1. validate apparatus and objective/metric;
2. maintain live rival hypotheses;
3. maintain an explicit remaining resource budget;
4. generate candidate actions from current-frame search, mapping, reframing, outside imports, retained structures, and tools;
5. adversarially widen candidate predictions;
6. apply hard gates: apparatus, closure-before-invention, success-attack, budget;
7. choose the action with greatest robust worst-case rival elimination, with lifecycle/mode, scaffold, risk, and cost only as tie-breakers;
8. update the live rival set from the external observation;
9. treat an outcome predicted by no rival as `SURPRISE`, not as confirmation of a preferred explanation;
10. when no useful candidate exists, distinguish incomplete candidate search from a bounded same-frame null before reframing;
11. attack successful results with controls/ablations before retention;
12. transfer and test retained structures against active RAW_RECONSTRUCT baselines.

## What is still NOT solved

V5 does not establish that candidate generation has been exhausted in an open-ended natural domain. `candidate_generation_exhausted=True` is meaningful only relative to a frozen declared generator family/budget. It must never be interpreted as metaphysical impossibility.

V5 also does not solve creative hypothesis generation. It only prevents failure of a finite proposal process from being silently relabeled as evidence for a new representation.

## Prospective experiment

Do not tune V5 on historical next-action labels.

On an untouched mechanically selected task stream, freeze:

- task ordering and anti-contamination boundary;
- base model, tools, verifier, context and resource budgets;
- candidate generators and their per-step budgets;
- independent prediction critic and widening rule;
- stopping/exhaustion rule for each declared generator family;
- LOCAL, RAW_RECONSTRUCT, V5_FULL, V5_SELECTION_ABLATION, V5_STATE_SHUFFLE arms;
- where naturally available, V5_IMPORT and V5_NO_IMPORT arms using imports timestamped before protected outcomes.

Primary endpoint remains externally verified terminal capability under the fixed primary budget. Report separately: terminal successes, robust rival elimination, surprises, residual sharpening, mode/lifecycle switches, candidate-generation expansions, import use, full cost vector, and later causal effects of retained structures.

A positive meta-reasoning result requires prospective outcome differences, not retrospective agreement with human research choices.
