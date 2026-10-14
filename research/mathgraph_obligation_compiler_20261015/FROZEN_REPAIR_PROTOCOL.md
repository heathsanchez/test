# FROZEN REPAIR-GENESIS PROTOCOL — 2026-10-15

**State: CANDIDATE; no repair experiment executed at freeze.** The previously frozen [FROZEN_PROTOCOL.md](FROZEN_PROTOCOL.md), same original source families and exact source SHAs, and green [observer-run #38609390264](https://github.com/heathsanchez/test/actions/runs/38609390264) are the only developmental evidence. The contributor HEAD source patch and author regression test content have NOT been consulted for generating these transformations. PR titles/descriptions and original base implementation have been read; this is NOT blind patch invention.

## Proposed two generic candidate transforms, not per-target patches

1. **Error atomicity by guarded expression movement**. If a changed mutable-mapping insertion method has a scoped clock context and a later arithmetic deadline assignment executed AFTER mutating cache state, generate a new local binding that computes the expression at the start of the context, then replace the later assignment value with the previously computed binding. Use Python AST identity and source spans; do not match any repository/class-specific symbol or literal. Verify that the expression depends only on values available at the proposed insertion site, not on mutated state. If preconditions fail, return typed UNKNOWN rather than textual replace.
2. **Variadic iterable flattening**. If a changed method with documented iterable *args passes the collection of iterables to an imported flattening/chain call that only traverses its immediate inputs, generate a candidate from an available flatten-one-level primitive, not from a copied upstream patch. Require exactly one unambiguous target AST node, type and source binding; do not hardcode class/method names. If the candidate fails native observation or source qualification, preserve it REJECTED.

Both transforms are HUMAN-DESIGNED constructor families. Only their actual patch *instances* are constructed automatically from original source. They do NOT count as autonomous novel generator-language invention (L7).

## Native source verification boundary

- Clone original base/head at exact identities and verify HEAD on clean original trees. Keep original baseline unchanged and original author head read-only.
- Apply one syntactically minimal patch to an EPHEMERAL base checkout only. Store unified diff and resulting SHA256. Never write patches to original third-party GitHub repositories.
- Execute same prequalified source-derived observation program against original base (must fail), generated patch (must pass), and contributor head (must pass).
- Execute original repo's targeted native test suite on patched base, including inherited tests (do not copy author-head tests). Confirm original base original test suite was green.
- Actually undo patch and execute the same failing native observation again (must fail), then restore ephemeral patch to show identical digest.
- Execute actual probe deletion without any observer call; status must be UNKNOWN_NO_OBSERVATION rather than treating Python exit 0 as semantics.
- Source mismatch / unavailable original / stale reference must fail closed; verify original exact SHAs and patched SHA256.
- Do not claim adequate repair beyond tests and declared input grammar; no independent strong coding-agent comparison has been run.

## Stop rules

Any unsupported source structure, nonunique candidate, failed compile/test, failed ablation, inherited suite failure or ambiguous normative contract leaves CANDIDATE/REJECTED/UNKNOWN, never warrant. A successful pair earns only WARRANTED_BOUNDED_HUMAN_GRAMMAR_REPAIR_CONSTRUCTION in two historical libraries, not L7 or generalized autonomous PR repair. Retain failures and costs.

No upstream writes, merges, installs, production deployment, Gmail, Render, external outreach or policy changes.
