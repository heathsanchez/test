# G9-001 Empty-Inductive Authority Plan

**Goal:** Accept the exact Arena empty-inductive block without treating exported
recursors as axioms or introducing authority for any broader inductive class.

**Scope:** One safe, singleton, nonrecursive inductive type with no universe
parameters, parameters, indices, nesting, constructors, or reflexivity; one
independently derived empty eliminator. Nonempty, indexed, recursive, mutual,
nested, unsafe, K-like, and projection-bearing blocks remain `UNKNOWN`.

## Authority boundary

The exported inductive record is an untrusted claim. Parsing and ordinary type
well-formedness cannot authorize a recursor: a fabricated recursor whose type
is `False` is itself a well-formed declaration type and would become an axiom
if installed.

The checker therefore derives the unique supported block shape:

```text
I : Type
I.rec.{u} : (motive : I -> Sort u) -> (x : I) -> motive x
```

It compares the exported type and recursor against that derivation, including
names, universe binders, ownership, arity metadata, `all`, empty constructor and
rule lists, safety, and `k = false`.

## Transaction

1. Parse and resolve every nested identifier in the full inductive record.
2. Classify the exact supported empty shape; unrelated well-formed shapes stay
   `UNKNOWN`.
3. Validate the inductive type against the prior environment.
4. Stage an opaque type signature in a persistent child environment.
5. Structurally derive and match the empty eliminator and check its type in the
   staged environment.
6. Stage an opaque recursor signature.
7. Publish the completed child environment only after the whole block passes.

Both signatures have no executable body. The empty recursor has no iota rule;
applications remain neutral.

## Deciding experiments

- Exact tutorial 036 must `ACCEPT`.
- Exact tutorial 062 must `ACCEPT`, proving recursor authority is usable.
- Perturb only recursor name, type, `all`, `k`, or arity metadata in case 036;
  each supported-shape contradiction must `REJECT`.
- `tests/other/extra-rec.ndjson`, `tests/bugs/orphan-rec.ndjson`, tutorial 073,
  and an atomicity fixture must never accept.
- Ablating the validator back to unsupported handling must restore `UNKNOWN`.
- The exact protected prefix and every cycle/budget `UNKNOWN` boundary must be
  unchanged.

## Promotion boundary

Deep evidence retains the complete block and the derived comparison. Runtime
authority executes only two opaque constant signatures. This is an exact
external qualification certificate until a portable `IdealLean` inductive
rule and Rust refinement theorem are added.
