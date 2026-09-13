# Hex Verified Meta-Language Contraction V9 — Frozen Protocol

## Question

After V8 expanded the meta-language and constructed a successful binary selector operator, can verified consequence prove that some of the scaffolding used to construct it is no longer needed and contract the retained machinery?

## Frozen input

Read the sealed V8 authority.

Required selected truth table:

`[1,1,1,1]`

Inputs are the two boundary signals:

- FIRST
- LAST

V8's runner-up control is:

`[0,1,1,1]`

## Dependency factorization

For every subset of the input variables:

- none
- FIRST only
- LAST only
- FIRST and LAST

test whether the selected truth table factors through that projection.

A factorization through a subset is valid iff any two Boolean input assignments that agree on the retained variables always have the same output.

The selected contraction is the minimum-cardinality valid dependency set.

## Semantic replay

After contraction, replay the exact bounded semantic worlds that earned the V8 operator:

- one relation, all 64 loopless directed graphs on 3 vertices;
- two relations, one arc each on 3 vertices;
- three relations, one arc each on 2 vertices.

The contracted selector must preserve zero disagreement on all three.

## Controls

- The V8 runner-up [0,1,1,1] must not factor through the empty input set.
- It must also fail to factor through either single input alone.
- Replacing the contracted output 1 with output 0 must restore semantic failure.

## Held-out continuation

Instantiate the contracted zero-input selector on five named directed relations over a two-vertex carrier.

No FIRST/LAST computation is used at runtime: every relation is selected directly.

Generate one held-out positive isomorphism and one held-out negative obligation, compile to pinned HexGraphIso, and kernel-check both.

## Pass

A pass requires:

- V8 authority is valid;
- the selected V8 operator factors through the empty input set;
- empty is the unique minimum dependency set;
- the V8 runner-up requires both inputs;
- semantic replay stays exact after contraction;
- constant-zero ablation fails;
- held-out five-relation Hex checks pass.

## Claim boundary

This establishes bounded verified contraction of learned developmental machinery. It does not remove the supplied Boolean substrate that was used to construct the operator in V8; it shows that the retained result can lawfully forget that scaffolding after its semantics are established.
