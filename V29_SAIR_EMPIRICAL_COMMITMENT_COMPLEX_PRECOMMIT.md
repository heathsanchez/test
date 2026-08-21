# V29 — SAIR empirical multi-action commitment complex

## Frozen question
Does the V26 commitment router remain meaningful on a natural SAIR subset when lawful commitments are empirical solver portfolios, not TRUE/FALSE singleton labels?

## Frozen corpus
Use the official `SAIRcompetition/equational-theories-lean-stage2` public development distributions (`normal`, `hard1`, `hard2`). Select 160 rows by lexicographic SHA256(problem id), independent of the public answer.

## Empirical terminal route atoms
For every selected problem run, under frozen budgets:
- `CE2`: exact exhaustive order-2 forward countermodel search.
- `CE3`: exact Z3 order-3 forward countermodel search, independently rechecking every SAT table.
- `VP_DEF`: Vampire default theorem search, 1 second.
- `VP_CASC`: Vampire CASC theorem search, 1 second.

The public answer is protected audit information: it is never used to construct route outcomes, but any countermodel on a TRUE row or Vampire theorem on a FALSE row fails the soundness audit.

## Commitment/action carrier
A commitment is a fixed terminal solver portfolio:
- `A0 = CE2 OR VP_DEF`
- `A1 = CE3 OR VP_DEF`
- `A2 = CE2 OR VP_CASC`
- `A3 = CE3 OR VP_CASC`

The same action may therefore be lawful on TRUE and FALSE worlds. For world H,

`A*(H) = {Ai : portfolio Ai terminates successfully on H}`.

If no Ai succeeds, add bounded terminal commitment `OBSTRUCT_B`, meaning only that no action in the declared frozen carrier succeeded under its budget.

## Observation / probe boundary
Cheap observational cells are the exact Fin-2 verifier signature `v0..v5` used in V27. Candidate epistemic probes are answer-blind order-3 forward and reverse model-existence bits, cost 3 each. Cheap order-2 bits remain redundant controls.

## Router
For each Fin-2 cell E compute `A(E)=intersection_H A*(H)`. If nonempty, no epistemic split is required. If empty, exhaustively compute minimum worst-case probe cost J(E) over the declared probe carrier. A finite tree is accepted only if every reachable leaf has nonempty empirical common-action intersection.

## Primary gates
1. sample selection answer-blind;
2. every order-3 SAT witness independently rechecked;
3. no protected-answer contradiction from route atoms;
4. at least one problem has more than one lawful portfolio action;
5. at least one mixed TRUE/FALSE Fin-2 cell is already commitment-coherent, establishing that commitment coherence is not label purity; if absent, report this as a falsification rather than patching;
6. at least one action-incoherent Fin-2 cell exists;
7. router search exhaustive over declared probes;
8. if finite positive-J cells exist, every leaf is recomputed to have nonempty common-action intersection and used-probe ablation is audited;
9. shuffled order-3 probes are an audit only;
10. no gate requires Fin-3 or Vampire to win.

## Claim boundary
A pass establishes only a finite natural-corpus instance of commitment routing over empirically observed solver portfolios. It does not establish complete solver coverage, final SAIR generalization, probe-DSL invention, or unrestricted WorldCover.
