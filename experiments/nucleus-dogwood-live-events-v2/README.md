# Nucleus × Dogwood live evidence-to-event compiler V2

This experiment removes the hand-authored trace from the qualified Dogwood
promotion gate.

The exact real Nucleus lineage is:

- base authority: `d2bdeadceb1bb6d0695f15126fb23b50f732c4ce`
  (31 residual);
- candidate: `98f87d9e66fb97987427d68180f51a653d626fdb`;
- qualification run: `36638427344`;
- qualification artifact: `11065775422`;
- artifact digest:
  `sha256:2bdd0c6f94f014e698eb59dd4b53effc2f890a3e3628795e6033fcd15c4e2024`;
- exact earned consequence: `other/proj-of-prop` UNKNOWN → REJECT;
- full frozen result: 103 ACCEPT / 60 REJECT / 30 residual / 0 wrong.

`compile_events.py` consumes the qualification `result.json`. It emits a
Dogwood lifecycle event only when the corresponding evidence predicate is
present:

`ResidualObserved → CandidateDerived → ControlsGreen → FullReclosureGreen`.

It always appends an `Admit` request. If reclosure is not green, it emits
`CandidateRejected` instead.

The CI gate replays two histories generated from machine evidence:

1. the untouched real qualification artifact → expected **ALLOW**;
2. a synthetic copy with one injected wrong decision → expected **DENY**.

No lifecycle trace is committed to the repository. Generated traces exist only
inside the qualification artifact.

## Claim boundary

A green result warrants a bounded **evidence-to-temporal-event adapter** for this
Nucleus result schema and source-pinned lineage. It does not authenticate GitHub
events, prove the adapter formally, cover all Nucleus result schemas, or establish
Metatron↔Dogwood semantic equivalence.
