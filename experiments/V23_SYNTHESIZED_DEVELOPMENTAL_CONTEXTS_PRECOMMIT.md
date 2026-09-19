# V23 — Synthesized Developmental Contexts

## Frozen question

Can the developmental substitution contexts used to induce witness types be discovered from a lower-level verifier-interaction language rather than supplied as semantic roles such as CLOSE / PRESERVE / COMPOSE / ABLATE / RETAIN?

## Learner-visible structure

The learner receives only:

- opaque witness mechanisms;
- ten anonymous observation ports;
- low-level context-construction primitives `READ(i)`, `READ(j)`, `EQ`;
- an exact finite verifier that executes synthesized context programs.

It does **not** receive:

- semantic context-role names;
- hidden witness-type labels;
- action labels during context induction;
- domain labels.

## Context induction

Generate the complete finite carrier of pairwise equality programs over the ten ports. Let `P_full` be the observational partition induced by all such programs. Exhaust context subsets in increasing cardinality and freeze the lexicographically first minimum basis `C*` whose induced partition equals `P_full`.

Only after `C*` and its quotient are frozen are action labels exposed for policy synthesis.

## Required gates

1. semantic context-role names absent;
2. context programs synthesized from the low-level grammar;
3. context induction uses neither action labels nor hidden types;
4. finite CompleteCover reaches a minimum context basis;
5. induced quotient equals the full observational quotient;
6. hidden semantic-type agreement passes audit-only;
7. deleting any selected context breaks the policy-relevant quotient;
8. leave-one-positive-mechanism-out action transfer is 100%;
9. every held-out action is independently CompleteCover-verified;
10. alpha-renaming does not alter quotient identity;
11. deterministic shuffled verifier outcomes destroy hidden-type reflection;
12. hostile causal and preservation controls are rejected.

## Evidentiary boundary

A pass establishes finite verifier-driven discovery of a context basis from a supplied low-level observation/interaction language. It does **not** establish discovery of the raw-domain adequacy map, discovery of the primitive observation interface itself, or unrestricted natural-domain context formation.
