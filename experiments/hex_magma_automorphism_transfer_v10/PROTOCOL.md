# Magma Automorphism Transfer V10

## Frozen question

V9 qualified the magma-to-coloured-graph reduction as an isomorphism decision adapter. V10 asks whether the same reduction preserves a richer structure: the automorphism action.

## Prior authority

V9 must report VERIFIED_FINITE_MAGMA_ADAPTER_GENESIS_AND_TRANSFER and the selected adapter must contain all six channels T-L, T-R, T-O, A-L, A-R, A-O.

## Exhaustive order-2 world

For every one of the 16 order-2 magmas:

1. enumerate every source carrier permutation and retain exactly the magma automorphisms;
2. independently enumerate all colour-preserving permutations of the L, R, O, and A element-role classes in the encoded target;
3. quotient tuple-node permutations extensionally through their complete transformed incidence signatures;
4. retain exactly the target graph automorphisms.

A full-adapter pass requires:

- source automorphism-group order equals target automorphism-group order for all 16 magmas;
- every target automorphism uses the same underlying carrier permutation on L, R, O, and A;
- those common permutations are exactly the source magma automorphisms.

## Causal ablation

Remove each of the six V9 channels in turn.

For every removed channel, at least one order-2 magma must exhibit an enlarged or otherwise incorrect target automorphism action.

## Held-out order-3 capability check

Use the additive magma on three elements.

Its source automorphism group is computed independently by exhaustive permutation.

Compile the V9 graph representation and ask pinned HexGraphIso for its automorphism-group order. The workflow must fail unless Hex reports the same order.

The generated Lean file also repeats one positive and one negative graph-isomorphism obligation.

## Claim boundary

This is bounded automorphism-action preservation: exhaustive at order 2 plus one held-out order-3 Hex automorphism check. It is not a general all-order theorem.
