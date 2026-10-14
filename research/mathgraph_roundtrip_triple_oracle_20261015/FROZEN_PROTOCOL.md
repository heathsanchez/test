# Frozen independent-reference replay — 2026-10-15

Objective: test whether the already-discovered, automatically enumerated YAML roundtrip discrepancy candidates survive independent replay and a THIRD implementation oracle. This is NOT a new held-out first discovery or autonomous generator invention.

Prior discovery, not authored here:
- Original immutable experiment and grammar: `mathgraph-roundtrip-unseen-witness-20261014-v1`.
- Existing original CI: https://github.com/heathsanchez/test/actions/runs/38556432200
- Corpus generation: 1088 cases, SHA256 `86b3b2477024dec6cb57b82c3503d472132c5b50f2214bc34aa03afccfc8f2fe`.
- Original source pins: `goccy/go-yaml@72a4f95c648c844ef2f8ddbc009530be64ab4c41` and `go-yaml/yaml@944c86a7d29391925ed6ac33bee98a0516f1287a`.
- Frozen prior native signatures: target 21/1088 failures, reference 15/1088 failures; 16 target-only, 5 shared, 10 reference-only.
- Recorded prior target-only exemplars: `.nan`, `.NaN`, `.NAN`, `.inf`, `-.inf`, CRLF-containing strings. These are no longer blind to us.

New independent oracle chosen BEFORE rerunning: CPython + `PyYAML==6.0.2` `safe_dump`/`safe_load` on the ENTIRE original corpus. No target-dependent expected output, issue-specific assertions, or patch inspection. Evaluate the identical invariant: roundtrip of a map of string values must preserve the exact input string and type. Inspect ALL 1088 cases, not a post hoc curated subset.

Decision procedure (predeclared):
1. Re-run immutable two original Go source revisions and assert identical corpus, original source pins, complete 1088/1088 native observations, and prior case-ID counts.
2. Run the third PyYAML oracle on every case; record type and content, exceptional status, Python and package versions. Preserve actual emitted bytes for all earlier target-only candidates.
3. `CORROBORATED_BOUNDED_STRING_ROUNDTRIP_WITNESSES` only for actual Go target-native failures on old exact source that Go reference and independently implemented PyYAML BOTH preserve, with original input and output type. The result is a library-specific bounded internal consistency witness, not YAML-standard conformance, exploit, general source understanding or reviewer advantage.
4. Third-oracle disagreement / errors become `UNKNOWN_THIRD_ORACLE_CONFLICT`; failures to fully run become `INCOMPLETE`. A ref-removal ablation must withdraw corroboration (`UNKNOWN_REFERENCE_REMOVED`), and source evidence withdrawal `STALE`.
5. Strong baseline: a conventional three-implementation test given the same corpus and code can reproduce the same output. No measured advantage claim. No generalized autonomous test-operation generator, L7, or new customer adoption.

No third-party repository writes, secrets, outreach, product deployments, merges or privileged actions. Run in owned isolated branch only. This protocol is committed before the implementation.
