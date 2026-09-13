# Compiled Type-Constructor Genesis V4 — Frozen Protocol

## Question

Can one frozen generative basis promote a repeatedly verified **type-formation pattern** into a new anonymous parametric constructor, and can that learned constructor causally make new language signatures reachable under a fixed formation budget?

V3 showed verified composite programs can become reusable callable vocabulary. V4 asks for the next level: verified recurring *formation* becomes reusable grammar.

## Frozen primitive type basis

The primitive type language contains only:

- Bool
- one type variable X
- Product(A,B)

No duplicate/pair-state/type alias constructor is primitive.

A parametric type program is an expression F(X) built from X, Bool, and Product.

The frozen developmental kernel may:

1. enumerate parametric type programs by AST cost;
2. instantiate them at a challenge-supplied base type T;
3. ask the external authority whether the resulting concrete type is acceptable;
4. quotient only exact symbolic duplicates;
5. after repeated independently verified use of the same parametric formation program on distinct base types, promote it to an anonymous content-addressed type macro;
6. subsequently use that macro as a one-step formation constructor on new base types.

## Promotion rule

For verified F(X):

- recurrence key is the exact symbolic normal form of F, not the concrete instantiated type;
- at least two distinct verified base types must instantiate the same F;
- F must exceed the frozen minimum primitive formation cost;
- promotion creates an anonymous constructor

      t_h : Type -> Type

  whose interpreter expands by the frozen verified symbolic definition;
- provenance records all earning base types, challenge origins, and source formation digests.

No semantic name such as PairState, Duplicate, Memory, or ProductSquare may be assigned by the kernel.

## Causal transfer requirement

After promotion, a post-promotion challenge uses a **new base type never seen in promotion**.

The learned constructor must make a target language signature reachable under a strict type-formation cost bound.

A cold kernel with the same frozen primitive type basis and the same bound must fail.

A deeper cold bound must recover the same concrete signature using primitive Product.

Explicit ablation of the promoted constructor from the warm kernel must restore failure under the strict bound.

Thus a pass establishes:

    recurring verified formation
      -> anonymous parametric constructor
      -> new signature reachable under fixed budget
      -> ablation restores obstruction.

## Program layer

To ensure this is language generation rather than merely type pretty-printing, each accepted formed type must be used as the input signature of an executable identity language/program:

    input : F(T)
    output: F(T)
    body  : identity

The authority independently checks both the concrete signature and finite identity behavior.

## Temporal protocol

1. Commit this protocol.
2. Commit basis.py and kernel.py.
3. Freeze exact commits/hashes.
4. Only after freeze add challenge_pack.py and CI.
5. CI proves core files remain unchanged.

## Required post-freeze gates

- no duplicate/square type constructor primitive;
- first formation earned from primitive Product only;
- second distinct-base recurrence earns exactly one anonymous parametric type constructor;
- promotion has two distinct base types, provenance, and symbolic definition;
- transfer base type is unseen during promotion;
- warm tight transfer succeeds and its signature construction uses the promoted constructor;
- cold tight transfer fails;
- deeper cold search reconstructs the same signature primitively;
- learned constructor gives a strict formation-cost advantage;
- ablation restores tight failure;
- the produced language/program is executable and independently verified;
- incomplete search remains UNKNOWN rather than expressive failure.

## Claim boundary

A pass establishes bounded verified **formation-constructor compilation** over a supplied finite symbolic type algebra.

It does not establish invention of a new irreducible semantic type former, dependent types, arbitrary inductive types, unrestricted grammar invention, or autonomous revision of the promotion law.

The next boundary after a pass is whether a constructor can be invented whose semantics are not merely a macro-expansion into the old formation algebra, but require an actual new representational/evaluation rule.
