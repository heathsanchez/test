# Independent Nucleus: Nat prefix closure

Candidate: `e5916cf9d2863377d84a717604ef1da452eb62ea`.
Base: `84c35be307d3c154c6d1bab5dd9b0fdc0a696417`.
Run: https://github.com/heathsanchez/test/actions/runs/36789664885

## Qualification — WARRANTED / REUSABLE on this boundary

Run **36789664885**, job **110139326886**: **SUCCESS**.
Artifact **11131436487**, ZIP SHA-256 **4ed8f8855ccd55b350c2244d8e72ea43f9e4104d2bc0ba95c489396f0094e124** (downloaded and independently hashed).

- All **157 Rust tests pass**, including 16 new tests.
- **17/17** dependency slices: baseline UNKNOWN → candidate ACCEPT.
- **34/34** pinned reference checks accept those slices (17 per engine).
- Current **194**: **110 ACCEPT / 60 REJECT / 24 UNKNOWN**.
- Frozen **193**: **108 ACCEPT / 61 REJECT / 24 UNKNOWN**.
- Both complete corpora: **0 wrong, 0 errors, 0 regressions, 0 verdict changes**.
- Both app-lam controls pass under an **8 MiB launcher stack**. The checker retains its explicit 64 MiB worker stack and 65,536 judgment fuel; no efficiency ranking is claimed.

This closes valid prerequisites in ten full files, with **zero new final Arena verdicts**.

## Mechanisms

1. **Natural literal constructor view.** At Full exposure only, the already certified Nat recursor may view literal zero as the admitted zero constructor, and a positive literal as admitted successor applied to a computed predecessor. The predecessor has an explicit runtime literal closure, independent of export expression IDs. The existing certified RHS, arity, universe instantiation and pending-application machinery still perform the reduction. Wrong recursors and missing Nat authority do not consume literals. Fuel exhaustion stays UNKNOWN.
2. **Closed data/proof records.** One safe, nonrecursive, nonindexed, nonnested, monomorphic record with two fields: a data type in exactly the record's nonzero universe, then a dependent proposition. Both domains are checked using prior authority, before the record exists. Existing constructor, motive, minor and field-order checks are retained; RHS lambda annotations are also checked. This admits Char without a Char name exception. General two-data-field records remain unsupported by this extension.
3. **Exact Nat.le.below.** Reconstruct the complete indexed Prop family, both constructors, Prop-only dependent motive, minors and both recursor rules. Match bound variables by scope, not exported binder spelling. The sole recursive call consumes the exact recursive field. Prior certified Nat.le computation is required. No K, generic indexed positivity, or large elimination is added.

## Method and distinction

The campaign continues the ROS residual-driven method: first failed declaration, dependency slice, mathematically bounded law, controls and reference replay, then whole-corpus reclosure. The labels of complete Arena files never authorize a rule. The independent reference is lazylean at `68c66fa18c1afe029512b90ecfe0b162c0dcd8fb`, using KAM and substitution engines within that single checker lineage; they are not two independent implementations.

Seventeen extracted valid prefixes are targeted across ten current full files: nine literal-related matcher prefixes, two Char prefixes, six Nat.le.below prefixes. These are external instances of three laws, not seventeen distinct semantic laws. Four matcher prefixes come from expected-REJECT full files; their validity is a separate obligation. Full-file verdicts remain separate from all prefix results.

## Local evidence and lineage

- Four natural-literal machine tests failed before the representation/reduction change; the authority control was already nonreducing.
- The actual magma matcher prefix and Init division matcher prefix each moved UNKNOWN to ACCEPT.
- The Char prefix was initially UNKNOWN. An initial implementation omitted wiring its new preconditions; three targeted tests caught the overly broad acceptance (higher data universe, non-Prop second field, wrong rule annotations). The gates were connected, and all controls passed. That prototype was never promoted.
- Nat.le.below prefix was UNKNOWN before its exact schema, then ACCEPT. Altered metadata and a wrong recursive-field call remain non-ACCEPT.
- Independent review caught and repaired a shared-DAG test mutation that failed too early. See review.md.
- Earlier expression-table predecessor lookup and broad computed-major prototypes remain unpromoted in the prior no-confusion campaign; this revision uses neither hack.

## Residuals after this candidate

The full 24-case residual set still consists of 13 expected ACCEPT and 11 expected REJECT files. The first obstruction advanced in ten:

| Full files | Next first obstruction |
| --- | --- |
| Init, grind-ring-5, magma pair-n7/pair-n21 | Nat.modCore_lt, theorem.value, application-function-type |
| Magma deep-n21/deep-n36 | Option inductive admission |
| Four projection/recursor bug files | WellFounded inductive admission |

The other fourteen first boundaries are unchanged. See frontier/frontier.json for exact file names and input/trace digests. A later boundary is progress through valid prerequisites, not a complete Arena decision.

Large excluded corpora, full Mathlib, and leaderboard instruction/memory ranking are not qualified by this work. No official Arena submission or runtime backstop was added.

## Next decisive experiment — not part of the qualified source

A diagnostic copy traced pair-n7's Nat.modCore_lt mismatch to two local proofs of `0 < y` passed to `Nat.modCore.go._f` beneath a stuck PProd projection and Nat.rec. The current proof-irrelevance helper compares normalized proposition representations by structural equality, including closure environment identity. A bounded prototype that first establishes both types as propositions and then compares those types by conversion advances this one full file from Nat.modCore_lt to Iff admission. This supports a specific next hypothesis; it has **no complete-corpus or independent-reference qualification** and supplies **no warrant for a full-file verdict**. It is preserved only in lineage/proof-type-conversion-unqualified.patch and its log. In particular, delta-policy propagation, recursive conversion budget and negative proof/data controls must be addressed before promotion. The tested candidate e5916cf does not contain this prototype.
