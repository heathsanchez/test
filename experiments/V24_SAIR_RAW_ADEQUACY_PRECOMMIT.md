# V24 — SAIR Raw-Domain Adequacy Bridge

## Goal

First external-natural-domain transplant after V23. No manually distilled developmental episodes are supplied.

Raw inputs are the official public SAIR Stage-2 problem rows (`equation1`, `equation2`) from the external repository `SAIRcompetition/equational-theories-lean-stage2`.

## Frozen split

- representation/policy development: `normal`, `hard1`, `hard2`
- held-out natural distribution: `hard3`

The split is by official SAIR difficulty source, not random rows.

## Learner-visible raw interface

The learner receives only equation strings and generic parser/execution primitives. It is not given hand-authored developmental roles, StrCC classes, witness types, context-role names, or domain-specific feature labels.

The script derives anonymous raw observation ports from:

1. syntax-tree statistics of the two equations;
2. exact exhaustive behavior over all 16 binary operations on `Fin 2` (counts of operations satisfying the hypothesis, target, both, and counterexample incidence).

The public `answer` field is withheld while the raw observation representation is constructed and is exposed only for downstream policy fitting/audit.

## Policy question

Can a compact program over the frozen raw observation ports predict the required certificate family:

- `PROOF` for true implications;
- `COUNTERMODEL` for false implications;

on the held-out `hard3` distribution?

This is deliberately a first adequacy bridge, not the final DI claim. A pass would show a raw externally defined mathematical domain can support learned developmental coordinates without hand-distilled episode semantics. A failure is expected to identify what raw information is missing.

## Gates

1. external SAIR repository and official splits are used;
2. no manually authored episode labels/roles enter the representation;
3. representation construction does not use `answer`;
4. held-out source is `hard3` only;
5. policy beats majority baseline on held-out `hard3`;
6. policy beats syntax-only ablation;
7. shuffled-verifier control degrades held-out performance;
8. every `Fin 2` counterexample observation is independently rechecked by exact evaluation.

The umbrella gate is `SAIR_RAW_ADEQUACY_BRIDGE_GATE`.

## Boundary

This does not yet discover an unrestricted adequacy map, run the Lean judge for every held-out action, or prove cross-domain developmental identity. It tests the first raw natural-domain bridge using exact finite verifier-visible behavior plus generic raw syntax.