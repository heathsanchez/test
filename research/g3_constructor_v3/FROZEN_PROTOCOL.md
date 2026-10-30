# G3 V3 — source-independent native constructor error feedback

Status: CANDIDATE protocol. No strict G3 closure can be established by this test.

## Boundaries

- Retain the sealed V2 Go AST type planner and its source SHA binding without modification.
- The V3 bridge may inspect only the V2 candidate expression, a reflected public configuration struct, and native constructor error strings. It may never use target-specific identifiers in its implementation.
- An error may suggest only an *exact public field name*. Prefer the longest matching eligible name; ties are UNKNOWN. Mutable fields: exported, settable integer/unsigned/float/bool fields. Try positive numeric values `1`, `16`, `256`; false boolean becomes true. Bound attempts by 12; no inferred field name or unsupported value means UNKNOWN.
- Constructor retry and reflection are mechanical runtime-admission tests, **not** proofs of semantics, safe external effects, independently invented operators, or future-relative equivalence.
- Any target read, workflow repair, or config-rule expansion after a failure is post-hoc and cannot count as an untouched cold result on that target.
- Required tests: named multiple-constraint native success; name collision longest-match success; opaque error abstention. Compare no-repair V2 on same fixtures.
- Upon fixture green, freeze V3 bridge and planner byte-for-byte. Then execute against an unopened metadata-selected rank-4 Go module on an isolated owned branch, with fair baseline and replay if a usable behavioral probe emerges. `STRICT_G3=UNKNOWN` regardless of native constructor status.

## Frozen status vocabulary

- `CONSTRUCTED_NONNIL_WITH_HINT_REPAIRS`: bounded native viability, not semantic capability.
- `UNKNOWN_RUNTIME_HINT_UNMATCHED`: no admissible exact field-name hint.
- `UNKNOWN_RUNTIME_REPAIR_EXHAUSTED`: budget or value ladder exhausted.
- `UNKNOWN_NATIVE_CONSTRUCTION`: compilation or source-native runtime failure.
- `STRICT_G3=UNKNOWN`: invention not yet distinguished from fair manual baseline.
