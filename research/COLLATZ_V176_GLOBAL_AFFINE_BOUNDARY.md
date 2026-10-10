# V176 — the exact global odd-affine boundary is indispensable

**11 October 2026 NZ · WARRANTED_FORMAL_NEGATIVE_SEPARATOR, NOT COLLATZ QED**

## Qualified evidence

- [SUCCESS #38092315302](https://github.com/heathsanchez/test/actions/runs/38092315302) — exact head [270b594ad39bbeb6d55bb117488f5775c28a5135](https://github.com/heathsanchez/test/commit/270b594ad39bbeb6d55bb117488f5775c28a5135), all three independently scoped jobs passed. The new formal theorem source is [HiddenDefectStructuralSeparator.lean](https://github.com/heathsanchez/test/blob/270b594ad39bbeb6d55bb117488f5775c28a5135/formal/Collatz/HiddenDefectStructuralSeparator.lean), pinned Lean 4.35.0-rc2, standard permitted foundational axioms only, no sorryAx.
- Baseline [V174 universal finite-audit no-go SUCCESS #38091793892](https://github.com/heathsanchez/test/actions/runs/38091793892).
- V171 fixed-source one-arrow comparator [SUCCESS #38089579931](https://github.com/heathsanchez/test/actions/runs/38089579931).

## Exact all-finite-bounds adversary

For any finite source cutoff X and clock cap H choose

    a(X,H) = 6 * 2^H * (X+1) + 5.

Set S(n)=T(n) for every n other than a; set S(a)=a. Since T^t(n) <= 2^t n <= 2^H(X+1) < a for all n<X and t<=H, S^t(n)=T^t(n) for every audited original source-clock pair.

Lean additionally verifies the following UNIVERSAL, not just sampled, statements for this synthetic S:
- S(2u)=u for every u and S(odd u)≡2 (mod 3);
- for every original n and every k, 3 divides S^k(n) iff 3*2^k divides n;
- any future-invariant label f(S(n))=f(n) that is periodic modulo ANY positive fixed M is constant on all positive sources (by reconstructing the missing f(T(a))=f(a) relation from the unaffected odd source a+2M and V159's true-map modular collapse);
- a is a positive fixed point, disjoint from genuine preserved 1↔2.
The map S is NOT real Collatz and is NOT a counterexample to the actual conjecture.

**Why all-source affine law is a decisive discriminator:** a is odd. For the true T,

    T(a+2) = T(a)+3.

For S, the left side remains T(a+2), but S(a)+3=a+3. Since T(a)>a, this exact one-step affine law FAILS at a. Thus a proof of convergence from only (finite observations + even halving + all-depth ternary sieve + no periodic invariant label) is UNSOUND; it would falsely certify S. Any successful true-map proof must use an additional global source-sensitive arithmetic statement, such as the precise odd intercept at ALL sources, not just almost everywhere.

## What this does not settle

This theorem does not produce the critical, missing all-scale arithmetic inequality. It does not show that full exact +1 arithmetic plus the established invariants forces single future-class connectivity; that is still equivalent to resolving the central open obstruction.

The currently smallest conditional finish line remains the **sparse second-macroscopic-component criterion** in V170/V171, with authentic original source clocks, effective cutoff H(k)=8k, and the external timed targetwise predecessor-density theorem as a separately unimported premise. The conditional Lean bridge, full finite-clock graph, V172 height-only witness, V173 one-arrow basin repair, and V174 source-cohort pilot remain individually scoped and warranted.

### Next cheapest consequential mathematical experiment

Analyze **source-height cross-component connection production** under EXACT +1, not general parity mixing:
- Fix a true source cutoff 2^k and clock H(k)=8k.
- For two distinct observed macroscopic future components, express candidate new-height shell connectors using the V160 actual affine source product and V149 exact guarded inverse grammar. Preserve each original source and both independent clocks.
- Attempt to prove a symbolic unbounded-shell connector/exclusion lemma, not merely a finite collision percentage. Test any candidate inequality on the S hidden-defect family, S5, G5, G7, and Mersenne corridors. The correct theorem must fail for these artificial adversaries at the precise absent arithmetic premise, and hold for real T based on the full +1 rule.

**Result:** V176 removes broad classes of invalid proof routes. The remaining arithmetic theorem has NOT been proved. GLOBAL COLLATZ UNKNOWN, NO QED.
