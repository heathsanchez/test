# C135 — N7 checked recursor trial diverges by route (WARRANTED_BOUNDED)

Green native workflow:
https://github.com/heathsanchez/test/actions/runs/43491083743
Artifact `14068773423`; ZIP SHA256
`5b45fba3d762b8f057974ecbe852c82731f06f419af85ede89c1889688f02408`.
Same frozen original N7 and immutable source SHA256
`abce636f6a7dd529c0dc6bbad8e7c8e2eaecfdda0d04c191d7f868e3a4468d35`.
Same two experimental flags, same exact second C133 captured conversion.
Observer OFF/ON stdout and verdict remained equal per budget. C105-derived
surrogate, not recovered C124/C125b.

Source `NameId(147)` recursor with five applied arguments was **checked** at:

| Initial test budget | Owner outcome | One-step probe | One-step result |
|---|---|---:|---|
| 65,536 | UNKNOWN | 253 | UNKNOWN `nested-recursor-iota-budget` |
| 65,536 | UNKNOWN | 32,625 | UNKNOWN `nested-replay-key-work` |
| 14,155,776 | PROVEN | 253 | UNKNOWN `nested-recursor-iota-budget` |

The candidate's trial is local: the probe is reserved from the owner
comparison and the observer records its real result without modifying it.
There is **no large one-step qualified-recursion trial** in the observed
successful high-budget owner. Consequently, C134's hypothesis that the high
budget merely finishes the same expensive one-step trial is **REJECTED**.
The high-budget owner must follow a different positive comparison path,
possibly at an earlier inference, checked proof, source-support, congruence,
or exposure stage. Its exact sufficient rule is not yet identified.

Next cheapest decisive experiment C136: read-only owner-scoped event markers
at the earlier positive conversion rules, without transporting a success
between captured environments. Do not promote N7 or modify kernel rules.
