# Controller V3 — Research-yield selection, not historical imitation

V2 separated **research lifecycle** from **epistemic mode**. V3 adds the missing third layer: selection among concrete candidate experiments.

The controller now asks three distinct questions:

1. **Lifecycle** — REPAIR / DISCOVER / VERIFY / TRANSFER / RETAIN.
2. **Mode** — EXPLOIT / INSPECT / MAP / REFRAME / DISCRIMINATE.
3. **Action** — which actual experiment should be run next?

V3 does not train an action classifier on more historical labels. Candidate actions declare their predicted observable outcomes under every live rival hypothesis. Selection maximizes **worst-case rival elimination** first, then uses lifecycle/mode fit, scaffold additions, semantic risk, and an explicit resource vector as tie-breakers.

For hypotheses H and an experiment-induced outcome partition, the distribution-free discrimination score is:

`D(a) = |H| - max_o |{h in H : prediction(a,h)=o}|`.

This avoids fabricated Bayesian probabilities and avoids an arbitrary weighted utility scalar. A result can be scientifically useful even when it falsifies the favored mechanism.

## Hard gates

**Apparatus first.** If the apparatus is invalid, semantic actions are inadmissible until a repair action restores a valid observation path.

**Closure before invention.** If a proposed missing representation/object may already exist, representation-changing actions are inadmissible while a direct closure inspection is available.

**Imports have no authority.** Papers, comments, repos, conversations, analogies, or offline observations can generate candidate hypotheses/actions only when internal evidence already warrants inspection, mapping, or reframing. Retrieval novelty is not evidence.

**No novelty bonus.** When a same-frame action separates more live rivals than a reframe, V3 takes the same-frame separator. Reframing is a means, not an objective.

## What V3 fixes

V2 could say `DISCOVER + REFRAME` but did not decide whether a particular reframe was more informative than a cheap local separator. It also left "information gain" qualitative. V3 gives a predeclared, inspectable selection rule that does not depend on the eventual outcome being favorable.

The adversarial test suite checks that:

- separators beat flashy non-discriminating patches;
- infrastructure repair gates semantic inference;
- closure inspection beats premature representation invention;
- a stronger local separator beats a prettier reframe;
- equal-value ties prefer the warranted mode and lower scaffold/risk/cost;
- external imports are inert without an internal trigger;
- every candidate must account for every live rival.

These are controller invariants, not evidence that V3 improves real research.

## Prospective boundary

**Do not tune V3 on additional historical next-action labels.**

The next evidentiary test is prospective. Freeze an untouched task stream and compare, under matched base model, tools, verifier access, context, and total budgets:

- `LOCAL` — strong direct agent, normal reflection/retry;
- `RAW_RECONSTRUCT` — LOCAL plus all permitted raw history and active permission to reconstruct any useful structure;
- `V3_FULL` — same information plus the frozen lifecycle/mode/action controller and admitted compiled structures;
- `V3_SELECTION_ABLATION` — same state and candidate actions as V3_FULL, but consume candidates in a deterministic shuffled order rather than by discrimination score;
- `V3_STATE_SHUFFLE` — equal-size structured state with causal/trajectory associations shuffled;
- optional `V3_IMPORT` — V3_FULL plus outside candidate material selected without protected-outcome access.

Primary endpoint must remain **externally verified terminal capability gained per fixed model-call budget**. Report separately:

- terminal verifier successes;
- live rivals eliminated by externally observed outcomes;
- residual sharpening events that change the admissible next-action set;
- model calls, verifier calls, candidate count, tokens, wall time;
- retained structures admitted/rejected;
- later effects of retained structures under ablation;
- RAW_RECONSTRUCT cost to produce a verifier-behaviorally equivalent substitute.

Do not collapse these into a single post-hoc score. A controller can improve diagnosis without improving terminal capability; that is a narrower result and must be reported as such.

## Recursive-development gate

A strong recursive claim requires a prospective chain:

`P1 -> K1`, `(P2,K1) -> K2`, `(P3,K2) -> T3`,

with `-K1`, `-K2`, RAW_RECONSTRUCT, and sham/equal-size controls. The claim is supported only if earlier admitted structure causally lowers cost or changes matched-budget reachability of acquiring the next structure, and the later structure in turn does the same downstream.

V3 itself makes no such claim. It is the frozen selection policy to be tested.
