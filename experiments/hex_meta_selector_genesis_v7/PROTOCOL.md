# Hex Meta-Selector Genesis V7 — Frozen Protocol

## Question

V6 selected the correct scaling rule from three explicitly supplied extrapolations. V7 removes that explicit candidate list.

Can a smaller generic program language generate the extrapolation candidates, with prior fit, future consequence, and a frozen simplicity rule selecting the retained meta-rule?

## Prior behavior

The prior one-relation trajectory requires selecting its only named relation for connection to the fresh role.

## Generic selector language

A selector is a Boolean expression over a relation index i and relation count m.

Atoms:
- TRUE
- FIRST: i = 0
- LAST: i = m - 1

Programs:
- any atom;
- OR(atom, atom).

No explicit ALL, FIRST-ONLY, LAST-ONLY, or FIRST-OR-LAST candidate list is supplied. These behaviors arise by executing programs in the grammar.

Program cost is syntax-tree node count. Lexicographic order is used only after equal semantic consequence and equal cost.

## Developmental qualification

Stage 0: retain every program that matches the prior one-relation behavior.

Stage 1 future consequence: the complete V5 two-relation world, 36 objects and 1,296 ordered pairs.

Stage 2 continuation consequence: three named relations on a two-vertex carrier, exactly one loopless arc per relation. This is the complete 8-object, 64-pair world.

At each stage, exact source isomorphism is compared against exact colour-preserving target isomorphism.

## Selection

Retain only zero-disagreement programs after both future stages. Among extensionally equivalent survivors, select minimum program cost, then lexical order.

## Pass

A pass requires:
- the grammar generates multiple prior-consistent programs;
- stage 1 removes incomplete one-relation-only extrapolations;
- stage 2 removes the boundary-only FIRST OR LAST extrapolation;
- the unique minimum-cost survivor is TRUE, which selects every named relation;
- its instantiated representation matches the all-active pattern selected in V6 and verified through Hex in V5;
- a generated held-out three-relation Hex test passes after selection.

## Claim boundary

This is meta-rule synthesis inside a supplied generic selector language. The remaining designer boundary is the meta-language itself, plus the chosen subject and verifier.
