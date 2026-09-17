# ARC → Robotics Developmental Transfer V1 — Design

## Objective

Test whether a developmental operator acquired in an ARC-like interactive setting transfers causally into a structurally different active world, reducing the cost of discovering a sufficient representation without transferring source-domain labels, truth tables, target features, or target answers.

## Transferred object

The only retained cross-domain capability is the meta-operator:

> When states that are equivalent under the current representation produce incompatible verified consequences, treat the collision as evidence that the representation is insufficient; choose an allowed intervention that maximally separates the surviving latent explanations; retain the smallest new behavioural distinction needed to restore predictive consistency.

The retained capability contains no target-domain ontology and no target-specific separator.

## Phase A: source acquisition

Construct an ARC-like active environment in which an initially sufficient-looking representation eventually produces a verified predictive collision. A cold developmental learner must discover the residual → separator → representation-split procedure from source episodes. The acquired operator is serialized as a domain-independent capability and all source-derived transient state is discarded.

The source environment must not use the same latent variable, observation encoding, action semantics, or target rule as Phase B.

## Phase B: prospective active-world transfer

Generate target worlds only after the source capability and scorer are frozen. The target is a lightweight physics-like environment with observable position/motion and a hidden interaction regime. Two target states are deliberately aliased under the initial representation but respond differently to interventions. The system is not told the hidden regime or which intervention reveals it.

A successful learner must detect a predictive collision, identify an informative allowed intervention, introduce a behavioural distinction, and then use that distinction to select the correct terminal controller/action on untouched target worlds.

## Arms

- `COLD`: no developmental operator retained; searches the frozen developmental strategy family from scratch.
- `WARM`: receives only the serialized source-acquired developmental operator.
- `RESTART`: serializes the retained operator, destroys all derived state, reloads it, then follows the warm protocol.
- `SHAM`: receives an equally sized irrelevant developmental operator that does not prescribe collision-driven active separation; it must not reproduce the warm advantage.
- `ABLATION`: exact deletion of the causal residual→separator→split dependency before target development; otherwise identical resources.

All arms face identical sealed target worlds and execution probes. Paid developmental interventions and search/evaluation work are counted separately from final execution observations.

## Primary hypothesis

All correctness conditions must hold, and:

1. `WARM developmental_cost < COLD developmental_cost`;
2. `WARM developmental_cost < SHAM developmental_cost`;
3. `WARM developmental_cost < ABLATION developmental_cost`;
4. `RESTART developmental_cost == WARM developmental_cost` within exact deterministic Phase-A semantics;
5. removing the claimed dependency restores the cold developmental frontier;
6. the warm gain must arise before target answers are revealed and may not depend on target-specific information retained from Phase A.

No fixed numeric speedup is predeclared; the scorer freezes ordering and causal requirements rather than tuning to an observed magnitude.

## Leakage controls

- Target seeds derive from frozen code/provenance after the source operator is fixed.
- No target hidden-state labels are exposed to any learner.
- The source and target latent mechanisms are intentionally different.
- The transferred artifact is inspected and hashed.
- SHAM matches the transfer channel/type and approximate representation size.
- ABLATION removes the exact claimed developmental dependency rather than reducing generic compute.
- RESTART demonstrates that the gain resides in retained capability rather than process-local state.

## Phase-C promotion

MuJoCo is not part of the primary Phase-B claim. Phase C is launched only if Phase B passes the frozen causal gate. The same serialized developmental operator and the same arm semantics are then adapted to a MuJoCo environment in which a visually/kinematically aliased object interaction differs because of a hidden physical property such as friction or actuator response.

The MuJoCo experiment must preserve the epistemic boundary: the learner receives observations and allowed interventions, never simulator ground-truth physical parameters.

A Phase-C failure does not invalidate Phase B; it names the sim/representation obstruction that prevents promotion.

## Interpretation boundary

A Phase-B pass establishes finite causal transfer of a developmental procedure across two deliberately different domains. It does not establish general ARC solving, general robotics intelligence, physical-world safety, or sim-to-real transfer. A Phase-C pass would establish the same causal pattern in MuJoCo simulation only.