# Local Transition Warrant and Constraint-Cycle Closure V38 — Frozen Protocol

## Question

Can stabilization become local and compositional?

V37 established that consequence can force a residual state to exist before there is enough evidence to warrant that state's complete recurrent law.

V38 asks a sharper question:

> Can individual outgoing transitions become warranted independently, can those locally warranted transitions close into a recurrent constraint cycle before every state is fully stabilized, and can the remaining transition obligations then be completed without revising already warranted structure?

## Frozen substrate

To isolate transition-level warrant, V38 works directly on an anonymous ordered binary encounter stream.

The kernel receives a finite prefix-closed set of encounter histories with externally verified consequence labels.

It is not told:

- hidden state identities;
- which histories realize the same state;
- which transition is being tested;
- any target graph;
- any cycle;
- any stage number;
- any semantic family name.

The binary alphabet and order remain supplied priors.

## Residual state identity

For a candidate future horizon h and any prefix p for which the complete h-neighborhood is authoritative, define

    R_h(p) = ( C(p ++ s) ) for every binary suffix s of length <= h.

Two supported histories occupy the same residual state exactly when these vectors agree.

The kernel searches h from 0 upward.

A horizon is admissible only when every transition that is locally supportable is deterministic: if two supported representatives have the same residual signature, then whenever both have an h-supported successor under symbol a, those successors must have the same residual signature.

The minimum admissible horizon is retained.

## Local transition warrant

For a discovered residual state q and symbol a:

- WARRANTED(q,a) iff at least one representative p of q has an authoritative h-neighborhood for p++a, and all such supported representatives agree on the successor residual state.
- UNRESOLVED(q,a) iff no representative has enough future authority to identify the successor residual state.

A transition is never invented merely to make the graph total.

A state is locally STABLE iff all of its outgoing transitions are warranted.

The whole recurrent machine is STABLE iff every discovered state's outgoing transitions are warranted.

## Constraint-cycle closure

Independently of whole-machine stability, the kernel analyzes the graph containing only warranted transitions.

A warranted cycle is a directed cycle among discovered residual states using only warranted edges.

A spanning warranted cycle is a warranted cycle that visits every discovered residual state at least once.

Thus a recurrent constraint cycle can become certified before all alternative outgoing transitions are known.

The cycle claim is purely graph-theoretic and does not imply that the whole machine is already executable on arbitrary future streams.

## Monotone retention

Across staged authority expansions, post-freeze evaluation may compare results.

A previously warranted transition is required to retain the same source residual signature, symbol, and target residual signature when more authority is added.

New evidence may:

- warrant previously unresolved edges;
- make a state locally stable;
- close a warranted cycle;
- stabilize the whole recurrent machine.

It may not silently rewrite a previously warranted edge without failing the comparison.

## Post-freeze challenge family

The hidden evaluator may supply multiple unknown finite recurrent systems using staged prefix-closed authority.

Primary families may include:

- a three-state system whose consequence signatures require horizon 1;
- a four-state system whose consequence signatures also require horizon 1;
- stages that first expose a chain of warranted transitions;
- a later stage that closes a spanning cycle while some alternative edges remain unresolved;
- later stages that stabilize states one by one;
- a final stage that stabilizes the complete recurrent machine;
- binary-symbol relabelling controls.

The hidden target machines and authority schedules are committed only after the scientific core is frozen.

## Frozen gates

L1. Frozen scientific core remains byte-identical after hidden systems are committed.
L2. The minimum admissible residual horizon is discovered without hidden state labels.
L3. The first stage contains multiple warranted transitions and multiple unresolved transitions.
L4. The first stage does not falsely claim a spanning warranted cycle.
L5. Adding one local authority region closes a spanning warranted cycle without stabilizing the whole machine.
L6. Every edge warranted before cycle closure is retained unchanged after closure.
L7. At cycle closure, at least one state is still locally unstable.
L8. Later authority stabilizes individual states without revising the already closed cycle.
L9. Whole-machine stability occurs only when every discovered state's outgoing transitions are warranted.
L10. The final stable machine exactly replays held-out histories beyond the authority used to construct it.
L11. A second hidden recurrent family exhibits the same chain -> cycle closure -> local stabilization -> whole stabilization ordering.
L12. The second family has a different number of residual states from the first.
L13. Binary symbol relabelling preserves residual-state count, local-warrant counts, closure stage, and canonical structure.
L14. Previously warranted edges are monotone under every staged authority expansion.
L15. No unresolved edge is treated as executable in partial stages.
L16. Prefix-authority corruption that is not prefix-closed remains UNKNOWN_AUTHORITY.
L17. Verifier ablation authorizes no residual or transition construction.
L18. The frozen kernel contains no hidden family name, target cycle, state label, or staged prefix schedule.
L19. Spanning-cycle closure is certified strictly before whole-machine stability in at least two hidden families.
L20. Local state stabilization occurs strictly between spanning-cycle closure and whole-machine stabilization in at least two hidden families.

## Claim boundary

A pass would establish only:

> within this finite residual-machine substrate, transition obligations can be warranted independently and composed monotonically; a recurrent cycle of mutually supporting transitions can become verified before the entire state-transition law is known.

This is not yet biological constraint closure, thermodynamic self-construction, or unrestricted compositional learning.

It would, however, experimentally separate:

    state genesis
    transition warrant
    cycle closure
    local stabilization
    whole-machine stabilization

as distinct developmental events.
