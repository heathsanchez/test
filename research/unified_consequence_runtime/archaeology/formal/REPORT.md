# Formal and native verifier source archaeology

Read-only source review. The local kernel and arena clones contain complete reachable branch and commit inventories, saved in `mathgraph-lean-kernel.history.json` and `lean-kernel-arena.history.json`. `INDEX.json` records pins and unknowns.

The MathGraph Lean kernel README describes an experimental Lean 4 proof checker in the nanoda/sokonanoda lineage, used for soundness and differential testing. The Arena `mathgraph-latest-draft` source (`0c3d0b75675249dce4682270a6c554cfa3fa11f5`) binds checker `78c7502bac8a5ba000057b3f083bc0595ac65750`. It expressly disclaims independent rewrite. Its runtime config uses `unsafe_permit_all_axioms=true` and `unpermitted_axiom_hard_error=false`; checker acceptance therefore does not mean absence of assumptions.

`VerifiedDevelopmentalNavigation/DevelopmentCertificate.lean` has not yet been read locally, and its assumptions remain UNKNOWN pending exact source. No concrete VDN/MSI Lean instance for the integrated Python runtime is established. Original workflow artifacts have not been inspected in this subtask; branch names, prose or green workflow status are not substituted for artifact outcomes.

A combined environment-status/network clone call blocked until user cancellation (2525.8 seconds). No clone was produced. Subsequent work uses local repositories only.

## Distinct native implementations

Arena `mathgraph-arena-submission-v1@debbf137a0470707226e16c87a36364309a4e97f` contains a separate self-contained JavaScript checker, derived from the `genesis` development line. Its source excludes developmental search from the checking path; the frozen entrypoint uses 23 capability names and budget 1,000,000. Exit statuses are ACCEPT 0, REJECT 1, DECLINE 2 and runtime error 3. Its source README explicitly distinguishes finite supplied-rule selection from autonomous program synthesis, and says finite tests do not prove soundness. This JS implementation is distinct from the Rust Flash derivative, and neither is identified with the MathGraph Check web application merely because of its name.

The serial research composition document at `metalogiclabs/mathgraph-lean-kernel@66b9c4a1d1c30c938f8ac40fdf70cbd629b19bc8:docs/arena-serial-warrant-v1.md` binds Soko `7645b1e1fcacfe410c99141f1234381d995b325d` and Flash `78c7502bac8a5ba000057b3f083bc0595ac65750`. Its correctness statement is conditional on both constituent checkers' sound decisions. It records a portable 196-case test claim, excluding nine large valid exports. No original artifact has been opened here, so those outcome counts remain documentary evidence rather than this audit's verified replay.

## Exact MSI assumptions cross-check

Seven original Lean files from `heathsanchez/Minimal-Sufficient-Interface@5d448c0ecc82ff3945d009963064ebbb67d2f308` are saved under `sources/`, with Git blob IDs and SHA256 in `INDEX.json`. The formal runtime map is `/workspace/udm/research/unified_consequence_runtime/FORMAL_CORRESPONDENCE.md`. Direct source checks establish the explicit monoid/category/action laws; universal future quantifiers; complete finite action cover and genuine refinement progress for finite recovery; fixed ambient category for developmental stage extension; genuine collision/separation witness for residual repair; and idempotent/commutative/associative meet for least-change repair. Source withdrawal is provenance recomputation above the meet kernel: `update_cannot_coarsen` rules out genuine retraction by monotone meet update alone.

The full MathGraph remote branch list supplied by the root is now included in `INDEX.json`. Exact VDN file path resolved documentarily to `verified-developmental-navigation/lean/VerifiedDevelopmentalNavigation/DevelopmentCertificate.lean`, with historical authority pin `e80fed62b6e58d2f4b62e2ceb012646c60dd1e28`; source bytes still pending.
