# V104 Adversarial Quotient-Identity Falsification

Protocol was frozen first in `protocols/V104_ADVERSARIAL_QUOTIENT_IDENTITY_PRECOMMIT.md`.

## Execution status

Two GitHub Actions launches (`31866781031`, `31866821184`) failed before acquiring a runner: `runner_id=0`, `steps=[]`. These are infrastructure failures, not scientific failures. The exact finite calculation was then executed independently against the committed algorithm after one harness-only correction to the deliberately invalid B2 presentation control (the first implementation accidentally retained constant `1`, making NOT recoverable from XOR; the frozen protocol itself was unchanged).

Because the successful execution was not Actions-hosted, this result is **not yet Actions-attested**.

## Primary verdict

**PASS_V104_ADVERSARIAL_QUOTIENT_IDENTITY**

All frozen G1–G6 predicates passed in both exact finite substrates.

### G1 — literal-coordinate invariance

B2:
- old affine binary functions: **8/16**;
- non-affine binary functions: **8/16**;
- all 8 non-affine literal operators form exactly **one** orbit under old-language-expressible argument swap, input negations and output negation:

`{1,2,4,7,8,11,13,14}`.

F3 unary:
- old affine maps: **9/27**;
- non-affine maps: **18/27**;
- all 18 non-affine literal operators form exactly **one** orbit under affine-bijection pre/post coordinate changes already available in the old language.

So in both frozen worlds, literal representative identity is not stable, but the old-language orbit is.

### G2 — old-presentation invariance

Three different presentations of the same old semantic capability were evaluated in each substrate.

B2:
- XOR + constants + NOT;
- XNOR + constants + NOT;
- extensional affine truth-table set.

Each generated exactly the same **8-function binary affine closure**.

F3:
- `x+1`, `2x`, constants;
- `x+2`, `2x+1`, constants;
- extensional affine-map set.

Each generated exactly the same **9-map affine closure**.

Novelty classification therefore did not depend on those old-language generator presentations.

### G3 — genuine boundary enlargement deliberately kills novelty

B2 reachability on three-input Boolean functions:
- old affine closure: **16/256**;
- after adding **any one** of the 8 non-affine binary representatives: **256/256**.

F3 unary reachability:
- old affine closure: **9/27**;
- after adding **any one** of the 18 non-affine unary representatives: **27/27**.

This is the important anti-cosmetic control: when the old capability state is genuinely enlarged enough to subsume the class, the previous novelty distinction disappears.

### G4 — verifier-indexed refinement

B2 frozen witness:
- XOR and OR agree on weak verifier inputs `00,01,10`;
- they differ at the withheld separator `11`.

F3 frozen witness:
- identity `x` and square `x²` agree on weak verifier inputs `0,1`;
- they differ at withheld separator input `2`.

Thus an old and a genuinely closure-expanding behaviour can be observationally identical under a weak verifier and split under a stronger one.

The identity object is therefore not just `[O]_A`; in these worlds it must be indexed by verifier authority as well: `[O]_(A,V)`.

### G5 — cross-substrate recurrence

Both substrates exhibit the same pattern:

1. coarse old closure;
2. strong-verifier candidate outside that closure;
3. many literal representatives collapse under old-language automorphisms;
4. adding one representative expands actual reachability and removes the novelty distinction.

This is a two-substrate structural recurrence only, not a universality claim.

### G6 — negative controls

All passed.

Most importantly, allowing non-invertible old maps in the identity relation would create false collapses:
- B2: `OR(x,0)=x`, which would spuriously identify a non-affine operator with old identity behaviour;
- F3: `square(constant 0)=constant 0`, same failure mode.

Therefore the quotient cannot be “anything reachable by old maps”; the identity transformations need to be reversible/structure-preserving for this criterion.

The deliberately incomplete old-language presentations were also correctly rejected:
- B2 incomplete linear presentation size: **4**, not 8;
- F3 incomplete translation/constant presentation size: **6**, not 9.

## What survived the attempt to break it

In these two exact worlds, the strongest supported object is:

`novelty identity = verifier-indexed behavioural orbit modulo invertible transformations already realizable by the old capability state`.

This is stronger than literal-operator identity and stronger than a syntactic frozen-DSL claim, but still explicitly relative to `(A,V)`.

## Exploratory discovery after the frozen V104 gates — F5

The next exploration deliberately moved to a richer fresh finite algebra: unary functions over GF(5).

This **broke the naive stronger hypothesis** that “all non-old operators collapse to one novelty class.”

Exact counts:
- all unary GF(5) functions: **3125**;
- old affine maps: **25**;
- non-affine maps: **3100**;
- non-affine old-automorphism orbits: **12**, not 1;
- orbit sizes: `100,100,100,200,200,200,200,400,400,400,400,400`.

This is a useful falsification, not a setback. The quotient idea survives but becomes a **capability lattice** rather than one binary old/new class.

Adding one representative from each orbit produced exact closure sizes:

| F5 orbit | orbit size | resulting closure size |
|---:|---:|---:|
| 0 | 100 | 125 |
| 1 | 200 | 225 |
| 2 | 400 | 925 |
| 3 | 200 | 925 |
| 4 | 400 | 925 |
| 5 | 200 | 925 |
| 6 | 200 | 625 |
| 7 | 400 | 3025 |
| 8 | 400 | 3025 |
| 9 | 100 | 625 |
| 10 | 400 | 3025 |
| 11 | 100 | 125 |

The orbit-containment pattern is also structured rather than arbitrary:

- orbit 0 closure contains `{0}`;
- orbit 1 contains `{1}`;
- orbit 2/3 contain `{0,1,2,3}`;
- orbit 4/5 contain `{0,1,4,5}`;
- orbit 6/9 contain `{0,1,6,9}`;
- orbit 7/8/10 contain `{0,1,2,3,4,5,6,7,8,9,10}`;
- orbit 11 remains `{11}`.

So “construction” in the richer world is not merely crossing one old/new boundary. Different new equivalence classes induce **different amounts and directions of future reachability**.

That suggests a sharper object than the initial V103/V104 framing:

> **developmental state may be the partially ordered family of verifier-distinguishable behavioural orbits reachable from the current capability basis.**

A new operator then matters by how it changes that reachability lattice, not simply by whether its literal syntax was absent.

## Emerging unification

The current evidence now points to three distinct developmental transitions:

- **EXTEND** — admit a new behavioural orbit/class and thereby enlarge reachable behaviour;
- **REFINE** — stronger verifier evidence splits a previously merged observational class;
- **RETRACT/COLLAPSE** — governance withdraws a retained class, or capability enlargement makes a previous novelty distinction no longer novel.

This is exploratory theory, not yet a promoted headline claim.

## Claim boundary

Primary V104 supports quotient-level identity robustness only in two exact finite algebraic substrates. The F5 lattice is exploratory because it was inspected after the V104 primary protocol. None of this yet establishes natural-world, open-ended, representation-independent operator invention or reasoning-language growth.
