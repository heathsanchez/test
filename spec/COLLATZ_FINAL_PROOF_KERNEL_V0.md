# Collatz Final Proof Kernel V0

Status: executable proof architecture. This file does **not** claim the Collatz theorem.

## Protected theorem

The final target is to eliminate every minimal bad positive integer. The trusted Lean kernel proves the generic reduction:

[
	ext{minimal bad}
	o
	ext{normalized residual state}
	o
	ext{nonempty post-fixed residual kernel}
	o
ot.
]

The computational side is not trusted for truth. It may only emit certificate objects for the obligations below.

## Four Collatz-specific obligations

1. **Minimal-bad normalization**

   Every minimal bad integer is represented by a normalized Farey/source↔endpoint state carrying the exact source constraints, affine source→endpoint relation, protected endpoint survivor language, and real-gap bound.

2. **Exit soundness**

   For a normalized state belonging to a minimal bad integer, each declared exit is genuinely fatal to minimal badness:
   - direct descent;
   - lower merge to a smaller positive source with a common future;
   - exact recurrence, after separately excluding every nontrivial recurrence compatible with the normalized constraints.

3. **Residual progress**

   Any normalized state with no exit has a lawful normalized successor. Later Farey rungs and longer coefficient-persistent continuations are represented only as successors in this relation, not as separate proofs.

4. **Kernel emptiness**

   The greatest post-fixed subset of the no-exit normalized continuation graph is empty.

## Certificate-facing implementation

The preferred executable certificate is a finite quotient graph with:

- canonical state IDs;
- exact source/endpoint constraints for every state;
- typed exit certificates;
- successor edges with preservation certificates;
- a natural-valued rank on every residual state, strictly decreasing on every residual edge.

A rank certificate is sufficient to prove kernel emptiness and is much smaller than replaying exploratory search in Lean.

If the normalized graph cannot be ranked, the compiler must emit the smallest directed residual cycle instead of weakening the theorem.

## Research-method boundary

The discovery stack may use SAT, BDDs, automata, exact arithmetic, Python, Rust, or LLM-proposed representations. None become authority by themselves.

The only promoted object is the smallest independently checked semantic consequence:

[
	ext{residual}
	o
	ext{candidate quotient/certificate}
	o
	ext{Lean check}
	o
	ext{promote/reject/UNKNOWN}
	o
	ext{reclose}.
]

This is the same Research OS law used across Nucleus, Metatron, MathGraph, ARC, SAIR and the preceding Collatz line.
