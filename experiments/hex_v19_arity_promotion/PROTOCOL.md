# Hex V19 Cross-Arity Occurrence-Node Promotion

## Question

Can the verified V16 occurrence-node repair be promoted into a general arity rule by future consequence, rather than replaying cold subset search independently at arities 4 and 5?

## Prior authority

The workflow downloads the exact sealed V16 artifact:
- run 34736220712
- artifact 10311390727
- artifact SHA-256 d53b6d12d0956a1c7fb86acd603495fba994537ecd557882671b70fb74004cdb

Required verdict:
VERIFIED_TERNARY_COHERENCE_EXPANSION_AND_HELDOUT_TRANSFER

V16 established that for arity 3, the unique adequate occurrence-node representation connects each tuple occurrence to all three argument-position roles.

## Frozen future consequences

Two continuation experiments were completed before this promotion test and are frozen byte-for-byte in this branch:

V17:
- arity 4
- carrier 2
- relation size 4
- 1,820 objects
- 3,312,400 ordered pairs
- all 15 nonempty connection subsets evaluated
- evidence SHA-256: 4bd358531d126a753f5a88c794ceb61d9ae882ddc5514e63a7c5e63e81fb5606

V18:
- arity 5
- carrier 2
- relation size 4
- 35,960 objects
- 1,293,121,600 ordered pairs
- all 31 nonempty connection subsets evaluated
- evidence SHA-256: dc5054e53f2cec05cec1696f113d448c89cbfe5fee2f158e44a29d658e11151c

## Generalization candidates

All candidates reproduce V16 exactly at arity 3:

1. OBSERVED_ONLY
   Retain only positions 0,1,2.

2. OBSERVED_PLUS_BOUNDARY
   Retain positions 0,1,2 plus the first and last active position.

3. ALL_ACTIVE
   Connect the occurrence node to every active argument position.

No candidate is preferred from V16 alone.

## Selection

Evaluate all three rules on frozen V17 consequence.

Then evaluate only V17 survivors on frozen V18 consequence.

Retain a rule iff its instantiated subset has zero semantic disagreement.

## Cold comparison

Cold independent search costs:
- V17: 15 candidates x 3,312,400 ordered pairs
- V18: 31 candidates x 1,293,121,600 ordered pairs

Staged generalization-law selection costs:
- V17: 3 rules x 3,312,400 ordered pairs
- V18: surviving rules only x 1,293,121,600 ordered pairs

## External held-out checks

After law selection, generate new held-out full-star encodings:
- arity 4, carrier 3, three tuple occurrences
- arity 5, carrier 3, three tuple occurrences

For each arity, kernel-check one positive and one negative source obligation through pinned HexGraphIso.

## Pass

A pass requires:
- exact V16 external authority;
- exact frozen V17/V18 evidence hashes;
- all three laws agree on arity 3;
- V17 eliminates OBSERVED_ONLY;
- V18 eliminates OBSERVED_PLUS_BOUNDARY;
- ALL_ACTIVE alone survives;
- the selected rule matches the unique full-star winners in both cold searches;
- staged rule selection uses fewer candidate-level semantic pair comparisons than cold search;
- both arity-4 and arity-5 held-out Hex checks pass.

## Claim boundary

The three-member generalization family is supplied. The experiment tests future-consequence selection and cross-arity reuse, not autonomous invention of the generalization grammar.
