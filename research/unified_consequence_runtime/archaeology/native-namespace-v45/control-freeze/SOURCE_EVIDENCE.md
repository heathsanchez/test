# Original source evidence

All paths below are relative to `research/unified_consequence_runtime/` at base commit `88aa5090c310d2f75683a019a5bc958cdb3b576e`. Exact file SHA256 values are retained in SOURCE_PINS.json. This review used source reads only; statements about existing controls describe their actual assertions, not a fresh test run.

| Obligation | Original evidence | Scope actually supplied |
|---|---|---|
| Immutable source/configuration/author delta | `native_admission_v2.py:501` `derive_suite_contract`, `:574` `validate_suite_contract` | Independent Git snapshot; only original test overlay; full equality to reconstructed authority; changed test-source hashes and required prefixes. |
| Typed source kinds and candidate restrictions | `native_admission_v42.py:29` `_snapshot`, `:50` `derive_suite_contract`, `:69` `validate_candidate` | Authenticated V42 source kinds and source-only test deltas; original candidate grammar reused. |
| Configured class/unittest inheritance routes | `native_admission_v2.py:204` `_class_test_nodes` | Source-local C3-style base mapping, declarations and actual collection route prefixes. The function can return origin/declaration information; existing output authority does not expose executable declaration binding. |
| Dynamic namespace refusal | `native_admission_v2.py:382` `targets`, `:423` `visit` | Every attribute/subscript assignment is refused. Test aliases/deletions/duplicate definitions and registration primitives are conservatively refused. There is no ordering-hook authority. |
| Wildcard refusal | `native_admission_v2.py:455` import branch | Every wildcard import is refused. It does not resolve origin/export namespace, including safe production wildcard imports. |
| Authority precedes native collection | `native_execution_v2.py:151` `_context`, especially `:167` | Source-derived suite authority validates before `_run`; successful collection cannot bootstrap its own deleted-assertion authority. |
| Observed object code identity | `native_execution_v2.py:77` child `code_hash`, `:108` `pytest_itemcollected`, `:120` `pytest_runtest_call` | Records observed object code and checks its observed hash did not change before call. `code_hash` explicitly follows `__wrapped__` before hashing. It does not independently compare original declaration code to actual outer callable. |
| Exact collection/no deselection | `native_execution_v2.py:234` `_collection` | Nonempty unique collected/selected node sets; no deselection/errors; actual item source hash; each required prefix represented. It does not assert one item per node nor independently authenticate source-declaration code against the observed item. |
| Independent replay and order | `native_execution_v2.py:271` `validate_certificate` | Packet/source/policy/environment binding and fresh independent original collection, including ordered lists and observed item hashes. Reproducing a consistently wrong executable still does not prove the changed declaration was called. |
| Required execution | `native_execution_v2.py:306` `_status` | Exact observed suite/items/plugin manifest and required setup/call/teardown ordered sequences, counts, no skip/xfail. Native PASS/FAIL only under those constraints. |
| Receipt reconstruction | `native_execution_v2.py:357` `validate_receipt` | Exact bound source/candidate/authority/certificate identity; independent reexecution for caller-supplied evidence. |
| Runtime and immutable verifier lineage | `native_execution_v3.py:25` pins and `:137` environment identity; `native_execution_v42.py:25` dependencies and `:43` private controller globals | Original verifier pins and runtime/stdlib binding, private versioned adapters. |
| V43 generated source transport | `native_execution_v43.py:93` `_context`, `:110` `_validate_generated` | Existing build evidence/source authority maintained separately, source/exec views checked. It currently delegates assertion validation to previous source authority. |

## Existing meaningful control assertions to preserve

| Original test | Demonstrated control intention |
|---|---|
| `test_native_admission_v2_adversarial.py:118` `test_original_fixture_reorder_binds_collection_and_final_execution_orders` | A lawful original collection hook reverses selected order while preserving collected order and full original parameter cases. |
| `test_native_admission_v2_adversarial.py:142` `test_candidate_cannot_change_original_fixture_order_or_discard_collected_nodes` | Same counts with changed order or discarded item yield UNKNOWN_EXACT_COLLECTION. |
| `test_native_admission_v2_adversarial.py:162` `test_candidate_cannot_shrink_or_expand_cases_behind_same_static_prefix` | Static prefixes do not license different parameter cases. |
| `test_native_admission_v2_adversarial.py:174` and `:180` skip/xfail controls | Required tests cannot hide behind module skips or xfail/xpass. |
| `test_native_admission_v2_adversarial.py:269`, `:281`, `:296` plugin controls | Original plugin declarations require a separate distribution license; exact licensed plugin can execute; candidate plugin registration does not gain authority. |
| `test_native_admission_v2_adversarial.py:321`, `:381`, `:394` packet/schema controls | Forged costs, changed policy, extra/missing authority fields are rejected. |
| `test_native_admission_v2_adversarial.py:536` `test_resealed_wrong_import_source_is_not_authenticated_by_equal_pass_counts` | Equal passing counts and recomputed public hashes cannot authenticate wrong imports against independent reexecution. |
| `test_native_execution_v3.py:339`, `:359`, `:364` | Selected order retained; `__test__ = False` missing node refused; code changed after collection refused. |
| `test_native_authority_v4.py:185`, `:208`, `:217`, `:225` | Malformed unimported Python bytes can remain data; same bytes actually imported fail at native runtime or collection as appropriate. |
| `test_native_suite_authority.py:100`, `:129` and `:137` | Forged required set/source/config/protocol authority and altered runtime authority/receipt rejected. |

## Missing authority, stated narrowly

The original static authority has neither a checked wildcard namespace/export closure nor an allowed ordering-only write grammar. The original collector also lacks an independent source-declaration-to-actual-outer-executable binding. Source hashes plus required prefixes plus stable independent observed code hashes do not exclude an initially rebound assertion, especially a no-op wrapper with forged `__wrapped__`.

The minimum extension can add that missing source-local namespace and executable binding in new versioned files, then reuse original exact native collection/replay and execution assertions. There is no need for a new scientific framework, solver, learner, candidate search algorithm, order equivalence relation or generic dynamic namespace permission.

The prior report and diagnostic residual in `archaeology/native-bootstrap-v44/prospective-result/` establish the two exposed refusals and warrant ceiling. They do not grant permission to execute the exposed tasks or prove pycparser's entire runtime export namespace from a read-only source observation.
