# Programme closure implementation plan

Goal: activate recovered source-native observation and construction mechanisms
inside the qualified UDM, with actual multi-frontier propagation and restart.

Spec: PROGRAMME_CLOSURE_PROTOCOL.md and the user's complete-runtime mission.
Architecture: retain Machine, Metatron and FLASH; source-pinned typed adapters
invoke original algorithms and domain-native verifiers. Additional FLASH views
are reconstructible projections of the same log, never new authorities.

## Tasks and ownership

- [x] Verify isolated continuation branch and 91-test clean baseline.
- [x] Source coverage: resumable paginated metadata, historical blob signatures,
  exact result/artifact inspection and explicit coverage gaps. Owner source_coverage.
- [x] ROS/papers: original sources, primary archives, paper access limitations,
  formal assumptions and negative records. Owner papers_ros.
- [x] Native observation: native_observation.py and preparation helper; original
  FLASH constructor, independent audit, executable admission/replay/controls.
  Owner observation_recovery; only these implementation files.
- [x] Cross-frontier: cross_frontier.py and tests; registration/publication,
  original FlashClosure derived from one log, exact support cuts and restoration.
  Owner cross_frontier; root owns Machine hook.
- [x] Native construction: native_constructor.py and tests; original AST observer
  and repair compiler, executed candidate code, independent native qualification.
  Owner constructor_recovery; only these implementation files.
- [x] Root integration: one qualification entrypoint and workflow, native controls,
  choice/UNKNOWN preservation, informed comparison, persistence and restart.
- [x] Independent review: source-level review of actual diff and archived packet;
  address consequential findings, commit source, run branch-only Actions.
- [x] Reconcile one capability index/graph, formal correspondence and ROS-ready
  report with separate bounded verdicts and exact green receipts or obstruction.

## Shared interfaces and review focus

NativeObservationRuntime(machine, source_repo, worlds, output) provides observe,
acquire, execute, withdraw and restore using existing Capability records. Native
constructor adapter provides equivalent scoped operations over original native
collection sources. Cross-frontier helpers register obligations, publish live
independently checked capability routes, recompute and require live routes.

Original E/D selectors must skip unrelated typed scopes. Source hashes and native
receipts must be bound to actual executable bytes. Withdrawal must invalidate
routes before execution. Ambiguous/evidence-incomplete profiles retain candidates.
Persisted derived caches cannot overrule the log. Existing state inputs must not
be mutated. Supplied grammar/target exposure and native verification boundaries
must remain explicit in every report.

No file ownership conflicts: adapters have separate modules/tests; root alone
edits Machine, workflow, end-to-end qualifier and canonical index. Root will
reconcile shared interfaces before execution and request independent diff review.
