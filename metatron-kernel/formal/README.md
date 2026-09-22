# IdealLean portable semantics

`IdealLean` is a small, provisional specification vocabulary for reasoning
about theorem declaration and opaque signature promotion. It is intentionally
independent of the Rust kernel APIs and is **not** a model of full Lean.

## Scope and assumptions

The model includes a small expression syntax, chronological declaration
environments, opaque theorem declarations, an abstract typing relation, and a
locally nameless binder-opening operation. It assumes that a client supplies a
`TypeCorrect : Environment → Expr → Expr → Prop` relation. The portable
`Checks` judgment adds freshness and the requirement that every constant in a
candidate's type and proof is already declared in the prior environment. It
also requires the declared theorem type to inhabit `sort 0`, the skeleton's
representation of `Prop`, before its proof is checked against that type.

The theorem transition is deliberately ordered:

1. `Checks TypeCorrect prior candidate` is derived against `prior`.
2. `install prior candidate` appends an opaque theorem declaration.

The proof term is never stored in the installed declaration. Only a
`definition` may expose a reducible body.

## Mechanized laws

- `openBinder_bvar_zero`: opening the outer variable produces the requested
  free variable.
- `openBinder_bvar_succ`: opening the outer binder leaves deeper variables
  unchanged.
- `openBinder_const`: opening does not change constants.
- `installed_theorem_has_no_body`: installed theorem declarations are opaque.
- `type_correct_in_prior_environment`: type correctness is established against
  the environment from before installation.
- `theorem_type_is_prop_in_prior_environment`: the declared theorem type is
  established as `Prop` against the prior environment.
- `prior_environment_is_prefix`: installation preserves declaration order.
- `checked_proof_uses_prior_environment`: proof constants resolve before
  installation.
- `checked_theorem_is_not_self_referential`: a fresh theorem cannot cite
  itself, because its proof is checked against the prior environment.
- `promote_preserves_environment_validity`: inductive, constructor and recursor
  signatures validated in dependency order preserve any environment-validity
  invariant whose one-signature extension rule has been established.
- `promoted_signatures_are_opaque`: the promoted signatures have no delta body;
  iota, projections and eta require separately qualified rules.
- `ParameterizedInductivePromotion.promote_preserves_environment_validity`:
  a validated parameter telescope plus dependency-ordered opaque signatures
  preserves environment validity under the existing one-signature extension
  rule.
- `ProdUniversePromotion.promote_preserves_environment_validity`: the same
  promotion law remains valid after validating the exact two-universe `Prod`
  telescope, its computed result level, and signatures at those levels.
- `PProdSortPromotion.promote_preserves_environment_validity`: the existing
  parameterized opaque-promotion law remains valid after independently
  validating the exact `PProd` Sort-polymorphic telescope, `Sort u`, `Sort v`,
  its computed `Sort (max 1 u v)` result, and signatures at those sorts.

## Non-goals

This skeleton does not derive positivity or recursor signatures, and it does
not specify general parameter-telescope typing or general Lean universe levels,
definitional equality, reduction, iota,
projections, eta, quotient primitives, proof irrelevance, elaboration, kernel
serialization, or trust boundary. `TypeCorrect`, `SignatureValid`, and
`EnvironmentValid` are abstract, so these files do not establish soundness of
the Rust checker or of any whole checker. In particular, the parameterized
promotion theorem is a portable environment law, not a Rust-refinement claim.
The `ProdUniversePromotion.Level` vocabulary contains only the level forms
forced by tutorial 040 and likewise does not constitute a general universe
framework. `PProdSortPromotion.Level` is separately limited to tutorial 041;
its replication does not itself promote a shared parameterized-inductive
architecture.

## Build

The pinned toolchain is Lean `v4.29.1`.

```sh
cd metatron-kernel/formal
lake build
```
