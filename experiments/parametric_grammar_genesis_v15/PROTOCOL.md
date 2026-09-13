# Parametric Grammar Genesis V15 — Frozen Protocol

## Dependency

V15 begins one level above the verified V14 result.

Pinned lower-layer result:

- V14 branch: `recursive-grammar-genesis-v14`
- V14 successful run: `34750917389`
- V14 head: `2ac57c21ca8a2935e4a39fdea94426c753320ae6`
- V14 verdict:
  `VERIFIED_RECURSIVE_HIERARCHICAL_GRAMMAR_GENESIS_FROM_COMPILED_PHRASE_ATOMS`
- V14 artifact SHA-256:
  `35ec378762bdaaeeaa03837a3374f3a71d01906a155e6291d6beb82e8535a991`

V14 established literal hierarchical grammar:

    verified phrase atom
      -> literal binary rule
      -> rule-containing-rule
      -> causal construction advantage.

V15 asks whether literal recurring constructions can be generalized into a parameterized schema without supplying the variable pattern.

## Question

Can the developmental algorithm infer the smallest parameterized grammar schema forced by independently verified literal constructions?

The canonical example shape is not supplied:

    X Y X Y

Instead the learner receives only verified literal sequences.

A schema is represented only by an equivalence relation over positions.

Example:

    pattern (0,1,0,1)

means:
- positions 0 and 2 share one parameter;
- positions 1 and 3 share another.

The variable names themselves have no semantics.

## Primitive substrate

The V15 learner receives only:

1. verified literal lower-level constructions of one fixed arity/length;
2. sequence position;
3. equality of opaque lower-level tokens;
4. a generic finite generator for set partitions of sequence positions;
5. exact replay;
6. independent provenance;
7. a construction cost.

No parameterized template is supplied.

No `REPEAT`, `ALTERNATE`, `COPY`, `SYMMETRY`, `ABAB`, or grammar-variable pattern is primitive.

## Candidate schema universe

For sequence length n, enumerate every set partition of positions:

    {0,...,n-1} / ~

using canonical restricted-growth strings.

For n=4 there are 15 candidates.

A schema pattern p fits a literal sequence s iff every equality required by p is true in s:

    p_i = p_j  =>  s_i = s_j.

Different schema variables may be instantiated by the same token.

Therefore a more highly identified schema is more specific/compressed.

## Minimum-sufficiency objective

Among schemas fitting every admitted verified example, choose the schema with the fewest parameter classes.

Equivalently:

    identify positions until a verified example forces them apart.

If multiple incomparable schemas with the same minimum parameter count remain, preserve a frontier.

This is the grammar-schema form of:

    identify until forced to distinguish.

## Developmental transition

The governing algorithm remains:

    EXECUTE
    -> VERIFY
    -> DIAGNOSE
    -> CONSTRAIN
    -> RESTRUCTURE
    -> CHOOSE
    -> COMPILE
    -> UPDATE

### EXECUTE
Use the current positional-equivalence schema.

### VERIFY
Replay every admitted literal example through that schema.

### DIAGNOSE
If the schema requires two positions to be equal but an admitted example distinguishes them, produce the exact witness positions/example.

### CONSTRAIN
Enumerate only refinements of the current positional equivalence relation.

### RESTRUCTURE
Choose the refinements with the smallest increase in parameter count that fit all admitted examples.

### CHOOSE
Preserve all equal-cost incomparable lawful refinements.

### COMPILE
A schema may compile only after at least two independent examples witness every distinction that the schema keeps separate.

### UPDATE
The compiled schema becomes a one-step constructor over opaque verified lower-level tokens.

## Required post-freeze gates

### S1 — no parameter pattern supplied
Frozen core contains only generic set-partition generation and equality testing.

No challenge-specific positional pattern appears in the frozen core.

### S2 — maximally identified beginning
With only independently verified all-equal examples:

    A A A A
    B B B B

the minimum lawful schema is:

    (0,0,0,0).

The learner must not invent extra variables.

### S3 — consequence-forced variable split
Add independently verified examples of the form:

    C D C D
    E F E F

with C != D and E != F.

The old one-variable schema is certified insufficient.

The minimum lawful refinement must be discovered as:

    (0,1,0,1)

without that pattern being supplied.

### S4 — exact global minimum
For the refined training set, exhaustively enumerate all 15 positional partitions.

Certify that:
- no one-variable schema fits;
- a two-variable schema fits;
- the selected two-variable schema is globally minimum;
- no more general lower-cost schema exists.

### S5 — schema compilation
After two independent distinction-witnessing examples, compile the anonymous schema with:
- exact positional partition;
- parameter count;
- provenance;
- lower-layer dependency.

### S6 — unseen parameter transfer
On unseen verified lower tokens G,H:

    G H G H

the compiled schema must construct the full literal sequence in one schema application.

Cold direct binary concatenation requires 3 composition steps.

Under a tight budget of 1:
- warm schema succeeds;
- cold direct construction fails;
- cold relaxed budget 3 succeeds;
- ablation restores tight failure.

### S7 — parameters may themselves be compiled grammar tokens
The schema must accept opaque V14-style nonterminal tokens as bindings.

No distinction is made between a phrase atom and a compiled grammar token at the parameter interface.

### S8 — wrong structure falsifies retained schema
A verified target:

    G H H G

must fail replay under the retained (0,1,0,1) schema.

The learner must not force it through merely because it has the same length and token counts.

### S9 — further consequence expands the schema
If the wrong-structure example is admitted alongside the earlier training examples, the current schema becomes insufficient.

The minimum lawful refinement should expand to the smallest partition fitting all evidence.

### S10 — split ablation
If positional splitting is disabled, the first all-equal schema may remain, but the later distinction must return:
    `CERTIFIED_SCHEMA_INADEQUACY`.

### S11 — single-example compilation control
One ABAB-style example may justify a provisional schema, but must not compile it.

Independent recurrence is required for retention.

### S12 — incomplete authority
Any unverified literal exemplar returns `UNKNOWN_AUTHORITY`.

### S13 — heterogeneous pattern
The same frozen learner must infer a different minimum schema on a different literal family, e.g. an AAB-style equality structure.

## Construction cost

Warm compiled schema:
    1 constructor application.

Cold length-n literal sequence under binary CONCAT:
    n-1 applications.

The construction-budget gate tests causal retained value, not mere descriptive naming.

## Claim boundary

A V15 pass establishes only:

> In a bounded finite equality-pattern language, positional parameter structure can be synthesized as the minimum verified partition of literal constructions, refined only when consequence forces additional variables, compiled after independent recurrence, and reused on unseen opaque lower-level tokens.

It does NOT establish:
- natural-language grammar;
- arbitrary tree-pattern anti-unification;
- context-sensitive variables;
- universally quantified semantics outside the declared type/interface;
- open-ended grammar invention;
- designerless choice of the parameter-cost objective.

The next boundary is to remove fixed sequence position/arity and synthesize typed tree contexts / variable-bearing relational programs.
