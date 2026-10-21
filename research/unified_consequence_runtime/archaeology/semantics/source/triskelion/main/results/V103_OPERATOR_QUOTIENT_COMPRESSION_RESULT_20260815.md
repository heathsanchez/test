# V103 Operator-Quotient / Compression Validation

Protocol precommitted in `protocols/V103_OPERATOR_QUOTIENT_COMPRESSION_PRECOMMIT.md` before validation execution.

Execution status: deterministic local execution of the committed exact finite-world algorithm. Not yet GitHub-Actions-attested.

## Primary frozen validation

Acquisition seed: `202608151703`
Held-out seed: `202608151704`

Old effective language: variables/constants/XOR. Exact unbounded closure over 3-input Boolean functions contained **16/256** functions: the affine class.

The acquisition hidden binary representative was truth-table id **1**. The held-out generator deliberately used a different literal representative, id **8**, plus variable permutation `[2,0,1]` and greater program depth.

Both representatives lie in the same orbit under transformations already available in the old language:

`{1,2,4,7,8,11,13,14}`

This orbit is exactly the eight non-affine binary Boolean operators under argument swap, independent input negations and output negation.

All 50 held-out targets lay outside the old affine closure.

### Discovery

Exact acquisition governed costs (4 operator-definition units + typed scope + withdrawal rule + exact minimal AST node costs):

- op 1: 200
- op 2: **184**
- op 4: **184**
- op 7: 238
- op 8: 228
- op 11: 200
- op 13: 200
- op 14: 214

So the discovered literal winner was not the literal generating operator. The acquisition optimum was the argument-swapped pair `{2,4}`. This is evidence that the stable object is not “recover the hidden surface primitive”; the data select a cheaper coordinate/representative inside the same non-affine quotient class.

### Source-distinct held-out validation

Held-out governed totals:

- op 1: 394
- op 2: **322**
- op 4: **322**
- op 7: 372
- op 8: 360
- op 11: 344
- op 13: 344
- op 14: 416

The acquisition-selected pair `{2,4}` remained exactly optimal on the held-out stream despite the literal hidden generator changing from 1 to 8 and the variable representation being permuted.

### Compression

`WARM_RETAINED` governed cost: **322**

`COLD_RECONSTRUCT` governed cost, allowing each held-out target to choose its own cheapest non-affine operator while paying a fresh governed operator package: **544**

Warm/cold ratio: **0.5919** — a **40.81%** reduction in this frozen AST/governance cost.

Equal-information LUT dispatcher: **400 truth-table bits**. AST/governance units and LUT bits are not the same code, so no encoding-independent MDL claim is made from the numeric comparison. The LUT control remains visible rather than being reweighted away.

### Exact search economy

Cold reconstruction semantic-state expansions: **38,415**

Warm retained semantic-state expansions: **254**

Search compression factor: **151.24×**.

This is an exact semantic-state expansion count in the finite synthesis world, not wall-clock runtime.

## Frozen gates

- G1 affine obstruction: **PASS**
- G2 quotient robustness under literal representative change: **PASS**
- G3 discovered class transfer: **PASS**
- G4 >=4× search compression: **PASS** (`151.24×`)
- G5 governance charged: **PASS**
- G6 warm governed cost < cold reconstruction: **PASS** (`322 < 544`)
- G7 LUT control reported without post-hoc reweighting: **PASS / descriptive control**

Primary verdict: **PASS_V103_QUOTIENT_LEVEL_OPERATOR_DISCOVERY**

## Exploratory stress discovery after the frozen run

A post-validation 20-stream stress sweep changed the held-out seed and literal hidden representative while keeping the acquisition-selected `{2,4}` fixed.

Results:

- warm retained cost beat cold reconstruction: **20/20** streams;
- search compression exceeded 4×: **20/20** streams;
- acquisition-selected representative stayed within 10% of the best literal held-out representative: **18/20** streams;
- median selected/best held-out cost ratio: **1.04145**;
- median warm/cold governed-cost ratio: **0.60410**;
- median search compression: **158.04×**.

The two >10% misses are scientifically useful: the literal representative is not fully stable across source distributions even though the quotient-level non-affine capability is. In several streams the held-out literal optimum switched from the `{2,4}` pair to the `{11,13}` pair. That further supports quotient-level rather than surface-operator identity.

This stress sweep is exploratory because its seeds were not in the frozen primary protocol.

## Main discovery

The strongest interpretation is not “the system recovered the operator that generated the data.” It often did not.

Instead:

> **Operator construction is more stable when stated modulo transformations already expressible in the old language.**

In this exact world, all non-affine binary primitives are one old-language orbit. The acquisition process selected the representative that minimized future expression cost, and that representative transferred across a literal generator change. The invariant developmental event is therefore the transition from the affine closure to the non-affine quotient class, while the surface primitive is a coordinate choice inside that class.

This directly sharpens the boundary-choice objection: a reasonable redescription should be allowed to rename/reparameterize operators through old-language automorphisms without changing whether a genuinely new quotient class has been added.

## Claim boundary

Finite exact Boolean world. This supports quotient-level boundary robustness and governed reconstruction/search compression relative to a frozen affine effective language. It does **not** establish representation-independent invention, natural-world operator construction, or encoding-independent universal MDL optimality.
