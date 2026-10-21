# V43 native transport implementation evidence

The versioned native transport is implemented in `research/unified_consequence_runtime/native_execution_v43.py`. Its current SHA256 is `7d449419909c94ce6186d984545ce218c15ee97dc407104bd4e903180c564827`. It statically pins the final builder SHA256 `20f88ce36baa7e01c7e601c7840f72b9423a6ab04d093d35e36217d3049b8460` and the original V42 worker SHA256 `da4a4b19a988145d690a288b7714cd1f6d2a24f021811059de679e6c2b585d53`.

The tests below were run before the builder's separately frozen requirements-metadata correction. The worker's final change afterward only replaced the temporary builder digest with the final static digest. Final combined qualification under the final dependency hashes remains the root qualification driver's responsibility; no final-hash full runtime run is claimed here yet.

## Preserved authority

- The V43 contract has the actual original eleven fields plus explicit `generated_build`; `None` preserves tracked-only execution. The suite authority remains V42.
- `_roots`, `_collection`, `_binding`, `collect`, `_status`, and `verify` retain the original V2 code objects in private globals. The original certificate and receipt validator code objects remain available as `_controller_validate_certificate` and `_controller_validate_receipt`; their public V43 wrappers add separately validated build accounting.
- V42 validates the original contract projection, tracked source, environment, plugin policy and assertions. `ExecutableView` retains its original typed `SourceFiles` and manifest separately. Candidate grammar and project roots use only original tracked source. Receipt import checks see the same explicitly authorized generated view as execution.
- Every native collection/execution launch independently calls the builder's `verify`, retains its actual artifacts and receipt, then materializes original typed source plus the exact declared generated set. Generated leaf type, mode, inode, link count and bytes, and every generated ancestor directory's type, mode and inode, are checked after execution.
- A raw pytest plugin manifest entry for a generated module causes `UNKNOWN_SOURCE_OR_IMPORT_IDENTITY` before a collection or native-success warrant. Generated imports confer no plugin license.
- Original native packet names and strict native-cost dictionary schemas remain unchanged. Native timing starts after independent rebuild; outer elapsed time and build sidecars separately retain the rebuild work.

## Recorded runs

| Run | Actual result | Evidence |
| --- | --- | --- |
| Initial four focused native acceptance cases | 4 passed, 16 deselected, 7.92s | Tool output; tracked-only/schema behavior |
| Full immutable native V43 acceptance suite | 20 passed, 286.66s | `frozen-pytest-retry.xml`, complete `frozen-pytest-retry/` fixtures |
| Original adversarial methods privately rebound to V43 | 27 passed, 155.656s | `inherited-adversarial-retry.log`, exact `inherited_adversarial.py` runner |
| Additional real-backend native/accounting controls | 11 controls passed | `supplementary.py`, `supplementary-results.json`, complete `supplementary-fixtures/` |
| Final static dependency guard and algorithm identity | Passed | Current import checked both static source digests and original controller code identity |
| New reproducible postimplementation test module | 11 cases collected | `test_native_execution_controls_v43.py`; no runtime result under final hashes claimed yet |

The additional eleven controls cover honest native execution, missing build record, missing sidecar, an unchanged accounting clone, consistently forged zero build calls, recipe and counter claims, generated file mode mutation, generated parent alias mutation, actual generated-module pytest registration, and fresh independent receipt replay accounting. The actual local supplementary process recorded sixteen build calls (four preparations and twelve independent verifications), 7.103713114999891 seconds inside native wheel build commands, and twelve worker launches (eight collections and four executions). Full verification wall time is retained separately in each record; those wheel seconds do not represent all acquisition or environment-check costs.

The original 27 statements were executed with unchanged test method code objects and explicit dependency bindings; this is a V43 binding witness, not a relabeling of an old V42 run. That initial local runner retained its exact source and unittest log but allowed the original fixture cleanup to delete temporary case evidence, so its native packets cannot be independently artifact-audited. The new repository runner `native_inherited_controls_v43.py` reproduces the binding and archives its exact source, exact original test source, per-method source SHA256 values, worker digest, fixture adapters, result, invocation snapshots, and complete case trees before original temporary cleanup.

The supplementary repository file is explicitly postimplementation validation. Neither it nor the inherited runner is represented as part of the initial `2c23ade6` preimplementation acceptance freeze. The original frozen test files were not edited.

## Engineering negatives retained

The first full-suite invocation supplied a pytest basetemp whose parent did not yet exist: one case passed and nineteen fixture setups failed before worker behavior. The retry created the parent and retained the successful full fixture tree. The first inherited runner used a host interpreter without pytest and failed `setUpClass` with zero test cases; `inherited-adversarial.log` retains that error. The unchanged statements passed when run with the frozen modern interpreter. These are qualification harness errors, not native scientific outcomes.

## Accounting and portability boundary

`build_snapshot()` retains every independent verification attempt, refusal and actual builder attempt snapshots. Every attempted generated native launch writes `generated-build-verification.json`; the builder retains successful and failed build receipts underneath `generated-build-verification/`. The public receipt wrapper checks exact accounting fields, source/evidence/recipe/builder bindings, actual positive build-call/counter deltas, and equality with retained verification and build sidecars. Independent replay returns a fresh `independent_build_accounting` addendum with its own actual calls and records.

These timings and sidecars are controller-local measurements, not signatures or hostile-host attestations. Full budget authority must use independently audited local attempt snapshots, all retained sidecars and outer elapsed time. This report does not close G4. Historical absolute sidecar paths are required for receipt accounting validation; a separate process on the same filesystem can replay them, while relocation from CAS plus the native packet and original wheel alone remains UNKNOWN unless those paths are restored.

The original trusted-test/licensed-plugin execution ceiling remains in force, with external enforcement `UNKNOWN_NONBYPASSABILITY`. No new scientific task, foreign future, production effect, constructor algorithm or discovery algorithm was inspected or claimed by this task.
