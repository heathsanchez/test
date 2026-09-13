# Hex Truth-Table Meta-Language Growth V8 — Frozen Protocol

## Question

Can the selector primitive retained in V7 be reconstructed rather than supplied, after the current meta-language is exhaustively shown inadequate?

V7 still supplied the atoms TRUE, FIRST, LAST and OR. V8 removes TRUE and OR from the initial language.

## Initial meta-language

The only selector programs initially available are:

- FIRST
- LAST

A selector chooses which named relations have both endpoint roles connected to the fresh identity role.

## Prior qualification

One named directed relation on three vertices. Exhaust all 64 loopless directed graphs and all 4,096 ordered pairs.

FIRST and LAST are extensionally identical in this world and both must preserve exact source isomorphism.

## Inadequacy consequence

Move to the independently used two-relation qualification world:

- two named loopless directed relations;
- three vertices;
- exactly one directed arc per relation;
- 36 objects;
- 1,296 ordered pairs.

The complete initial language contains only FIRST and LAST. Growth is authorized only if both fail.

## Generic growth substrate

After inadequacy is certified, expose all 16 anonymous binary Boolean truth tables over the two available boundary signals:

`f(FIRST(i), LAST(i))`

Truth-table bit order is:

`[f(0,0), f(0,1), f(1,0), f(1,1)]`

The operators are not given semantic names.

All 16 are exhausted. A candidate must preserve the prior one-relation world and solve the complete two-relation world.

## Independent continuation consequence

Any survivors are tested on a new three-relation world:

- three named directed relations;
- two vertices;
- exactly one loopless directed arc per relation;
- 8 objects;
- 64 ordered pairs.

This exposes the previously unseen input `FIRST=0, LAST=0` for the middle relation.

## Causal controls

For the retained truth table, flip each one of its four bits separately and verify that the corresponding stage loses semantic adequacy.

## Held-out Hex transfer

Only after selection, instantiate the retained operator on four named directed relations over two vertices, with multi-arc held-out objects.

Compile the representation to pinned HexGraphIso and kernel-check one positive and one negative obligation.

External capability freeze:

- HexGraphIso v0.6.0
- commit f247c0898414ca29c502691e3a8ad0b3ce0b4f6a
- Lean v4.34.0-rc2

## Pass

A pass requires:

- FIRST and LAST both pass the one-relation prior;
- FIRST and LAST both fail the two-relation consequence;
- the complete 16-operator substrate is exhausted;
- exactly two truth tables survive prior plus two-relation consequence;
- three-relation consequence leaves one survivor;
- the survivor is truth table [1,1,1,1], without that meaning being supplied as a named atom;
- every single-bit mutation fails at the stage that witnesses that bit;
- the selected operator reproduces the V7 selector behavior;
- held-out four-relation Hex obligations pass.

## Claim boundary

This establishes bounded meta-language primitive construction from a supplied complete Boolean operator substrate. The Boolean substrate itself remains supplied.
