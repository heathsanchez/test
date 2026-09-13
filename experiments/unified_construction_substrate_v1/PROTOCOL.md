# Unified Construction Substrate V1 — Frozen Protocol

## Question

Can one small typed construction language make representations, witnesses, experiments, edits, and edit-generators instances of the same searchable program object, so that one frozen developmental kernel can discover *what kind of thing must change* without being told the architectural level in advance?

## Target claim

A pass establishes only a bounded result:

> one frozen finite typed substrate + one frozen verifier protocol can support heterogeneous developmental changes across several presently separate object classes.

It does **not** establish unrestricted program synthesis, universal completeness, self-hosting general intelligence, designerless goals, or development from no supplied primitives.

## Constitutional law

For an encounter `e`, protected consequences `P`, admissible set `A`, frontier `F`, and active realization `S_hat`:

1. Try retained/current programs first.
2. Independently verify decisive positive or negative evidence.
3. If verified, preserve the warranted consequence.
4. If search is incomplete, return `UNKNOWN_SEARCH`.
5. Only certified exhaustion of the declared current class may authorize developmental restructuring.
6. Convert a certified residual `rho` into adequacy constraints `C(rho)`; do not pre-label the failing architectural layer.
7. Search the typed substrate for the least-cost lawful program transformation satisfying `C(rho)` while replaying all protected consequences.
8. Preserve all still-admissible alternatives; execution may select one without deleting the others.
9. If alternatives remain non-canonical, construct the cheapest authorized discriminator expressible in the same substrate.
10. If the current edit class is certified complete and inadequate, its generating machinery may itself become the object of the same search.
11. Repeated verified developmental work may be compiled into retained executable structure when prospective total cost is lower than reconstruction.
12. Revocation and contraction are lawful only when protected consequence still replays.

## State model

```
Sigma_t = (P_t, A_t, F_t, S_hat_t, R_t)
```

where:

- `P_t`: protected warranted consequences;
- `A_t`: all presently admissible/warranted realizations;
- `F_t`: undominated lawful frontier under the declared cost vector;
- `S_hat_t`: active realization used for ordinary execution;
- `R_t`: retained verified programs/macros with warrant, scope, provenance, dependencies and revocation conditions.

Lawful, frontier-optimal, and active are distinct notions.

## MDC-L1 substrate requirements

The first substrate is intentionally finite and small. It must provide:

### Ground values
- Bool
- bounded finite integers
- finite tuples
- finite records
- finite lists with declared bounds

### Ordinary program structure
- typed input variables
- constants
- products/projections
- conditionals
- Boolean operators
- bounded equality
- finite lookup/table
- bounded fold/map over finite data
- explicit finite-state transition

### First-class code
- a typed `Code[A,B]` value representing an MDC-L1 program from `A` to `B`;
- quotation of admitted programs into `Code`;
- a verifier-controlled `eval : Code[A,B] x A -> B`;
- structural code constructors sufficient to build new well-typed code values;
- code size/cost available to the search procedure.

### Developmental objects
The same language must be able to represent, at minimum:

- a task-level constructor;
- a representation/map;
- a finite-state memory update;
- a discriminator/experiment;
- an edit `Code -> Code`;
- a bounded edit-generator returning candidate edits.

No challenge pack may introduce a new host-language repair primitive after the substrate is frozen.

## Search and completeness

Programs are enumerated by nondecreasing declared cost.

For every search invoked as "complete", the run must record the exact finite program class exhausted. Failure outside a complete declared class is only `UNKNOWN_*`.

Semantic duplicate programs may be quotient-collapsed only by an independently checked finite observational equivalence over the declared domain.

## Verification boundary

The substrate may construct candidates, but only the external verifier may authorize:

- task settlement;
- protection of a consequence;
- developmental admission;
- compilation/promotion;
- contraction;
- revocation.

The verifier must receive explicit finite evidence rather than trusting substrate-internal claims.

## Temporal freeze

Order of evidence generation:

1. Commit this protocol.
2. Commit the MDC-L1 type system, interpreter, enumerator, cost model, and generic developmental kernel.
3. Record exact commit/hash freeze.
4. Only then add heterogeneous challenge packs.
5. CI must verify the frozen substrate/kernel before running those challenges.

No substrate or kernel edit is allowed after challenge inspection without resetting the experiment version.

## Required heterogeneous challenge families

Post-freeze challenge packs must include at least:

1. **NO_CHANGE** — current program already resolves.
2. **REPRESENTATION** — a new distinction/feature is required.
3. **MEMORY** — identical present observation requires different consequence after different history.
4. **CONSTRUCTIVE_REACH** — current proof/constructor class is complete but too weak; a new composed constructor is required.
5. **CONTRACTION** — existing machinery contains a removable distinction.
6. **NONCANONICAL** — several cost-minimal lawful programs survive.
7. **EXPERIMENT** — the substrate must construct a discriminator that separates surviving programs.
8. **EDIT** — the required change is a program transformation rather than a task output.
9. **EDIT_GENERATOR** — an existing finite edit family is exhausted; a lawful generator over edits must be constructed from the frozen code substrate.
10. **UNKNOWN_SEARCH** — deliberately incomplete search must remain UNKNOWN.
11. **CERTIFIED_NO_REPAIR** — a complete finite class must be exhausted with no repair.
12. **AUTHORITY_CONFLICT** — inconsistent protected consequence must stop rather than induce arbitrary self-change.
13. **REUSE/COMPILE** — a previously expensive verified construction must be reused without rediscovery, with measured work reduction.

The kernel is not told which family a challenge belongs to.

## Success criterion

The strongest desired V1 result is:

> A single frozen typed construction substrate and frozen developmental kernel correctly resolve or conservatively stop on heterogeneous unseen finite challenges, while discovering whether the needed lawful change acts on task construction, representation, state, experimentation, edits, or edit-generation, and while compiling reusable verified work.

## Remaining boundary after a pass

Even a full pass leaves externally supplied:

- the primitive MDC-L1 semantic universe;
- the verifier/authority;
- resource bounds;
- challenge/encounter arrival;
- the cost vector and any policy governing its revision.

The next question would then be whether parts of the primitive substrate and cost policy can themselves be brought inside the same verified developmental loop.
