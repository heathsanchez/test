# Research Controller V4 — uncertainty, surprise, budget, and success attack

V4 is the first version aimed at the actual failure modes of an autonomous research controller rather than replay agreement.

V3 made concrete action selection explicit using worst-case rival elimination. V4 repairs four weaknesses in V3:

1. **Predictions can be uncertain.** Each live hypothesis predicts a *set* of possible observable outcomes. Overlapping sets do not receive discrimination credit. This prevents a proposer from gaining fake information value merely by writing overconfident point predictions.
2. **Resources are hard feasibility constraints.** An experiment outside the remaining frozen budget is inadmissible even when it looks maximally informative. The controller does not call an impossible experiment "high yield" and then hide the opportunity cost in a tie-break.
3. **Unexpected outcomes are first-class evidence.** If an observed outcome was predicted by none of the live rivals, the controller preserves the rival set and records a surprise/model miss. It must map or reframe; it may not force the observation into the favored explanation.
4. **Success creates an attack phase.** A verified target is not automatically retained. If ablation/surrogate/control actions exist, they become the admissible next actions before promotion.

The earlier hard rules remain:

- apparatus validity before semantic inference;
- closure before representation invention;
- no novelty bonus for reframing;
- imports propose rivals, never facts;
- imported rivals require an internally triggered need, a structural mapping, and a measurable differential prediction.

## Operating semantics

At each research state the controller maintains a set of live rival hypotheses `H`, an explicit remaining budget `B`, and candidate experiments with outcome sets under every `h in H`.

For action `a`, V4 scores robust one-step discrimination as the number of hypotheses guaranteed to be eliminated in the worst observable case:

`D(a) = |H| - max_o |{h : o is possible under a,h}|`.

Only budget-feasible and gate-admissible actions can be selected. If all admissible actions have `D=0`, the controller does **not** mechanically select the most sophisticated one:

- unsharp residual -> `MAP`;
- repeated/conditional residual -> `REFRAME`;
- repeated/conditional residual plus an active outside artifact -> `REFRAME_WITH_IMPORT`;
- otherwise -> continue `PUSH` inside the current frame.

This makes the altitude switch an explicit consequence of the live action set, not merely a hard-coded timer.

## Surprise rule

After action `a` produces observation `o`:

- retain every hypothesis whose predicted outcome set contains `o`;
- if none contains `o`, retain all current hypotheses and mark `SURPRISE`;
- do not declare an empty version space to be evidence for whichever reframe was preferred beforehand.

A surprise is a signal that the current hypothesis vocabulary or measurement model is inadequate. It is therefore a legitimate trigger for mapping/reframing in the prospective runner.

## Import rule

Outside material can come from anywhere: paper, article, comment, repo, conversation, offline observation, analogy, new tool, or hand-selected artifact. V4 treats it as a hypothesis generator only.

A proposed imported hypothesis enters the live rival set only when all hold:

1. internal evidence already warrants mapping/reframing/inspection;
2. the import has a stated structural mapping to the current residual;
3. it generates at least one measurable outcome that differs from an existing live rival.

This is intended to preserve the productive "is this related?" channel without turning semantic resemblance into evidence.

## Evidence status

The invariant suite is a software sanity test only. V4 has not yet shown prospective research superiority.

Do not tune V4 against more historical next-action labels.

## Required prospective comparison

Use an untouched, mechanically selected task stream. Freeze case order and all arm definitions before protected outcomes. Match base model, tool interfaces, verifier, context ceiling, model-call ceiling, verifier-call ceiling, candidate budget, tokens where controllable, and wall-time policy.

Arms:

- `LOCAL`: strong direct solver with normal retry/reflection;
- `RAW_RECONSTRUCT`: LOCAL plus the same complete permissible raw history and explicit permission to reconstruct abstractions/operators from it;
- `V4_FULL`: V4 switching + action selection + admitted compiled state;
- `V4_SELECTION_ABLATION`: same candidate actions/state/budget as V4_FULL but deterministic shuffled action order;
- `V4_STATE_SHUFFLE`: equal-size structured state with causal associations shuffled;
- `V4_NO_IMPORT`: full controller with outside-import channel disabled;
- where enough naturally arriving imports exist prospectively, `V4_IMPORT` versus `V4_NO_IMPORT` under an anti-contamination rule.

Primary endpoint remains externally verified terminal capability gained under the fixed primary resource budget. Report decision-changing evidence, rival elimination, residual sharpening, surprise rate, and full cost vector separately; they cannot substitute for terminal capability after the fact.

## Reconstruction control

RAW_RECONSTRUCT may actively derive a substitute `K'` from raw history. A retained object `K` earns more than a memory/compilation claim only when the precommitted verifier-context suite establishes behavioral equivalence/non-equivalence and the matched resource accounting shows the relevant downstream difference.

## Recursive gate

The strongest developmental claim remains a causal chain, not repeated success:

`P1 -> K1`, `(P2,K1) -> K2`, `(P3,K2) -> T3`.

Ablate `K1` during acquisition of `K2`, ablate `K2` on `T3`, and compare both against RAW_RECONSTRUCT and sham/equal-size controls. Any weaker pattern receives a weaker classification.
