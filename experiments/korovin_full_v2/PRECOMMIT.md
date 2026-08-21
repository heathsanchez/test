# Korovin Object Reinvention FULL V2 — Frozen Protocol

## Question

Can a developmental representation-search system recover a useful familiar mathematical object from restricted knowledge **without being given that object's name, axioms, target order, or a preselected behavioral-equivalence representation**?

This is a constrained re-invention test, not a claim of historically novel mathematics.

## Blind-constructor boundary

`constructor.py` may use only:

- opaque token sequences;
- exact input/output observations supplied by the world;
- generic syntactic features;
- generic point probes;
- a generic feature-combination/state-registry mechanism;
- residuals measuring predictive and transition inconsistency.

The blind constructor must not contain target-specific mathematical vocabulary or known object names. CI scans it.

The constructor is not told which feature family should win. It searches syntax features and observable probes under one frozen score:

1. minimize predictive + transition conflicts;
2. then minimize represented state count;
3. then description cost.

It expands feature width only while the current representation leaves residual conflicts.

## Independent verifier

`verifier.py` is separated from the constructor. Only after a representation is frozen may it test closure, identity, associativity, invertibility, commutativity, and element-order fingerprints.

Those laws cannot influence the representation search.

## Frozen worlds

- source: opaque 4-point transformation system;
- transfer: independent opaque 3-point transformation system;
- negative control: includes a non-invertible transformation;
- order-transfer controls: opaque cyclic systems of orders 3, 5, 7;
- four relabeling controls: source world with independently permuted point labels and token names.

Human mathematical names for the latent systems are excluded from constructor input.

## Holdout

Training syntax lengths: 0..9.
Protected test syntax lengths: 10..13.

Exact-string memory is the frozen baseline.

## Causal ablations

1. Remove each selected observable probe from the frozen representation and require predictive/transition damage.
2. Remove the entire observable-probe feature family and rerun the same search budget. No zero-conflict representation may remain.
3. Negative control must still support perfect downstream prediction while the independent verifier rejects the group-axiom bundle.

## Gates

- G0 constructor target vocabulary absent.
- G1 source syntax baseline = 0 on protected syntax.
- G2 source protected accuracy = 1.0.
- G3 every selected probe causally necessary in the frozen representation.
- G4 observable-behavior feature family necessary.
- G5 source independently satisfies group axioms.
- G6 transfer protected accuracy = 1.0.
- G7 transfer independently satisfies group axioms.
- G8 negative control predicts perfectly but fails group axioms.
- G9 orders 3, 5, 7 transfer perfectly and satisfy group axioms.
- G10 relabeling robustness.
- G11 >10x compression in every tested world.

No gate may be changed after the first evidentiary run.
