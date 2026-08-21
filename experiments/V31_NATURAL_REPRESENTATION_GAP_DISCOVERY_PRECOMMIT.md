# V31 — Natural Representation-Gap Discovery

## Frozen question
Can the V30 developmental runtime, on natural SAIR Stage-2 cells, prove that its entire initial epistemic representation is non-separating, respond by synthesizing a previously absent typed probe from lower-level constructors, use the verifier-backed observation to make a lawful continuation reachable, and lose that reachability again under representation ablation?

This is the direct separator against coverage-guided exploration inside a fixed probe language.

## Starting point
V31 starts from the V30 developmental runtime and V28 exact SAIR model-query machinery.

Natural data: official public SAIR Stage-2 `normal`, `hard1`, `hard2`, with `hard3` held out for transfer audit.

Protected TRUE/FALSE answers MUST NOT enter representation synthesis, candidate ranking, routing, state update, or the primary gate. V31 uses only exact order-2 observations and independently rechecked bounded model-existence queries.

## Initial epistemic representation R0
R0 contains exactly two atomic probes:

- `MODEL_EXISTS(ORDER2,FORWARD)`
- `MODEL_EXISTS(ORDER2,REVERSE)`

The strongest fixed-language baseline is not a sampler. It receives the complete Boolean closure of those two observations: all 16 Boolean functions on the two old probe bits. If none separates an obstructed natural cell, then no amount of additional sampling or coverage allocation inside that extensional old representation can help.

## Low-level constructor alphabet
The developmental arm is not given an order-3 probe name. It receives only the typed constructors:

- constant `ORDER2 : Order`
- unary constructor `SUCC : Order -> Order`
- probe constructor `MODEL_EXISTS : Order x Direction -> Bool`
- directions `FORWARD`, `REVERSE`

The bounded synthesis grammar permits at most one `SUCC` application. Thus the runtime may construct `SUCC(ORDER2)` compositionally, but no high-level order-3 probe is supplied as an initial capability.

## Residual and synthesis rule
A natural base cell is representation-obstructed when verifier-derived lawful continuations disagree inside the cell while every function in the complete old Boolean closure is constant on that cell.

When R0 is proven non-separating, the registered synthesis routine enumerates all well-typed probe programs in the frozen constructor grammar that are absent from R0. Candidate ranking is label-free: maximize the number of representation-obstructed training cells that the exact verifier observation nontrivially partitions, then minimize syntax cost, then lexical AST order.

No SAIR TRUE/FALSE answer may be read for this ranking.

## Downstream lawful continuations
For an exact synthesized model-existence probe:

- outcome `1` licenses `ACCEPT_COUNTERMODEL_WITNESS` only with an independently rechecked finite-model witness;
- outcome `0` licenses `ADVANCE_PROOF_SEARCH_FRONTIER` as a nonterminal successor when bounded countermodel search is exhausted.

The continuation must be recomputed by the generic runtime after the observation. It is not supplied to the synthesis routine.

## Arms

1. **FIXED-COVERAGE R0** — complete extensional Boolean closure of the original probe language; no representation growth.
2. **DEVELOPMENTAL R1** — same initial state, but the generic runtime may invoke the typed constructor synthesizer after proving R0 non-separating.
3. **NO-SUCC ABLATION** — remove the only constructor that can create a new `Order` object beyond `ORDER2`.
4. **NEW-PROBE ABLATION** — synthesize normally, then remove the synthesized probe before observation and reroute.
5. **HARD3 TRANSFER AUDIT** — freeze the selected synthesized AST from training and measure whether it partitions previously unseen obstructed hard3 cells; no refitting.

## Primary gates

G0. Official natural SAIR rows are used and all bounded SAT witnesses used by V31 are independently rechecked.

G1. At least one natural training cell has incompatible verifier-derived lawful continuations under R0.

G2. Exhaustive complete old-representation closure is non-separating on every primary obstructed cell.

G3. The developmental runtime routes to representation/probe development before the new probe exists.

G4. The registered synthesizer constructs a well-typed probe AST absent from R0 using `SUCC` compositionally; no high-level order-3 probe is supplied to the initial state.

G5. Candidate selection is answer-label-free and based only on verifier-observable structural partition value plus frozen cost/tie-breaking.

G6. After installation, the generic runtime routes to `PROBE`, exact observation is certificate-backed, and recomputation yields a lawful continuation.

G7. At least one executed branch performs a lawful nonterminal successor transition and obtains a fresh residual/route from the changed state.

G8. Fixed-coverage R0 remains obstructed even when granted its entire extensional closure, while R1 closes at least one such cell.

G9. Removing `SUCC` prevents synthesis and restores the original representation obstruction.

G10. Removing the synthesized probe after synthesis but before observation restores the original obstruction.

G11. The synthesized probe partitions at least one previously unseen representation-obstructed hard3 cell without refitting. This is a transfer audit, not a requirement that all hard3 cells close.

G12. Protected SAIR TRUE/FALSE answers are absent from synthesis, ranking, routing, state update, and gate computation.

`V31_NATURAL_REPRESENTATION_GAP_DISCOVERY_GATE` passes iff G0–G12 pass.

## Claim boundary
A pass establishes a bounded natural representation-gap result: exhaustive search/coverage inside the initial extensional probe representation is provably non-separating on natural SAIR cells, while verifier-guided development composes a previously absent probe from lower-level typed constructors, makes a lawful continuation reachable, and loses the gain under constructor/probe ablation.

It does **not** establish unrestricted meta-language invention, arbitrary scientific instrument invention, theorem-language expansion, full SAIR solving, or long-horizon autonomous science. `SUCC`, `MODEL_EXISTS`, the verifier, and the synthesis depth bound remain supplied primitives.