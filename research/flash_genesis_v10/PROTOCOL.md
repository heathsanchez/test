# FLASH Genesis V10 — prospective independence-critic transfer

Date: 2026-10-12 NZDT. Previous negative: V9 syntactic function-head retention yielded no acquisition-check saving (15 cold = 15 retained on unique-count/max, protected 8/8). V10 changes the hypothesis and *does not supersede that negative*.

## Objective
Test whether a system given (1) two source repairs and (2) a generic **typed, designer-supplied** independence oracle can **synthesize a source-level repair-generation rule** that transfers to source-distinct matroid families, rather than merely memorizing repaired expressions. Test the exact boundary and avoid attributing a generic greedy algorithm to new logic or unrestricted genesis.

## Source specification before protected read
Source independence systems: a partition-matroid of repeated labels (unique-count) and a GF(2) represented vector matroid (linear-rank). Each source instance is a finite labeled ground set, with is_independent(mask) and a source rank oracle computed independently by exhaustive subset search. The incumbent count-all program demonstrably fails on dependent sets. Candidate repair programs are compiled from a finite typed meta-grammar over loop accumulator, candidate element, union/inclusion operations and the same independence oracle. Do not provide the target source expression as a preferred candidate, fixed rule, or hardcoded patch.

## Protected specification (unseen when selecting rule)
Freeze independent instances and seeds in protected_oracles.py *before* authoring synthesis implementation: graph forest/graphic matroid, uniform capacity, partition, GF(3) vector representation, transversal matching, plus a mixed direct-sum matroid. Include a hereditary **nonmatroid** knapsack countercontrol where exchange fails and a greedy order returns a nonmaximum result. The protected implementation does not expose specialized rank formulas to the synthesizer; only the generic is_independent interface is available at application time. Candidate law is frozen before protected cases are evaluated.

## Warrant requirements
- Source old-language obstruction witnessed on each family and source complete-within-grammar check.
- Candidate rule induced/selected by source tests, serialized, freshly reloaded, and applied with zero subsequent synthesis or human repair to protected instances.
- Independent exhaustive matroid axioms where n<=8 (hereditary and exchange), plus brute-force optimal rank for all subsets and deterministic order tests; any invalid axiom → fail closed/UNKNOWN, preserving counterexample.
- Causal ablation without learned rule fails on protected dependent examples.
- Compare to full-source informed stateless matroid greedy, exhaustive subset solver, and old count-all. A matched stateless greedy will tie output and oracle calls. Count synthesis evaluations, source oracle calls, protective axiom certification, protected inference oracle calls, and persist/reload overhead as separate metrics. Do not conflate relative improvement over exponential brute force with a strict win over an informed strong stateless comparator.
- Deliberate faulty policy mutation kill, and test order permutations.
- Do not claim autonomy beyond the typed grammar and pre-supplied independence oracle, new theorem beyond elementary matroid greedy law, quantum physics, or universal developmental fixed point.
- Exact GitHub Actions test on frozen source commit and artifact replay required before promoting beyond LOCAL.
