# V26 — Commitment Router Mathematical Specification

## Status

Frozen mathematical/property-suite precommit before any new SAIR adaptation.

## Central objects

Let `H` be a finite WorldCover-bounded surviving hypothesis set and let `A*(h)` be the set of verifier-admissible commitments in world `h`, independent of current realizability.

Define the common lawful commitment set

`A(E) = ⋂_{h in E} A*(h)`.

Define the viable-commitment complex

`C = { E subset H : A(E) != empty }`.

For an action theta, define its lawful-world region

`S_theta = { h : theta in A*(h) }`.

The core equivalence under test is

`E in C  iff  exists theta, E subset S_theta`.

A current capability closure `Cl(Omega)` is kept logically separate from admissibility. If `A(E)` is nonempty but `A(E) ∩ Cl(Omega)` is empty, the residual is capability-side rather than epistemic.

## Epistemic distance

For pure probes p with cost c(p), outcome cells `E_y`, and a fixed finite probe carrier P, define worst-case epistemic distance recursively:

- `J(E)=0` if `A(E)` is nonempty.
- otherwise `J(E)=min_p [c(p)+max_y J(E_y)]`, where probes making no strict refinement are ignored.
- if no finite strategy reaches coherent leaves, `J(E)=infinity`.

Thus:

- `A(E) ∩ Cl(Omega) != empty` => ACT.
- `A(E) != empty` and `A(E) ∩ Cl(Omega) = empty` => DEVELOP CAPABILITY.
- `A(E) = empty` and `J(E) < infinity` => PROBE using an optimal adaptive experiment policy.
- `A(E) = empty` and `J(E) = infinity` => DEVELOP PROBE LANGUAGE.
- an observed verifier outcome with `E_y = empty` => DEVELOP WORLD/HYPOTHESIS LANGUAGE.

Terminal certificates such as `OBSTRUCT_B` are ordinary admissible commitments when justified.

## Frozen 14-test suite

1. Commitment-complex theorem: exhaustive 3-world x 3-action enumeration.
2. JOIN-MANY adversary: pairwise coherence but global incoherence.
3. Nonunique maximal safe quotient/compression.
4. Sequential-probe adversary: no one-step deciding probe but finite adaptive strategy.
5. Probe-language obstruction: `J(E)=infinity` under CompleteCover of the supplied probe carrier.
6. Entropy adversary: maximum information-gain probe may fail to restore commitment while lower-entropy probe succeeds.
7. Adaptive-cost adversary: adaptive experiment tree strictly cheaper than best fixed nonadaptive probe bundle.
8. Terminal certificate case: common `OBSTRUCT_B` stops unnecessary probing.
9. World-model surprise: verifier outcome inconsistent with every current world yields an empty posterior cell.
10. Capability-only obstruction: commitment is identifiable but absent from current capability closure.
11. Probe monotonicity: adding probes cannot increase optimal epistemic cost (random stress).
12. Action monotonicity: enlarging lawful action sets cannot make a coherent cell incoherent (random stress).
13. Probe ablation: remove a necessary probe and resolution becomes impossible.
14. Capability ablation: remove the realizable action; epistemic coherence remains while realizability disappears.

No SAIR labels, Fin-3 choice, or natural-domain outcomes may be used to alter these tests after the branch is created.
