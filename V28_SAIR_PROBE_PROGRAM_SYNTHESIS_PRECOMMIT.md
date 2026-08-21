# V28 — SAIR Natural Probe-Program Synthesis

## Purpose

Test the next scaffold left by V27. V27 optimizes over four manually enumerated probes. V28 removes those probe IDs and gives the controller only a tiny low-level experiment-program grammar. The controller must synthesize a minimum-cost verifier probe program that resolves a natural decision-relevant observational collision.

This is an **E2 epistemic-development** claim: probe programs are synthesized inside a supplied primitive experiment DSL. It is **not** probe-DSL invention (E3/E4), unrestricted experimentalization, or a capability-language invention claim.

## Frozen natural setting

- External corpus: public SAIR Stage-2 repository.
- Development rows: `normal + hard1 + hard2`.
- `hard3`: secondary transfer audit only; it is not used to select the probe grammar or costs.
- Cheap observation quotient: the exact Fin-2 behavior already frozen in V24.
- Lawful audit commitments: `PROOF` for public TRUE rows, `COUNTERMODEL` for public FALSE rows. These labels define whether a development cell is commitment-coherent; they are not available to the verifier probe itself.

## Supplied primitive experiment DSL

The learner is **not** given names such as `Fin3`, `order3_forward`, or `p2`.

Primitive constructors are:

- `ORDER2`: integer-valued base experimental scale.
- `SUCC(order)`: increase experimental scale by one. Maximum synthesis depth is one successor.
- `FORWARD`, `REVERSE`: orientation tokens.
- `MODEL_EXISTS(order, orientation)`: exact bounded countermodel-existence query.
- `PAIR(q1,q2)`: execute two atomic queries and return the outcome pair.

The finite synthesized program carrier is generated compositionally from these constructors. Costs are frozen as:

- atomic `MODEL_EXISTS(n,dir)`: `max(1, n-1)`;
- `PAIR`: sum of child costs plus one.

Thus order-2 atomic programs cost 1, order-3 atomic programs cost 2, and the two-order-3 pair costs 5. The exact values are arbitrary but frozen before execution; the important test is minimum-cost decision-changing synthesis under this declared carrier.

## Old vs expanded epistemic language

- Old probe closure: programs constructible **without** `SUCC`.
- Expanded probe closure: programs constructible with at most one `SUCC`.

For every Fin-2 observational cell containing multiple lawful commitments, V28 computes exact adaptive epistemic distance `J(E)` over the old and expanded synthesized carriers.

## Primary gates

1. Real external SAIR rows are used.
2. At least one Fin-2 observational cell is decision-incoherent.
3. CompleteCover of the old no-`SUCC` probe closure gives `J(E)=infinity` for at least one such cell.
4. The expanded grammar synthesizes a finite-cost probe program for at least one previously obstructed cell.
5. The selected program is minimum-cost under exhaustive search of the declared synthesized carrier.
6. Every SAT countermodel witness returned by synthesized order-3 queries is independently re-evaluated.
7. The synthesized probe creates commitment-coherent verifier leaves.
8. Removing every probe program used by the optimal tree restores either impossibility or strictly larger epistemic cost for at least one resolved cell.
9. Cheap old-language programs are explicitly nonseparating inside the Fin-2 quotient cells.
10. A more expensive `PAIR` program must not be selected when an atomic synthesized probe already achieves the same deciding refinement.
11. A within-split shuffled-verifier control is reported, never shuffled across development/hard3.

## Interpretation

PASS supports:

`natural epistemic collision -> CompleteCover(old probe language) -> probe-language obstruction -> compositional probe-program synthesis -> verified quotient split -> lawful downstream commitment`.

It does **not** support:

- invention of the primitive probe DSL itself;
- unrestricted raw-domain experimentalization;
- proof/countermodel construction beyond the existing SAIR verifier machinery;
- uncontaminated hard3 generalization.

The next residual after PASS is probe-language invention: can the system construct or transform the primitive experimental interface itself rather than synthesize a program inside this frozen DSL?
