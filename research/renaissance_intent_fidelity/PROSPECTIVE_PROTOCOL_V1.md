# Prospective mathematical-intent fidelity protocol v1 — frozen before outcomes

## Question
Does a source-independent comparison of independently specified mathematical requirements and Lean formalizations identify wrong-but-provable claims, while accepting equivalent formulations?

## Roles and independence
Source statement authority: publicly known mathematical definitions or theorem statements, transcribed with citations and a source pin. The source statement must be frozen BEFORE candidate formalization outcomes are inspected.
Formalization candidate: either an AI-generated candidate with model/prompt/seed pinned, or a separately authored controlled mutant clearly marked as such.
Oracle: independent mathematician adjudication, with documented ambiguity/UNKNOWN. A hand-authored reference predicate is *not* an independent oracle.
Native authority: exact Lean+Mathlib toolchain, original proof check and axiom report.
Comparators: (1) kernel-only checking; (2) equally informed conventional semantic review, with all source statements, candidate formalizations, proofs, and definitions. Do not claim improvement over (2) without blind and cost-matched results.

## Frozen evaluation
Use a new source not used in the existing Euclid example. Preselect a family of at least 8 claims before opening candidate outcomes; include quantifier, hypothesis, domain and harmless rewrite changes. Avoid using outcomes to select which examples count.
Classifications: FAITHFUL, WRONG_MEANING, UNKNOWN. Fail closed when source intent cannot be established independently.
Score false acceptance, false rejection, unknown rate, coverage, reviewer time and total computational cost.
Test causal withdrawal/restoration only on claims whose source/parent evidence is pinned; unaffected descendants must remain warranted.
No changes to method after held-out reveal; any correction starts a new preregistered generation.
No submission claim or automated source fidelity until the independent oracle and native proof gate both pass.

## Existing calibration only
Euclid IX.20: infinitude of primes versus existence of a prime; both provable, latter too weak. GitHub Actions run 39207073502 validates Lean and Mathlib compilation, NOT automatic intent adjudication.
Synthetic Fin4 and 64-state dependency audit are calibration only, NOT held-out data.

## Stop conditions
If no independently frozen source interpretation exists, return UNKNOWN. If no equally informed reviewer comparator is measured, comparative advantage UNKNOWN. If native Lean fails, preserve RED; do not call scientific hypothesis false.
