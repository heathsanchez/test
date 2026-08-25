# Palomar candidate audit

Date: 2026-08-26
Status: preparation only; do not submit until the candidate clears both the mathematical-interest and provenance/maintainer gates.

## Current Palomar constraints that matter

A normal submission should pin a public GitHub commit and provide an auditable `Challenge.lean`, matching `Solution.lean`, `comparator.json`, `formalization.yaml`, a Lean/Lake project, and a licence. Palomar mechanically checks Challenge/Solution alignment and replays exported proof terms with Lean and NanoDa. Its editorial floor also asks whether the result could plausibly warrant a research paper or serious research note and whether a credible research audience exists.

The Challenge-side trust surface is deliberately narrow, so a submission should not merely import a candidate-local theorem from another file and hide the mathematical statement there. The statement should be small enough to audit directly.

## Candidate A — generalized Law 43 term-definability theorem

Source evidence:
- upstream merged PR: teorth/equational_theories#1461
- theorem: `Equation43_termDefinableFrom_swapped_args`
- proof author on the merged PR: `heathsanchez`
- merge commit: `54edcda2f320cef0a241f8109fa164f901a69b87`

Mathematical content:

> For a two-variable magma law whose right-hand side is obtained by swapping the two variables in the left-hand side, every magma satisfying that law admits a term-defined commutative derived operation.

Why it is interesting:
- this is a structural universal-algebra statement, not one isolated implication;
- it explains a family of definability edges at once;
- the proof constructs the derived operation explicitly from the law term;
- it lives inside the Equational Theories research programme rather than being a benchmark-only fact.

Palomar risk:
- the substantive formalization currently lives upstream in `teorth/equational_theories`;
- Palomar requires the submitter to be a responsible author/maintainer of the substantive formalization or to have approval from one;
- therefore we should not submit a thin wrapper around the upstream project without maintainer approval.

Decision: **strongest mathematical candidate, but provenance/approval must be resolved before submission.**

## Candidate B — closure-relative schema identity / no-separator theorem

Source evidence:
- `experiments/minimal_core_schema_isomorphism_v8.py`
- exact table/relation map over all 16 Boolean binary functions;
- exhaustive 65,536 behavior-only continuations;
- zero separators under the code↔mask extensional bijection;
- positive control separates a genuinely non-isomorphic parity/pair representation after continuation expansion.

Potential formal statement:

> If two finite schemas are pointwise extensionally identical under a bijection of their carriers, then every continuation that factors only through their complete extensional behavior is invariant under that bijection. Conversely, adding access to latent structure can separate non-isomorphic schemas that were equivalent under the restricted continuation class.

Strength:
- completely owned in this repository;
- clean connection to representation identity and quotienting;
- can be made self-contained and independently checked.

Risk:
- the abstract invariance lemma is mathematically elementary if stated too generally;
- the exhaustive Boolean instance by itself may fall below Palomar's research-interest floor unless tied to a stronger theorem or research note.

Decision: **eligible provenance, but needs theorem sharpening before packaging.**

## Candidate C — Stage-2 equational-theory closure/grammar obstruction

Source evidence:
- `heathsanchez/equational-theories-lean-stage2`
- order-5 residual work around problem 0014 and subsequent closure/grammar experiments.

Potential content:
- a formally stated non-reachability / closure obstruction for a bounded operator family;
- ideally paired with a positive theorem showing what representation expansion repairs the obstruction.

Strength:
- closest to the current SAIR mathematical programme;
- obstruction + repair is a more substantial research story than a solver score.

Risk:
- current evidence is largely experimental/search evidence and workflow artifacts rather than a single compact Lean theorem;
- bounded-search negatives need careful formalization so the claim is exactly what was exhausted, not stronger.

Decision: **potentially the best original Palomar result, but not submission-ready yet.**

## Working order

1. Treat Candidate A as the fastest high-quality route if upstream approval is available.
2. In parallel, sharpen Candidate C into one auditable theorem with a positive/negative pair.
3. Use Candidate B only if the representation theorem can be strengthened beyond the tautological extensional-invariance core.

## Candidate A packaging target

Prepare a standalone statement surface rather than exposing the full upstream file. The target should have:

- `Challenge.lean`: only the definitions needed to state term-definability and the generalized swapped-arguments theorem, with mathematical docstrings;
- `Solution.lean`: the proof, adapted without `sorry`, `native_decide`, or nonstandard axioms;
- `comparator.json`: compare exactly the public theorem(s);
- `formalization.yaml`: explicitly credit the Equational Theories Project, the existing upstream theorem context, the proof contribution, AI assistance where applicable, and the merged PR;
- a pinned supported Lean release;
- a committed manifest and reproducible CI.

Do not describe this as a novel theorem unless provenance research supports that claim. The strongest accurate framing is a machine-checked structural term-definability result contributed to the Equational Theories Project.

## Immediate next technical step

Build a minimal standalone Lean formalization of Candidate A on this branch, then run it in GitHub Actions. If the standalone statement becomes awkward or imports too much project-specific machinery, stop and switch to Candidate C rather than hiding complexity behind a thin wrapper.
