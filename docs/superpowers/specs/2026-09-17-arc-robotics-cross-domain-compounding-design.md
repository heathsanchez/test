# ARC → Robotics Cross-Domain Compounding V1 Design

## Goal

Test whether a capability discovered in a passive ARC-like domain can causally reduce search or interaction cost in a structurally related active world, without transferring task answers, hidden-world parameters, or hand-labeled domain semantics.

## Scientific question

Can a domain-independent developmental mechanism retain an abstraction/operator from sparse ARC-style examples and reuse it to identify or control a previously unseen active world more cheaply?

The experiment is a finite causal probe, not a claim about general ARC solving, physical robotics, or universal transfer.

## Core structure

Two domains share only an abstract latent relational law. They differ in observation and action vocabulary.

1. **Source / ARC-like domain:** small symbolic grids encode hidden object relations. The learner sees input/output examples and searches a frozen library of generic relational operators for a minimal operator that explains the source examples.
2. **Target / embodied finite domain:** a hidden world exposes observations only through allowed interventions. The learner must identify the consequence-relevant regime and choose the correct terminal action.

The retained source capability is not a source answer. It is a generic operator/schema that can be instantiated over the target domain's primitive observations after a separately defined adapter test confirms extensional compatibility on calibration cases.

## Arms

- `COLD`: no retained source capability; search the full frozen target operator library.
- `WARM`: source-derived capability is available at unit lookup cost after compatibility calibration.
- `SHAM`: same-sized retained memory containing an irrelevant operator; target must fall back to cold search.
- `ABLATION`: source-derived capability is removed before the target phase; expected to recover cold cost.
- `RESTART`: serialize only the retained capability, discard derived target decoder/cache, reload, and solve the target again.

All arms receive the same target observations, action budget, operator library, and verifier.

## Hidden-world protocol

Training/source worlds and calibration worlds are fixed before the target trial. Target worlds are generated deterministically from a seed that includes the executing commit SHA and GitHub run ID when available, so concrete target instances are chosen only after the tested commit exists.

No target answer or hidden parameter may affect capability selection before the target phase.

## Metrics

Primary endpoint: mean target developmental cost, defined as `operator evaluations + paid interventions`.

Secondary endpoints:

- paid target interventions
- operator evaluations
- exact target-task accuracy
- `UNKNOWN` count
- restart recovery cost
- compatibility-calibration cost

## Frozen primary prediction

`WARM` must be strictly cheaper than `COLD`, `SHAM`, and `ABLATION` while matching their target-task correctness. `RESTART` must preserve the warm advantage without access to the discarded derived decoder.

## Causal interpretation

A positive result requires all of the following:

1. WARM has lower target developmental cost than COLD.
2. SHAM does not reproduce the gain.
3. Exact ABLATION removes the gain.
4. RESTART reconstructs the useful target path from the retained capability.
5. All successful arms are exact on the sealed finite target set.

If these conditions hold, the justified claim is narrow: a retained cross-domain operator causally reduces later finite development cost under the declared adapter and world family.

## Non-claims

This experiment does not establish:

- general ARC-AGI performance,
- transfer from real ARC tasks to real robots,
- ontology invention without a frozen candidate grammar,
- sim-to-real robustness,
- physical safety,
- universal representation learning.

## Implementation boundary

The first version is dependency-free Python and intentionally does not use MuJoCo. Physics is promoted only if the finite separator establishes causal cross-domain reuse. This keeps the first test cheap, exact, reproducible, and falsifiable.

## Files

- `experiments/arc_robotics_cross_domain_v1/core.py`: worlds, operators, source discovery, target solving, serialization.
- `experiments/arc_robotics_cross_domain_v1/test_core.py`: unit and causal-control tests.
- `experiments/arc_robotics_cross_domain_v1/run.py`: sealed experiment runner.
- `experiments/arc_robotics_cross_domain_v1/score.py`: arm aggregation and frozen verdict.
- `experiments/arc_robotics_cross_domain_v1/validate.py`: leakage and artifact checks.
- `experiments/arc_robotics_cross_domain_v1/PRECOMMIT.md`: frozen hypothesis and interpretation.
- `.github/workflows/arc-robotics-cross-domain-v1.yml`: CI execution and evidence upload.
