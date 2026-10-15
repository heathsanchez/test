# V18 — Developmental Identity Reflection — frozen precommit

Residual inherited from V17:

`DEVELOPMENTAL_SEMANTICS_DOES_NOT_REFLECT_DEPENDENCY_GEOMETRY`

## Question

Can a minimal subset of verifier-visible semantic relation families identify the frozen StrCC-style developmental dependency class without being given the dependency graph itself?

## Hidden target

For each episode the evaluator holds a typed developmental dependency graph. Surface/domain identifiers are excluded from graph identity. Equality means equality of the abstract typed dependency graph used by this finite benchmark.

## Visible relation families

The learner may use only:

1. `COVER` — bounded CompleteCover attempted/witness/local-candidate observations.
2. `CAUSAL` — post-intervention closure and local-ablation restoration.
3. `PRESERVE` — protected old behavior/certificates preserved.
4. `RETENTION` — verified construction later retained/reused.

The dependency graph, graph edges, quotient key, intervention label, and domain name are not candidate coordinates in basis synthesis.

## Corpus

Six manually distilled historical episodes:

- FWL constructor synthesis;
- RC2 active-verifier ontology extension;
- MI V8 external-stream primitive expansion;
- BugsInPy V10 new-primitive synthesis;
- ARC V12 same-frame CompleteCover repair;
- Lean-kernel same-frame candidate/retention path.

Three hostile counterfactual controls are added so CompleteCover status alone cannot define identity: noncausal intervention, preservation failure, and retention/reuse dependence.

## Exact search

Exhaust all nonempty subsets of the four visible relation families in increasing cardinality. Choose the lexicographically first minimum subset whose equality partition is exactly the hidden quotient partition over the frozen corpus.

## Gates

A pass requires all of:

- a reflecting basis exists;
- pairwise soundness + reflection on the full finite corpus;
- leave-one-episode-out equivalence decisions are exact against every remaining episode;
- deleting any selected relation family breaks exact reflection;
- FWL and RC2 are identified as the same developmental class;
- ARC V12 and Lean kernel are not falsely collapsed;
- a separately synthesized tiny action rule from the learned basis transfers correctly leave-one-episode-out.

## Boundary

This is a finite identification experiment over manually authored adequacy encodings and relation families. It does not prove automatic adequacy discovery, unrestricted graph reconstruction, or natural-domain universality. A pass would establish only that the declared verifier-visible semantics is sufficient and minimal for the frozen finite developmental quotient corpus.
