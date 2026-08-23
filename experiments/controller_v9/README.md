# Research Controller V9 — outcome-blind move equivalence

V8 separated first discovery, independent rediscovery, substitutability, and unique causal contribution across LOCAL / RESIDUAL / STRUCTURAL / RETAINED / IMPORT / HUMAN generators.

The remaining attribution loophole was equivalence-by-hindsight: after seeing that two syntactically different proposals both succeed, an analyst could declare them to be "the same move" and erase a real generator difference; or do the reverse and call equivalent proposals different mechanisms to inflate novelty.

V9 freezes candidate equivalence before protected outcomes.

## Rule

Two proposals may count as the same move class only if they are behaviorally equivalent under a probe suite declared before protected outcomes.

A protocol contains frozen probes such as:

- semantic effect / preservation;
- resource or search effect;
- transfer behavior;
- relevant intervention scope;
- other domain-specific observables frozen in advance.

Each proposal receives a pre-outcome signature consisting of the allowed outcome set for every probe. Different syntax and provenance may collapse when those signatures match. Identical terminal success does not merge proposals if the frozen signatures differ.

Protected-outcome access disqualifies a proposal from defining or joining an equivalence class for generator attribution.

This gives the attribution rule:

> first discovery and substitution are measured over outcome-blind behavioral move classes, not names and not post-hoc narratives.

## Why this matters for HUMAN versus automated generators

If a HUMAN injection and a RESIDUAL-derived proposal are in the same precommitted behavioral class before the protected run, then later RESIDUAL rediscovery is legitimate substitution evidence even if the implementations look different.

If they only look equivalent after we inspect success, that does not count.

Conversely, if both solve the task but their frozen behavioral signatures differ, they remain distinct candidate mechanisms and neither can erase the other's attribution.

## Current invariant suite

The V9 tests require:

1. different syntax/source may be equivalent under the frozen probe language;
2. different pre-outcome behavior is not merged merely because terminal success might match;
3. protected-result access cannot establish equivalence;
4. an unfrozen equivalence protocol is invalid;
5. incomplete probe coverage cannot be treated as equivalence;
6. source substitution is credited only when another source independently generated a pre-outcome equivalent move.

## Remaining weakness

V9 still assumes the probe language is adequate. A weak probe suite can merge mechanisms that differ in an unmeasured way; an overfine suite can prevent useful compression.

So the next question is no longer "can we define move identity?" It is:

> Can the system learn an adequate move-equivalence probe suite without using protected outcomes, and does that learned suite predict later substitutability?

That should be tested by freezing probe-suite construction on development episodes, then evaluating equivalence predictions on untouched episodes where later ablation/transfer supplies the ground-truth substitutability test.

This is the same general discipline applied one level up: equivalence itself must earn adequacy rather than being supplied as an analyst convenience.
