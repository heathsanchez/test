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
- [x] Capture failed typed comparisons with expression, frame, context, expected/inferred types, policy, budget; capture masked application failures and unsupported inductive shape. Explicitly bound traces.
- [x] Replay all 387 tests in normal and diagnostic builds against base. Retain full traces for all24 current UNKNOWNs and input hashes.
- [x] Build evidence-scoped candidate paths; do not infer a missing law solely from a terminal reason. Require explicit unresolved bucket.
- [x] Review, preserve run/artifact evidence and update ROS.

## Rulings and ledger
- Offline Python replaces historical Rust planning module: smaller separation from verdict production, locally executable planner tests; cost is maintaining the diagnostic adapter boundary.
- Historical planner loses candidate lineage when derived interfaces are inserted into the seed set. New planner retains support sets throughout closure.
- RED: eight tests ran, five intended failures against no-path stub; GREEN: eight pass.

- Review Important fixed: missing terminal boundary no longer attaches preceding declarations' events to the terminal object. Reproducer RED (mixed scopes under terminal) → GREEN; full Python suite12pass1skip.
- Review coverage fixes: CI includes report tests; real capture test requires terminal-scope comparison.
- Registry scope: three qualified contracts are explicitly bound but this adapter does not manufacture their validated-premise witnesses; NO_REGISTERED_PATH is not global saturation or proof that a law is absent.

- Added measured existing-recursor-shape adapter; candidate composition now requires its actual successful observation. Missing/false probes RED→GREEN in Python.
- Blanket direct-reuse hypothesis rejected by run36819075234, at36949b; preserve this as semantic applicability evidence, not a harness defect or checker verdict regression.
- Second review Important: cardinality alone did not bound diagnostic expression traversal. Added conservative occurrence/depth preflight with explicit incomplete event; tiny benign shared-node tests cover work/depth separately.
- Direct pinned source inspection: SourceInfo.synthetic field3 uses optParam Bool false while its recursor minor uses Bool. Hosted stage marker pending.

- FINAL: b7d7baebf8485122fe02afe2e8d910189551cfe2 run36819395684 SUCCESS; artifact11142848175 SHA256d90f37ba8642bf936a460a715f1bc0dfd048963cebf68adc386cc6de38104676.387 exact three-build verdict identities;24 complete terminal scopes;3 candidate paths and21 no registered paths. Existing recursor check passes Option/Except, fails SourceInfo stage14.
