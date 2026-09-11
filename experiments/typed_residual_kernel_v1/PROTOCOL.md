# Typed Residual Kernel V1 Protocol

## Objective

Formalize the developmental constitution as a proof-carrying result and transition type. The kernel must prevent evidence from one boundary authorizing a repair belonging to another boundary.

## Frozen obligations

Lean must verify without `sorry`:

1. `UnknownExpressivity` contains both a completeness proof and a certified negative over the current language.
2. Incomplete search cannot emit `UnknownExpressivity`.
3. An existing resolving continuation cannot emit `UnknownExpressivity`.
4. Authorization is parameterized by an explicit selection policy and its exact obligation.
5. Results are indexed by state, language, authority, policy, and residual.
6. Each result type has only its licensed transition constructor.
7. Every transition carries a preservation proof.
8. Preservation composes over an arbitrary proof-carrying developmental path.

## Claim boundary

Passing Lean establishes type-level and theorem-level properties of the generic formal kernel. It does not establish that a real adapter supplies truthful certificates, that generator genesis succeeds, or that the kernel improves task performance.
