# External MiniF2F exaptation protocol v1

## Purpose

Test the first external-validity separator after the bounded internal convergence programme: can a capability acquired and frozen for purpose A be requalified by a later externally selected theorem B, with the exact B unknown when the controller/parser/requalification mechanism is committed?

This protocol is deliberately narrow. It is **not** arbitrary MiniF2F theorem proving and does not claim that the adapter itself is discovered.

## External authority

- Repository: `google-deepmind/miniF2F`
- Pinned commit: `f0a20e14c1eeccd859d51bb4c2b3ee487889c303`
- Test split: `MiniF2F/Test.lean`
- Expected Git blob: `7d3a756cb3da856fc26096c8da440f086653cfc1`

The implementation is developed only against a validation-split example. The workflow acquires and freezes `K_A` before checking out the pinned external repository. The test-split bytes are therefore absent from the working directory at the source-freeze step.

This does not prove that no human has ever seen MiniF2F Test. It establishes a narrower provenance fact: the exact selected B/held-out pair is determined only after the frozen commit exists, using the platform-assigned GitHub Actions run ID.

## Precommitted admissible family

The parser accepts only theorem declarations of the exact form:

```lean
theorem NAME (x : ℝ) : POLY ≤ POLY := by
```

or the same with `≥`, where both expressions use only the single variable, rational/integer constants, `+ - * / ^` and parentheses. The normalized difference must be a globally nonnegative quadratic that the already learned `half_line_square` source can expose with power zero.

No hypothesis-bearing, multivariable, transcendental, `answer(...)`, set, absolute-value, quantified, or higher-language theorem is admitted to the candidate pool.

## Selection after freeze

Candidates are sorted by `(theorem_name, statement_sha256)`. The pool identity is hashed. The train index is selected from:

```text
sha256(freeze_sha : workflow_run_id : corpus_commit : test_blob : pool_digest)
```

A different digest-derived nonzero offset selects the held-out theorem.

The workflow run ID does not exist until after the freeze commit is pushed. Re-running the same commit is explicitly allowed to choose a different pair and must be reported as a separate administration.

## Required causal chain

```text
pre-external purpose A
    -> frozen K_A : half_line_square under its original ray contract
    -> externally selected B
    -> cold UNKNOWN
    -> typed GLOBAL_ROLE_REQUALIFICATION_REQUIRED residual
    -> K_B : all-real role requalification, exact dependency on K_A
    -> K_C : external global-quadratic program, exact dependency on K_B
    -> restart
    -> externally selected held-out theorem at acquisition budget 0
    -> execution K_C -> K_B -> K_A
```

`K_A` is not mutated and does not directly satisfy the external adapter contract. The requalification must independently verify that the source's power-zero square decomposition proves nonnegativity on all reals.

## Controls

The result must record:

- same-serialized-size sham `K_B`;
- wrong-direction adapter;
- matched fixed policy with B acquisition budget 2 and requalification disabled;
- removal of the frozen source executable identity;
- removal of an unrelated pre-frozen capability;
- ancestor revocation and descendant collapse;
- raw immutable history with inactive source at the same B budget;
- restoration of the same source identity, role and downstream held-out success;
- source-distinct direct discriminant/square verifier over both selected theorems.

## Allowed outcomes

The workflow itself can pass while the scientific outcome is `UNKNOWN`, provided provenance and fail-closed behavior are intact.

Possible outcomes are:

```text
VERIFIED_EXTERNALLY_SELECTED_EXAPTATION
UNKNOWN_EXTERNAL_CORPUS_INSUFFICIENT
UNKNOWN_EXTERNAL_DEVELOPMENT
```

A failure of provenance, source freeze, corpus identity, certificate replay, dependency lineage or causal controls is a workflow failure, not a scientific `UNKNOWN`.

## Claim if verified

> Within a precommitted one-variable global-quadratic family, an externally maintained MiniF2F test-split theorem and coefficient-distinct held-out theorem were selected only after the source/controller freeze; a previously learned ray-square capability did not directly solve B, was requalified under a new independently checked all-real role, enabled a dependent program, and was causally executed in zero-acquisition held-out success.

This is **externally selected bounded exaptation**, not unrestricted external development. The adapter, parser, admissible family and requalification operation remain supplied before selection, and the exact-rational external verifier is Python rather than Lean-verified.
