# Contributing to Nucleus

Small reproductions and narrowly scoped changes are welcome.

## Reporting a checker result

Include the exact Nucleus commit, Rust version, launch command, input format,
raw exit code and stderr. Supply the smallest export that demonstrates the
behavior, together with its SHA-256 hash and the expected typing or reduction
rule. Distinguish an incorrect decision from an unsupported input or timeout.

Avoid changing expected outcomes simply to make a test pass. If the intended
semantics are unresolved, preserve the case as UNKNOWN and describe the open
obligation.

## Changing the checker

1. Reduce the failing or declined input to a consequential regression case.
2. Explain the source typing or conversion rule that authorizes the change.
3. Add a positive control and an adversarial variant when a new admission
   rule could also admit an invalid export.
4. Run the Rust and Python checks described in the README. Replay the relevant
   frozen corpus before claiming that established decisions are preserved.
5. Record input identity, configuration and the exact verification boundary.

The initial `evidence/source-import-20261126.json` manifest deliberately binds
the runtime to its qualified source snapshot. A future implementation change
must update that baseline with corresponding qualification evidence.

Runtime decisions must not depend on fixture names, known input hashes,
expected test outcomes or calls to a competing checker. These may be used by
external qualification tools to bind evidence to inputs.

## Historical experiments

The source import retains earlier experiments and negative results. Some
historical scripts reference the original research repository's sibling
directories or Actions artifacts. Those dependencies remain documented in
[source provenance](docs/PROVENANCE.md); they are not required to build or run
Nucleus.

This project is experimental. A passing test suite establishes its recorded
test boundary, not universal soundness or complete Lean support.
