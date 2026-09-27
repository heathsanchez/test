# V24 — Raw Natural-Domain Adequacy Discovery

## Scientific target

V23 closed the synthetic context-discovery scaffold but still received a designed anonymous observation-port interface. V24 attacks that remaining adequacy scaffold directly.

The target pipeline is:

```
RawTrace_D -> learned adequacy map A_D -> synthesized contexts C*_D
           -> verifier-induced quotient Q_D -> frozen policy -> verified action
```

No manually authored developmental feature vector, obstruction-role label, witness type, context-role label, or domain identifier may be supplied to the learner.

## Natural source requirement

The evidentiary run must ingest native artifacts from genuinely different existing sources, not hand-distilled V17-style episodes. Initial public sources are:

- ARC: `heathsanchez/test@arc-v12-frame-development-operator`
- SAIR/equational: `heathsanchez/mathgraph@main`
- Lean/kernel: `heathsanchez/lean-kernel-arena@master`
- Program/runtime: `heathsanchez/test@main` RGRS/runtime artifacts where eligible

A source does **not** count as a natural raw-trace domain merely because code or a README exists. The audit must find machine-readable native episode/attempt/result records with intervention/verifier consequences sufficient to test substitutability. If fewer than three genuinely eligible domains exist in the checked-out sources, V24 must emit `INSUFFICIENT_NATURAL_RAW_TRACE_DOMAINS` and the scientific gate is false. No synthetic replacement is permitted in the same evidentiary run.

## Generic trace language

The learner receives raw JSON/JSONL/tree values and a domain-agnostic primitive observation DSL only:

- node type / arity / list length
- primitive scalar equality and order comparisons
- parent/child and sibling relations
- before/after value relation when a raw record itself supplies paired states
- repeated-key incidence inside a record
- exact verifier outcomes present in the native record

Field names and repository/domain names are excluded from learned features. They may be retained only in audit provenance.

## Adequacy condition

For a learned encoding `A_D`, merging two raw histories is lawful only if the learned context basis cannot distinguish their verified intervention consequences:

```
A_D(t1) = A_D(t2)
  => for every synthesized context c in C*_D,
     V(c[t1]) = V(c[t2]).
```

The encoding is selected by verifier-relative substitutability, not action-label prediction.

## Frozen split

If at least three eligible domains exist, run leave-one-real-domain-out. Adequacy/context/type induction on the held-out domain must not use its developmental action labels. Domain identity is unavailable to the policy learner.

## Required gates

1. `native_raw_artifacts_not_hand_distilled`
2. `at_least_three_eligible_real_domains`
3. `no_manual_developmental_feature_map`
4. `field_and_domain_names_absent_from_learner`
5. `adequacy_induced_by_verifier_substitutability`
6. `heldout_domain_action_transfer_100pct`
7. `all_heldout_actions_independently_verified`
8. `adequacy_ablation_breaks_transfer`
9. `shuffled_verifier_breaks_structure`
10. `causal_capability_gain_on_heldout_domain`

The umbrella `RAW_NATURAL_ADEQUACY_GATE` is true only if every required gate is true.

## Strong causal criterion

A held-out success requires more than action prediction:

```
T notin Phi(F)
T in Phi(F + Theta)
T notin Phi(F + Theta - learned_development)
```

If the native sources do not expose enough information to establish this, the result remains an explicit boundary failure rather than being inferred from a summary label.

## Next step only after V24 passes

The subsequent experiment removes resets and tests persistent cross-domain developmental history under a frozen model. V24 itself does not claim long-horizon development.
