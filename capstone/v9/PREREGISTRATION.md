# V9 frozen induction-critic experiment protocol (pre-generator)

The full corpus, family labels and negative controls are fixed in `frozen_cases.json` in this commit, before any V9 generator code exists on this branch. Development is limited to orbit_nat_dev and foldl_append_dev. Four structurally varied families are held out; the two invalid controls and one already-valid control must not be spuriously promoted.

## Decisive claims

1. Compile unmodified proof attempts in pinned Lean 4.24.0 and retain actual diagnostics. A script that reads only names without invoking Lean is not failure-driven.
2. Construct generalization-binder policies from a small, declared program grammar, evaluate only on development tasks, freeze the selected policy identifier and its checksum **before** holdout evaluation.
3. Evaluate the selected policy on every held-out source without modifying it in response to heldout results. Each admission must be a Lean-accepted complete proof, with no `sorry`, `admit` or untrusted axioms.
4. Negative controls: already-valid proof must remain unchanged; invalid theorem attempts must remain unresolved after candidate search, not be described as refuted simply because tactics fail.
5. Comparators at the same source revision and verifier: unchanged baseline, ordinary induction with `simp_all` or `aesop`, and a stronger enumeration of all available generalized binders. Report compiler invocations and coarse wall time, including failed attempts and selection training cost.
6. Induction generalization is existing Lean functionality; no claim of invented logical rule, unrestricted proof-critic invention, formal old-grammar impossibility or advantage over an equally informed strong binder-search solver.

## Promotion

WARRANTED_BOUNDED_FAILURE_DRIVEN_GENERALIZATION requires: source freeze lineage, failures actually observed, selected rule frozen before heldouts, multiple accepted proofs, no false promotion on controls, ablation and strong-comparator accounting, and green pinned Lean CI. Otherwise record CANDIDATE/REJECTED/UNKNOWN explicitly. Do not merge with production, publish broad claims, or alter unrelated research branches.

## V9b apparatus correction and lineage (frozen before generator)

The first V9 qualification at [run 38231371530](https://github.com/heathsanchez/test/actions/runs/38231371530) failed **before the holdouts were opened**: the development List-fold proof already compiled under the old binder order, so it was not a genuine repair problem. V9b reorders that theorem's binder declaration to test a genuinely failed induction hypothesis. The earlier source and failed run remain recorded. This is an apparatus correction, not evidence of scientific success.

The earlier workflow also ignored `LEAN_TOOLCHAIN` and reported Lean 4.34.1. V9b MUST set `ELAN_TOOLCHAIN=leanprover/lean4:v4.24.0`, verify `lean --version` contains `4.24.0`, and assert that the same toolchain is used for every repair and baseline subprocess. Every holdout retains its previously frozen bytes. The new generator source is absent from the frozen parent commit and may only be added in a later commit.
