# Causal contract paths implementation plan

> **For agentic workers:** Use superpowers:executing-plans. Execution authorized inline by the user.

**Goal:** Recover reusable capability paths from current Nucleus residuals without granting new semantic authority.
**Architecture:** Feature-gated Rust evidence capture; offline Python support-preserving contract closure over one pinned declaration at a time. The historical contract graph is design lineage, not an authority registry to copy.
**Tech Stack:** Rust, Python standard library, pinned GitHub Actions corpus replay.
**Spec:** User-approved Crystal audit recorded in ROS Canonical Research State, 2026-10-01.

## Global constraints
- Base executable 0659bc671a4ef536ed4a096deacd0c61b1ca927e; branch starts at docs descendant c5fc72f06152803225db77df39dbef1875d2a3d6.
- No checker backstop, semantic change, submission or merge.
- Current194 and frozen193 verdict identity required against exact base, normal and diagnostic builds.
- Shape observations never count as validated premises. Missing evidence remains unresolved.
- Resource and semantic preservation cannot be interchanged.

## Review focus
Candidate-taint loss; shared-path double counting; cross-object evidence; bounded trace truncation; speculative failures mistaken for the final cause.

## Tasks
- [x] Write and run offline planner tests: candidate propagation, shared support, order independence, preservation, cycles, observed versus validated, duplicate IDs, bounded search.
- [x] Implement subset-minimal support closure; run all eight tests.
- [ ] Capture failed typed comparisons with expression, frame, context, expected/inferred types, policy, budget; capture masked application failures and unsupported inductive shape. Explicitly bound traces.
- [ ] Replay all 387 tests in normal and diagnostic builds against base. Retain full traces for all24 current UNKNOWNs and input hashes.
- [ ] Build evidence-scoped candidate paths; do not infer a missing law solely from a terminal reason. Require explicit unresolved bucket.
- [ ] Review, preserve run/artifact evidence and update ROS.

## Rulings and ledger
- Offline Python replaces historical Rust planning module: smaller separation from verdict production, locally executable planner tests; cost is maintaining the diagnostic adapter boundary.
- Historical planner loses candidate lineage when derived interfaces are inserted into the seed set. New planner retains support sets throughout closure.
- RED: eight tests ran, five intended failures against no-path stub; GREEN: eight pass.
