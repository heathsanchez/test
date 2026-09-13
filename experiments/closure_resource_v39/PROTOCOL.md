# Closure as Developmental Resource V39 — Frozen Protocol

## Question

V38 established that a verified spanning cycle of warranted transitions can close before the whole recurrent machine is locally complete.

V39 asks whether that closed relational whole can then do developmental work:

> can a verified cycle become a reusable coordinate frame that exposes regularity in already-warranted local transitions, uses that regularity to propose missing transitions, and measurably reduces external verification work without ever treating an unverified proposal as fact?

This experiment tests **prediction and verification acceleration**, not logical entailment of unseen transitions.

## Input interface

V39 begins at the verified partial-transition boundary produced by experiments such as V38.

The frozen kernel receives:

- opaque residual-state signatures;
- a binary anonymous transition alphabet;
- a set of already-warranted deterministic edges;
- an initial residual state.

It is not told:

- hidden state names;
- cycle coordinates;
- the hidden complete transition graph;
- any displacement parameter;
- which symbol closes the cycle;
- which edges are seeds versus targets;
- any family name.

All supplied edges are treated as already independently verified.

## Closure compilation

The kernel searches the warranted-edge graph for a directed spanning cycle through every discovered residual state.

If no such cycle exists, no closure frame may be compiled.

If a spanning cycle exists, the cycle is rooted at the initial residual state and induces relational coordinates

    0,1,...,n-1

around the verified whole.

This coordinate system is not an external state label.  It is derived from the closed relation itself.

For any already-warranted non-cycle edge q -> r, define its cycle displacement

    delta(q,r) = position(r) - position(q) mod n.

If at least two distinct warranted non-cycle edges have the same displacement and no warranted non-cycle edge contradicts it, the kernel may compile that displacement as a **proposal rule**.

The rule is not a theorem about unseen edges.  It is only a candidate generator.

## External verification and revocation

For each unresolved transition of the non-cycle symbol:

1. if a compiled displacement rule exists, propose its predicted target first;
2. ask an external verifier whether that concrete edge is correct;
3. only a positive verifier response converts the edge to WARRANTED;
4. on the first rejected prediction, revoke the compiled rule immediately;
5. complete the rejected edge and all later unresolved edges by local verified search.

The frozen kernel receives from the verifier only a Boolean response to the concrete edge it proposed.  It never receives the hidden transition table.

No rejected edge may be retained.

## Baseline

The local-search baseline has the same verified cycle coordinates but does not compile cross-state displacement regularity.

For each unresolved non-cycle edge it tests target states in relative cycle displacement order

    0,1,...,n-1

until the external verifier accepts the deterministic target.

Thus the comparison isolates the value of compiling relational regularity from the closed whole, rather than the value of merely knowing the cycle.

## Ablation

A closure-disabled mode must use the baseline local search even when a spanning cycle exists.

A pre-closure graph with one missing cycle edge must not compile a displacement rule at all.

## Post-freeze challenge family

Hidden complete machines are committed only after the scientific core is frozen.

The evaluator may include:

- a six-state family with a constant non-cycle displacement;
- a seven-state family with a different constant displacement and opposite raw symbol assignment;
- opaque state-signature relabellings;
- binary-symbol relabellings;
- a misleading family whose first seed edges support a displacement but a later hidden edge violates it;
- a pre-closure control;
- closure-disabled ablations.

## Frozen gates

R1. Frozen scientific core remains byte-identical after hidden machines are committed.
R2. No proposal rule is compiled before a spanning warranted cycle exists.
R3. A verified spanning cycle induces a complete relational coordinate frame over all states.
R4. Two consistent already-warranted non-cycle edges are sufficient to compile a displacement proposal rule.
R5. In the first regular hidden family, every closure-generated proposal is externally verified and accepted.
R6. In the second regular hidden family, every closure-generated proposal is externally verified and accepted.
R7. Closure-aware completion produces the exact hidden machine in both regular families.
R8. Closure-aware completion uses at least 3x fewer verifier calls than local search in each regular family.
R9. Closure-disabled ablation restores local-search verifier cost.
R10. Removing one cycle edge prevents compilation and restores local-search behavior.
R11. Opaque state-signature relabelling preserves compiled displacement, verified final structure, and verifier-call counts.
R12. Binary-symbol relabelling preserves compiled displacement magnitude, verified final structure, and verifier-call counts.
R13. The misleading family initially compiles a proposal rule from its verified seeds.
R14. The first contradictory hidden edge causes verifier rejection and immediate rule revocation.
R15. No rejected proposal is ever retained as a warranted edge.
R16. After revocation, fallback search still reconstructs the exact hidden machine.
R17. The misleading family never reports the revoked regularity as retained capability.
R18. The closure-aware kernel receives no hidden target table or target index from the verifier, only Boolean edge checks.
R19. The frozen kernel contains no hidden family size, hidden displacement, state signature, or challenge name.
R20. Across the regular families, verified closure-derived proposals convert a relational whole into lower future verification cost without weakening correctness.

## Claim boundary

A pass would establish:

> within this finite deterministic graph substrate, a verified relational closure can be compiled into a coordinate frame; repeated verified relations expressed in that frame can become a fallible proposal mechanism that reduces later external verification work, while verifier rejection revokes the overgeneralization and preserves correctness.

A pass would **not** establish that closure logically entails unseen transitions, that a closed graph self-constructs physically, or that Kauffman-style thermodynamic constraint closure has been reproduced.

The scientific separator is:

    closure as description
        versus
    closure as a verified structure that changes the economics of subsequent development.
