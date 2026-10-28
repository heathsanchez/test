# Frozen acceptance matrix

These outcomes are hand-derived requirements. No native execution result is claimed. CORE positives must succeed to claim the selected positive grammar; negatives must refuse or remain UNKNOWN at or before the specified boundary. Optional ordering support may be omitted with an explicit UNKNOWN.

| Control | Expected boundary/outcome | Authority |
|---|---|---|
| W01_closed_production_wildcard | ADMIT_THEN_PASS_NATIVE | CORE / wildcard |
| W02_unimported_malformed_python_data | ADMIT_THEN_PASS_NATIVE | CORE / malformed-data |
| W03_collection_imported_malformed_python | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / malformed-import |
| W04_runtime_imported_malformed_python | ADMIT_THEN_FAIL_NATIVE | CORE / malformed-import |
| W05_wildcard_public_function_test | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / wildcard-test |
| W06_wildcard_public_test_class | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / wildcard-test |
| W07_literal_all_test_hiding | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / export-protocol |
| W08_all_getattr_fabricated_export | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / export-protocol |
| W09_getattr_without_all | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / export-protocol |
| W10_reexport_origin | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / origin |
| W11_test_alias_export | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / alias |
| W12_class_alias_export | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / alias |
| W13_wildcard_after_local_shadowing | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / shadowing |
| W14_package_initializer_effect | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / origin |
| W15_export_opaque_call | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / origin |
| B01_same_prefix_literal_rebound | REFUSE_OR_UNKNOWN_NO_ADMISSION | CORE / binding |
| B02_same_prefix_noop_decorator | REFUSE_OR_UNKNOWN_NO_ADMISSION | CORE / binding |
| B03_forged_wrapped_noop | REFUSE_OR_UNKNOWN_NO_ADMISSION | CORE / binding |
| B04_deleted_local_test | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / binding |
| B05_imported_same_prefix_alias | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / binding |
| B06_duplicate_local_definition | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / binding |
| B07_missing_collection_test_false | REFUSE_OR_UNKNOWN_NO_ADMISSION | CORE / missing |
| B08_class_method_rebound | REFUSE_OR_UNKNOWN_NO_ADMISSION | CORE / binding |
| O01_deterministic_order_only_hook | ADMIT_THEN_PASS_NATIVE_IF_ORDER_SUBSET_SUPPORTED | OPTIONAL_ORDER_SUBSET / order |
| O02_entropy_salted_order_hook | REFUSE_UNKNOWN_ORDER_AUTHORITY | CORE / order |
| O03_test_method_prefix_write | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / namespace-write |
| O04_globals_subscript_write | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / namespace-write |
| O05_shadowed_order_target | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / shadowing |
| O06_effectful_comparator | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / order |
| O07_other_attribute_write | REFUSE_UNKNOWN_BEFORE_NATIVE | CORE / namespace-write |

The complete reason and immutable source bytes for each source case are in FIXTURE_INDEX.json and fixtures/.

| Replay control | Required outcome | Authority reused or missing |
|---|---|---|
| R01_stale_source | REFUSE_OR_UNKNOWN_NEVER_PASS | Original exact reconstructed authority/source identity |
| R02_forged_required_set | REFUSE_OR_UNKNOWN_NEVER_PASS | Original exact reconstructed authority |
| R03_forged_export_set | REFUSE_OR_UNKNOWN_NEVER_PASS | NEW independent closed namespace derivation |
| R04_wrong_export_origin | REFUSE_OR_UNKNOWN_NEVER_PASS | NEW origin closure plus inherited import/source checks |
| R05_wrong_declaration_binding | REFUSE_OR_UNKNOWN_NEVER_PASS | NEW independently compiled actual executable binding |
| R06_missing_protected_node | REFUSE_OR_UNKNOWN_NEVER_PASS | Original protected-prefix and independent replay |
| R07_partial_parameter_deselection | REFUSE_OR_UNKNOWN_NEVER_PASS | Original full exact independent collection and no deselection |
| R08_missing_call_report | REFUSE_OR_UNKNOWN_NEVER_PASS | Original strict report sequences and counts |
| R09_skipped_or_xfailed_assertion | REFUSE_OR_UNKNOWN_NEVER_PASS | Original no-skip/no-xfail required execution |
| R10_resealed_receipt | REFUSE_OR_UNKNOWN_NEVER_PASS | Original independent recollection/reexecution; NEW declaration binding |
| R11_environment_replacement | REFUSE_OR_UNKNOWN_NEVER_PASS | Original pinned environment and host identity |
| R12_plugin_replacement | REFUSE_OR_UNKNOWN_NEVER_PASS | Original licensed distribution, content, manifest and replay |
| R13_independent_order_mismatch | REFUSE_OR_UNKNOWN_NEVER_PASS | Original ordered equality, never set-only or sorted equality |
| R14_execution_order_mismatch | REFUSE_OR_UNKNOWN_NEVER_PASS | Original exact report order |
| R15_changed_imported_source | REFUSE_OR_UNKNOWN_NEVER_PASS | NEW namespace revalidation per executable view; no stale source namespace authority |
| R16_missing_namespace_binding | REFUSE_OR_UNKNOWN_NEVER_PASS | NEW exact versioned schema and fail-closed bridge |
| R17_candidate_test_or_config_edit | REFUSE_OR_UNKNOWN_NEVER_PASS | Original production-only candidate grammar and external authority |
| R18_observed_code_changes_after_collection | REFUSE_OR_UNKNOWN_NEVER_PASS | Original code-change check plus NEW outer callable check |
