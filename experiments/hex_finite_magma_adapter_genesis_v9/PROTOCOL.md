# Finite Magma Adapter Genesis V9

## Frozen question

Can the developmental machinery transfer beyond binary relations into finite magmas, where a total binary operation is a ternary relation x*y=z?

## Prior retained authority

V8 must report VERIFIED_META_LANGUAGE_PRIMITIVE_GENESIS_AND_TRANSFER. The warm condition may reuse the previously retained identity-star pattern: semantic role copies that denote one source element are synchronized through a fresh identity role.

## Source world

Order-2 magmas only.

There are 16 total binary operations on a two-element carrier and therefore 256 ordered magma pairs. Source isomorphism is exact under one carrier permutation.

## Target grammar

Target colour classes are L, R, O, A, and T.

L, R, and O are the left-argument, right-argument, and output copies of each source element. A is the identity-anchor copy. T contains one tuple node for every ordered input pair.

Six optional channel types define the complete cold grammar:

- T-L
- T-R
- T-O
- A-L
- A-R
- A-O

So the cold grammar has exactly 64 states.

Target isomorphism is exact colour-preserving graph isomorphism. Qualification canonicalizes all independent permutations of the four element-role colour classes; the tuple colour class is handled as an unordered multiset of transformed tuple signatures, exactly quotienting tuple-node permutations.

## Cold condition

Evaluate all 64 states over all 256 source pairs. A candidate qualifies only with zero disagreement.

## Warm condition

Reuse A-L, A-R, and A-O from the retained identity-star pattern. Search only the eight subsets of T-L, T-R, and T-O.

## Pass

A pass requires:

- one and only one cold zero-disagreement candidate;
- that candidate uses all six channels;
- one and only one warm zero-disagreement candidate;
- that warm candidate uses all three tuple-incidence channels;
- warm and cold winners are the same adapter;
- every single-channel ablation of the winner restores disagreement;
- cold evaluates 64 states and warm evaluates 8.

## Held-out Hex check

After qualification only, generate order-3 magma obligations: one positive relabelling pair and one negative pair produced by changing one operation-table entry.

Compile the synthesized adapter and kernel-check both through pinned HexGraphIso v0.6.0 at commit f247c0898414ca29c502691e3a8ad0b3ce0b4f6a using Lean v4.34.0-rc2.

## Claim boundary

This establishes only bounded finite-magma adapter genesis and held-out verified Hex exaptation. It does not establish unrestricted finite-algebra reduction, all-order completeness, or autonomous invention of the tuple-incidence grammar.
