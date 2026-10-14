# Frozen test: source-derived missing-obligation discovery, 2026-10-15

## Objective and authority
Determine whether a generic source-analysis + independent-native-differential procedure can *discover a verification obligation absent from a human-authored per-target manifest*, construct a concrete witness, and check whether an independently maintained contributor revision resolves it. Research-only, not MathGraph Check production. This is an intentionally bounded first test, not universal semantic invention.

## Independent original source
Third source family relative to earlier OPA/gojq work: `simplejson/simplejson`, pull request `#379`, author head `9504252b2fcc3be36dc2719ebdfa32419ac2339b`; historical predecessor is obtained exclusively as the parent of that pinned PR head (verify parent count, exact commit, and source snapshots in CI). Read-only upstream original. We know the PR title concerns a control-character error location; this is a **partially disclosed, retrospective** case, not blinded prospective discovery. Do not inspect author patch/tests before freezing generator code.

## Frozen gate
1. Independently build the historical **pre-fix** and author **fixed** source under the same native Python/C runtime; preserve exact full commit identities and observed native outputs.
2. From the **pre-fix source itself**, *without an operation-specific manifest*, discover candidate distinct implementations of the same interface using a generic, stable naming/structure rule. The mining code may recognize generic `py_` and `c_` naming conventions but MUST NOT contain any target-specific function name (including scanstring), expected input, correct output, special-case target fix or PR-specific instruction.
3. Generate arguments from one fixed, operation-agnostic finite typed input vocabulary and plausible argument positions; run the pre-fix pairs, classify values / errors / timeouts / unsupported accurately, preserve UNKNOWN.
4. **Before evaluating the patch head**, freeze the complete generator source and its witness manifest (including exact input and discovered operation). Measure at least one genuine pre-fix divergence. Then independently replay the exact witnesses on original contributor head. Only pre-selected witnesses count; ignore post-hoc newly chosen inputs.
5. Run unchanged explicit agreeing controls, eliminate spurious type-equality, report candidate/unsupported cases. Check a no-reference ablation returns UNKNOWN, and a modified input/source identity cannot be promoted.
6. Equal-information conventional exhaustive pairwise differential tester is a strong comparator: do not claim superiority if it can reproduce the same witnesses; record execution costs and selection costs separately.
7. At least one second, distinct untouched repo/family success (not another variant of #379) is required before general transferable method promotion. True reviewer decision/time advantage and production customer adoption require separate blinded tests.

## Acceptance vocabulary
- PASS_SCOPED: operation inferred automatically from pre-fix source (no per-target manifest), exact old native difference, head closure on **the identical frozen witness**, negative controls, restart/lineage guard, all retained.
- FAIL: no stable operation/witness, old and head tie, no actual C build, method leaks target name/answer or red-green was sourced from author tests.
- UNKNOWN: timeout, missing reference or environment, unsupported typed comparison. No guessed witness or semantic correctness certification.
- No automatic code edits, merge authority, installations, upstream messages, PR comments, external writes, Render, Gmail, deployment, grants or outreach.

## Precommitted report fields
source_pins, discovery_rule, operations_discovered, operation_selection_origin, candidate_count, divergent_pre_fix, first_witness, fixed_head_same_witness, agreement_controls, unknown_count, baseline_equal_information, runtime_sec, no_reference_result, final_epistemic_status.

## Important limit
A repaired previously disclosed regression is not a newly discovered upstream defect. Native C-vs-Python parity is not an independent proof of developer intent. Even a successful result remains within a human-designed implementation-pair grammar; L7 autonomous generator-of-generators and measurable superiority remain UNKNOWN.
