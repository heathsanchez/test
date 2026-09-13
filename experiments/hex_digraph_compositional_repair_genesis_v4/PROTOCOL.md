# Hex Digraph Compositional Repair Genesis V4 — Frozen Protocol

## Question

After an exhaustive residual certifies the current adapter substrate inadequate, can the successful substrate repair be composed from smaller generic growth primitives rather than supplied as a named repair?

V3 supplied four named growth constructors. V4 removes those named repairs.

## Frozen starting point

The complete one- and two-role substrate is first exhausted exactly as in V3. No candidate may qualify.

From the failed two-role family, choose the canonical least-residual state by:

1. lowest semantic disagreement count;
2. fewer identity couplings;
3. lexicographic arc channel;
4. lexicographic coupling list.

No three-role state is available initially.

## Generic growth primitives

Only three generic primitives are supplied:

- `ADD_FRESH_ROLE`: extend a two-role state with one anonymous third role;
- `COUPLE_OLD0_TO_FRESH`: add an identity coupling from old role 0 to the fresh role;
- `COUPLE_OLD1_TO_FRESH`: add an identity coupling from old role 1 to the fresh role.

The coupling primitives are invalid until the fresh role exists. Duplicate applications are inert and are not retained as new states.

No primitive represents the full successful adapter.

## Search

Breadth-first enumerate primitive programs up to depth 3.

At each depth:

- execute all syntactically valid programs;
- deduplicate equal resulting adapter states;
- exhaustively evaluate every new state over all 4,096 ordered pairs of the 64 loopless directed graphs on 3 vertices.

Stop only after the complete first successful depth is evaluated.

Canonical selection among equal-depth successes is lexical by primitive-program tuple.

## Pass

A pass requires:

- initial one/two-role substrate exhaustively inadequate;
- canonical least-residual base has nonzero disagreement;
- no primitive program of depth 1 or 2 qualifies;
- a depth-3 composition qualifies with zero disagreements;
- deleting either coupling from the selected state restores disagreement;
- selected state equals the adapter independently selected in V2, downstream Hex-kernel checked there;
- no held-out data influences search.

## Claim boundary

A pass earns bounded compositional repair synthesis from a supplied primitive developmental basis. It does not establish autonomous invention of the primitive basis or open-ended developmental language genesis.
