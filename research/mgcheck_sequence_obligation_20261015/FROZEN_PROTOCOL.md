# Frozen scientific gate — source-bound sequence obligations and native future separators

**Date:** 2026-10-15 NZDT. **Status at freeze:** CANDIDATE / NOT YET EXECUTED.

## Exact original sources (public metadata examined; implementations not yet examined)

- Development: sloria/TextBlob original PR #603, immutable predecessor e8401fa714b33157c4fa8e2e9233d9fec6cb00ef, contributor revision c0f27915bb25ece9fec6ef6ecea043bf04d6402b. PR title/body disclose WordList insertion/slice replacement issues.
- Source-distinct transfer: mahmoud/boltons original PR #514, predecessor 961dcff3f42e73b245aef65e377fe82763b257bb, contributor revision d574813837f830fd59a2653213cc8f5f8bfc1a86. PR title/body disclose BarrelList deletion issues. This repository appeared in previous research for a DIFFERENT class (IndexedSet), so transfer is new semantic source, NOT wholly unseen repository.

The real original author patches/test files MUST NOT be inspected or copied before the frozen discovery method is committed. Target selector gets only repository+SHAs and changed-source API AST, NOT manually specified target class, function, operation, test, input or expected repaired code. Titles/body have already contaminated topic selection; claim is mechanism transfer, not unknown bug discovery.

## Independent normative contracts

1. Python list / mutable sequence behavior: for a documented list-compatible sequence, performing delete(index or slice) on a source-native collection and builtin list with the same initial visible values must produce equal visible sequences, and both should preserve state on errors where the builtin does. The builtin list is an implementation-independent executable oracle for list semantics.
2. Source-native action substitution: if a public mutable sequence provides BOTH append(value) and insert(index,value), then appending x and inserting x at len(sequence) should be observationally equivalent on the same fresh state. This is a standard list law grounded independently of a contributor's patch, not an arbitrary type-consistency guess. Compare not only values but item runtime types and available **public future operations** (a method that is public and callable without extra arguments) when they can be safely observed without external services.
3. If API documentation does not establish list compatibility or a substitution's preconditions fail, return UNKNOWN rather than asserting a bug.

## Constructed executable verification program

Generic human-authored meta-language contains types: constructor(input sequence), call(public source method,args), read(iterator values, element type, len), public future(no extra required arguments), and independent builtin-list operation reference. The system must infer which operation and observer to synthesize from source AST, method signatures and normative contracts. It must enumerate distinct inputs including strings, ints, slice bounds with None/negative/positive/steps and mutation sequences. Every qualified candidate must be an actual original **native Python** execution with original source SHA verified.

- No target function names, class names or tests embedded in code.
- Exhaust finite declared grammar, output minimum native separating program by count/cost, preserve all consistent controls.
- On development source, acquire a new executable observer *program* (not a pre-authored test instance) from contract-aligned candidate language. Apply the SAME unchanged generator to transfer source.
- Physical absence of generated operation/observer => UNKNOWN_NO_TEST; incorrect source SHA => UNKNOWN_SOURCE_IDENTITY; missing or invalid contract => UNKNOWN_CONTRACT; compare old/head with distinct source exact identities.
- Source-native pristine original suite on both revisions plus (if generated patch attempted) replay and patch-removal only after qualification; source/test code changes isolated in ephemeral owned CI worktrees. No writes to upstream.
- A strong equal-information coding agent reviewer comparison should be performed IF an independently callable agent is available; otherwise mark NOT_RUN. A legitimate conventional comparator may use the same Python reference API and source AST with same budget, and any tie must be recorded. Never substitute a deliberately weak baseline to claim competitive superiority.
- L7 self-created grammar remains UNKNOWN: the typed meta-language is human designed; choosing/composing an executable observer program is narrower capability.

## Stop conditions

Nonexistent public contract, native import or test failure, degenerate "no test executed" passes, changed-source identity mismatch, semantic false assertion, target-specific human adaptation, or newly introduced unrelated violations => UNKNOWN or REJECTED. Do not write an upstream comment, PR, merge, deploy, install App, invoke Gmail or Render. Original contribution authors remain credited; no new unknown upstream bug or general safe-to-merge claim.
