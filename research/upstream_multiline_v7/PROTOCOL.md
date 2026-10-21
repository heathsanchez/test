# V7 prospective independent upstream multiline source transformation

Frozen 2026-10-22 before reading target implementation.
Independent upstream repository: pallets/itsdangerous, commit 672971d66a2ef9f85151e53283113f33d642dabd (2025-06-14). Metadata listing verified src/itsdangerous/encoding.py exists. Do not choose another file or change project after outcome.

## Source-selection algorithm frozen before exposure
Use AST to locate the first *module-level synchronous function*, in source-order, whose last top-level statement is a Return with a nonempty value. Reject any method, nested function, async function, function containing yield/await, reference to reserved variable _mg_retained_result_v7, dynamic self-inspection locals/vars/eval/exec, and any expression not safely reprinted as its exact original source span. Support multi-line return expressions by preserving original expression text and replacing the entire return statement with an assignment to reserved local and a subsequent return of that local. Do not change protected tests, function call signature or other source. If no eligible function, UNKNOWN. This grammar is human-designed after MarkupSafe exposure, not automatically learned.

## Native controls
Run full authentic upstream pytest suite on pinned unchanged commit before change, then after ephemeral source change. Run an alternate deliberate wrong-output mutation of *exact target function* if safe to inject; require that a native test or focused independently sourced target call detects it. If native tests cannot run because of absent external dependency, record environment UNKNOWN rather than fabricate pass.
The extra assignment may be observable through tracing, profiling, locals() and frame introspection. Exact source change and finite regression DO NOT prove universal observational equivalence. Do not claim so.

## Test-selection baseline
Inspect authentic tests and package import graph; conservatively keep any test importing it/dynamically loading it or with unresolved effects. Independent conventional dependency-aware test selector gets same source and may keep all. Safe omission requires independently closed boundary beyond importing itdangerous; otherwise 0 authentic skips. Compare with the original full suite. Charge all baseline, mutation, qualifier tests and setup in the receipt. No product release authorization or GitHub Check integration.

## Scope
Second external upstream source family versus MarkupSafe V6; prospective file/source code unseen at freeze, project itself previously known. No R7.2/CLC/MathGraph modifications or cross-kind formal adapter. Stop on unsupported source, tests, bad mutation inapplicable; preserve negatives. Research-only, no upstream PR.
