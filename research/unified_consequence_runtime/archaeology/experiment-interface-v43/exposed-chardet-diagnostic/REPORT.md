# Exposed chardet V43 diagnostic

**DIAGNOSTIC_ONLY_NOT_PROSPECTIVE. G2/G3 remain UNKNOWN.** Final production V43 operations cleared the previously exposed generated-import obstruction. Complete native admission remains UNKNOWN because the original accuracy tests then attempted to acquire an external, unpinned test-data repository and its clone failed. No repair, constructor, source workaround, test deselection or subsequent fetch/retry was performed.

The existing cached case was reused without external source acquisition: `chardet/chardet` PR 368, original base `ea7e547aa5197c32b9a4c0f8e2b0f97f071aef6c`, independently authored test-only augmentation `c133dbdacfe5d4470289f6c46c4ad0452834c2b4`. Both inventories contain 114 readable files. The original V42 setup was PREPARED but collection had 34 errors. The diagnostic derived a separate V43 authority/protocol, `dfe92c3939f81e1eb21c189145e39dcb65206fcbc585316d366bab90565cd25b`, retaining all 90 protected assertion prefixes and the exact original environment, six licensed plugins, 60-second collection limit and 600-second execution ceiling.

Actual `developmental_machine_v43.Machine` loaded the retained Metatron and FLASH components. The unresolved materialization obligation was registered before instrument admission. Actual `MaterializationRuntime.admit` executed original base preparation and an independent rebuild, then actual `Machine.select_and_execute_frontier` activated the retained operation and repeated preparation/independent verification. The native collector independently authenticated another build before launching pytest. Metatron/FLASH closure agreed; the new Machine retained eight records and only the materialization operation as an executable capability. No native pytest capability was admitted.

The admitted `src/chardet/_version.py` is 558 bytes, SHA256 `65de830ef24719bc053dfe3334f40eef851fd7aa25e4a29f27b618c2ffd68a08`. Its bytes exactly match the retained original V42 base-build output. The complete normalized wheel content also matches the retained original wheel: SHA256 `999c6708322ea732c67276a7e925d447b1355817a87d2180f8f80e918dacead1` on both sides. The native import manifest records that exact generated file. Source mutations, unexpected imports, external project imports and plugin violations were all empty.

The unchanged native collector found and selected **1,758 nodes, with zero deselection**, then returned exit 2 on exactly one collection error: `tests/test_accuracy.py`. Its original `_make_params` calls `scripts/utils.py:get_data_dir`, which invokes `_clone_test_data` and `_git_clone_shallow`.

The original helper declares `https://github.com/chardet/test-data.git`. Its ref is derived from chardet's version. The actual original generated version is `7.4.2.dev1+gea7e547aa`; because it contains `.dev`, the helper returns `None` and clones the remote default branch without an immutable commit pin. Its cache label is `main`. For release versions it instead tries a version-named tag/branch, with fallback to the default branch on failure. A preexisting `tests/data` symlink bypasses that behavior, but no such substitution was introduced here.

The exact observed command was:

```text
git clone --depth=1 https://github.com/chardet/test-data.git /tmp/tmp52o870nf
```

It returned 128. The clone's stderr bytes are **UNKNOWN_NOT_RETAINED**: the original helper uses `capture_output=True`, then its uncaught `CalledProcessError` reaches pytest's collection report without serializing those captured bytes. The native worker's retained stderr is empty. No cause was invented and no retry was used to recover different stderr.

Because collection did not issue a valid admission certificate, protected assertion execution and independent native reexecution were NOT_RUN. There was one actual collection launch and zero native execution launches. The operation's import success is diagnostic evidence, not a complete-suite native warrant or prospective growth result.

Five actual V43 wheel builds used the exact frozen interpreter and original base ancestry/30 ancestor tags, with 170 retained build commands. Actual pip-wheel time was 2.327914739 seconds. The collector's own measured worker time was 6.347742001 seconds. The diagnostic driver took 100.163304767 seconds, within its 1,200-second ceiling; the separate availability preflight took 5.335975600 seconds. Detailed build/phase timings are nested and must not be added to enclosing wall times. `COST_STORAGE_SUMMARY.json`, `machine-costs.json`, the build receipts, full phase stdout/stderr, raw collection reports, original source materializations, wheels and Machine state remain in this directory.

The preservation check compared **216 existing source/result/build files** before and after and found exact byte equality. The five production V43 modules checked before/after retain their exact source hashes in `PRODUCTION_SOURCE_PRESERVATION.json`. No root/component index, production library, original source/test/result or frozen qualification file was edited. A diagnostic-driver import-path apparatus failure was retained as `run-001-import-*.log`; changing its invocation to `runpy.run_path` affected no production source and performed no build/native launch.

Primary evidence: `PREFLIGHT.json`, `RESULT.json` (raw driver outcome), `DIAGNOSTIC_FINDINGS.json` (derived interpretation), `COLLECTION_SUMMARY.json`, `TEST_DATA_AUTHORITY_BOUNDARY.json`, `OLD_BYTES_BEFORE.json`, `OLD_BYTES_AFTER.json`, and `collection-v43/{report.json,checked-report.json,stdout.log,stderr.log,native.xml}`.

The successful driver invocation was:

```text
env GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 /workspace/qualification/native-authority-v42-controller/bin/python -B -c "import runpy; runpy.run_path('/workspace/qualification/experiment-interface-v43-exposed-chardet-diagnostic/run_diagnostic.py', run_name='__main__')"
```

This diagnostic does not bypass or replace the final whole-interface qualification gate. It establishes that the generic generated-import operation works on this exposed upstream package and identifies the next original-fixture authority boundary without changing it.
