# Frozen algebraic-separator pilot — 18 October 2026

**Verdict: REJECTED as a competitive factoring shortcut on the declared synthetic heldout.** No new factoring algorithm, RSA-270 factor, GNFS improvement or general complexity result.

## Evidence authority and lineage

- [Original freeze](https://github.com/heathsanchez/test/commit/b01d6af55f4d3f0abda515e2927d6b14c902812b) — nine precommitted 60–76-bit semiprimes, three calibration/six heldout, factor-hash commitments and fixed budgets.
- [Implementation source](https://github.com/heathsanchez/test/commit/ecce586745bb99ce9a72e19701fb39697a4cd8aa) — committed before the heldout execution, with both proposed arms and actual mature controls.
- [Independent verifier](https://github.com/heathsanchez/test/commit/7f6986fccff3ba2014baf4b840fb5d857a925ac9) — written after the outcomes and checks products, SHA256 commitments, prime status, modular-square/gcd/idempotent witnesses and a tampered-witness control.
- [Independent Actions replay workflow](https://github.com/heathsanchez/test/commit/293c239c986715d2046d127423c3bd7d0e365b7f), archives source/results. Its GREEN run/artifact remains **NOT VERIFIED**; local results must not be promoted to independent CI.

## Methods and fair boundaries

A uses one-polynomial smooth-only relation collection with incremental GF(2) dependence and exact square-gcd checking. B adds identical residual-cofactor pairing up to 100000, a **known partial-relations technique**, not novel algebra. Both receive up to 60000 identical x^2-N candidate offsets and prime factor bound 1000. C is actually executed established SymPy 1.14 self-initializing quadratic sieve with partial relations and multiple polynomials (prime bound 2000, sieve interval 8000, seed 1234, process timeout 30 seconds). D contains fixed Pollard rho (200000 steps) and Fermat (60000 steps) controls. Candidate counters compare only A with B; compare C/D using success and observed end-to-end cost, recognizing different underlying operations. Inputs are deliberately synthetic, deterministic, and precommitted; they are not a claim of true external novelty.

## Full-budget local results

| Split | Smooth A | Paired B | Mature SIQS | Rho | Fermat |
|---|---:|---:|---:|---:|---:|
| Calibration 60/64/70 bits | 0/3 | 0/3 | 3/3 | 3/3 | 0/3 |
| Heldout 64/64/70/70/76/76 bits | 0/6 | **1/6** | **6/6** | 5/6 | 0/6 |

The one B success occurred on hold-64-b after **24003 polynomial candidates**. B acquired 43 smooth and 42 paired relations, reached GF(2) rank 84 and found one nontrivial dependency (41 rows), yielding an independently checked congruence of squares, a nontrivial idempotent, and the exact factor pair:

12,183,504,419,152,496,609 = 3,548,126,069 × 3,433,785,661.

Five other protected B cases retained between 10 and 51 relations, with **zero linear dependencies** despite factor bases of size 80–88. This localizes the obstruction for this bounded, naive one-polynomial approach to **creating sufficiently many independent smooth relations**, not checking the final witness. Established SIQS factored all six. Aggregate single-host wall time: A 2.34s with 0/6; B 2.13s with 1/6; SIQS end-to-end 1.65s with 6/6. These are descriptive measurements, not stable normalized hardware comparisons. Pollard rho succeeded 5/6. The candidate scientific advantage gate is **REJECTED_BOUNDED**.

The independent local verifier checked all nine factor-pair commitments and SIQS factorizations, the sole B square congruence and idempotent, and a tampered-certificate rejection. Python 3.13.5, SymPy 1.14.0. No source-level mathematical generalization to GNFS follows.

## Reproducible execution

Run the following commands with SymPy 1.14.0 installed:

    python research/algebraic_separator_20261018/experiment.py --split calibration
    python research/algebraic_separator_20261018/experiment.py --split heldout
    python research/algebraic_separator_20261018/verify_independent.py

The source automatically writes results_calibration.json, results_heldout.json, independent_verification.json; the Actions workflow archives raw evidence. The local Python experiment file and GitHub file have identical nonempty lines (252), with only three blank-line differences; the local protocol and GitHub JSON format differ slightly but all nine n/factor commitments and numerical budgets match. The local result hashes refer to the local protocol, not the GitHub blob.

## Causal lineage and next gate

Prior separate negative results remain in the [RSA DSP generator checkpoint](https://app.notion.com/p/3fc3e523d7ab8159a107fed8426ea75f): no shared factors across 56 published moduli, bounded raw-LCG checks, and zero RSA-270 simple power forms. Do not conflate those with this heldout method-comparison result.

**UNKNOWN:** new separator operation, competitiveness against GNFS on large numbers, original RSA generator entropy, RSA-270 factors. The next scientifically informative gate requires an independently sourced, untouched corpus and a mathematically specified *new operation that increases relation supply*, assessed at full end-to-end cost against mature, equally informed factoring baselines. Do not reopen exposed holdouts as fresh. No production or external-owner changes.
