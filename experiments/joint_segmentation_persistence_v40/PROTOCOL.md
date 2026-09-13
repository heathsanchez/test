# Joint Segmentation + Persistence Genesis V40 — Frozen Protocol

## Question

Can locally individuated occurrences be removed as supplied primitives?

V40 receives only two flat finite binary boundaries:

- BEFORE;
- AFTER.

The scientific kernel is given:

- no occurrence boundaries within BEFORE;
- no occurrence boundaries within AFTER;
- no cross-time identity map.

It must decide whether the whole frames can remain unsegmented, where any contiguous cuts are required, and which resulting segments—if any—must be linked across time.

The hidden challenge pack is committed only after this scientific core is frozen.

## Cheaper non-occurrence baselines

Two representations precede segmentation:

- VOID: retain no distinction;
- BAGS: retain only the unordered multiset of bits in BEFORE and the unordered multiset of bits in AFTER.

If consequence is preserved by one of these, the kernel must stop there.

Thus V40 cannot pass merely by always segmenting a boundary.

## Candidate segmentation language

A frame of length n may be partitioned only by placing cuts between adjacent raw symbols.

Each candidate segmentation is therefore a composition of the flat ordered boundary into non-empty contiguous blocks.

No semantic meaning is attached to a cut or block.

For a candidate pair of BEFORE/AFTER segmentations, a candidate persistence hypothesis is a partial injective matching between the resulting blocks.

A candidate representation retains only:

- the unordered multiset of matched BEFORE/AFTER block-state pairs;
- the unordered multiset of unmatched BEFORE block states;
- the unordered multiset of unmatched AFTER block states.

A block state is its raw contiguous binary substring.

Block labels and block order are not exported into the consequence quotient.

## Generic intervention evidence

An active world contains, for each complete binary BEFORE/AFTER state and each raw BEFORE intervention position, one observed raw AFTER response position.

The kernel is not told which segmented occurrence the intervention or response belongs to.

For a candidate segmentation and matching:

1. locate the candidate BEFORE block containing the intervention position;
2. locate the candidate AFTER block containing the observed response position;
3. require those two blocks to be linked by the candidate matching.

This intervention-consistency test does not alter consequence labels.

It is external transition evidence used only to reject candidate persistence maps that fail to carry an observed action into its response block.

## Exact consequence verification

A candidate must induce exactly the authoritative consequence partition.

Under-distinguishing candidates fail by merge obstruction.

Over-distinguishing candidates fail by excess-distinction obstruction.

Intervention-inconsistent candidates fail by intervention obstruction.

## Search order

The frozen lexicographic metric is:

VOID:
    (0,0,0)

BAGS:
    (0,1,0)

SEGMENTS:
    (
        1,
        total number of BEFORE + AFTER cuts,
        number of cross-time matching links
    )

There are no tuned scalar coefficients.

All candidates at one metric are exhausted before a more structured metric is authorized.

## Primary finite scope

Primary hidden worlds use:

- four raw binary positions per frame;
- complete 2^8 passive transition tables;
- when active, one passive row plus one observed response row for each of the four possible raw intervention positions at every binary transition state.

All 2^(4-1)=8 contiguous segmentations per frame are generated exhaustively.

## Post-freeze challenge family

After freeze the hidden harness will include:

- constant consequence requiring VOID;
- frame-level multiset consequence requiring BAGS;
- a segmentation-only world requiring the unique two-block cut 2|2 in both frames but no persistence links;
- a passive 2|2 world whose minimum frontier contains exactly two distinct two-link correspondences;
- the same 2|2 world with observed intervention-response locations that collapse the frontier to the hidden correspondence;
- a full four-singleton segmentation with a nontrivial four-link cross-time permutation;
- independent BEFORE/AFTER boundary reversals;
- consequence-label relabellings.

The scientific kernel is never told these hidden cuts or maps.

## Frozen gates

J1. Frozen scientific core remains byte-identical.
J2. One frozen kernel recovers every post-freeze world at the correct minimum metric.
J3. Constant consequence stops at VOID.
J4. Whole-frame multiset consequence stops at BAGS with no cuts.
J5. Segmentation-only consequence exhausts VOID/BAGS and every cheaper segmented representation before earning exactly two total cuts and zero links.
J6. The segmentation-only minimum frontier is the unique hidden 2|2 + 2|2 cut pair.
J7. Passive joint world earns those same two cuts plus exactly two persistence links.
J8. Passive joint world preserves exactly two minimum correspondence witnesses rather than choosing an unjustified identity.
J9. Active intervention-response evidence collapses the passive two-member frontier to the hidden correspondence without changing the earned cut count or link count.
J10. Full-persistence world earns six total cuts and four links and exhausts every cheaper metric first.
J11. Independent reversal of BEFORE and AFTER boundaries transforms recovered cuts and links equivariantly.
J12. Consequence-label relabelling preserves the minimum metric and frontier.
J13. Cut ablation preserves VOID/BAGS but blocks every world genuinely requiring segmentation.
J14. Link ablation preserves segmentation-only structure but blocks every world genuinely requiring persistence.
J15. Incomplete authority remains UNKNOWN_AUTHORITY and verifier ablation authorizes no segmentation/persistence search.
J16. Named object/site/channel/graph/relation concepts and hidden challenge cuts/maps are absent from the frozen executable kernel.

## Claim boundary

A pass would not establish object segmentation from structureless reality.

V40 still supplies:

- a flat binary boundary;
- within-frame linear adjacency/order;
- stable raw positions for the duration of one frame;
- the language of contiguous cuts;
- partial injective matching between candidate segments;
- external consequence authority;
- generic intervention target and response positions in active worlds.

What V40 can establish is narrower:

> local occurrence boundaries and cross-time persistence links need not both be supplied. Within a flat ordered boundary, verified consequence can force the minimum contiguous segmentation and then preserve or resolve cross-time correspondence only to the extent justified by passive and interventional evidence.

If V40 passes, the remaining handhold is the raw within-frame positional lattice itself. The next frontier is to remove pre-individuated raw positions and derive segmentation from a boundary with weaker local structure.
