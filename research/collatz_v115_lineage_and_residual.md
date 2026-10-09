# V115 — parity collision reduces depth-specific reverse words to one source-attached law

**Status:** CANDIDATE_FORMAL, local exact-affine regressions passed; hosted Lean qualification not yet inspected. **Global Collatz UNKNOWN — NO QED.**

## Protected consequence and objective

For every positive original source `n>1`, the V66 quotient requires an actual `p` with `0<p<n` whose shortcut orbit coalesces with that of `n`. Endpoint future-equivalence without the strict original-source guard is circular, as V111's rejected policy showed.

## Reconciled lineage (do not double-count)

- V110: 8,788,896/8,957,952 bounded CRT source-family certificates; 169,056 UNKNOWN.
- V111: preferred endpoint q7 witness alone earns zero new mergers; rejected mechanism, not an all-word impossibility theorem.
- **Wider parallel V112 branch** `collatz-v111-crt-guarded-mixed-v112`, 12-step reverse search: **4,617 NEW** source-family certificates in 14 prefix/word types; **164,439 UNKNOWN**. Independently reconstructed all 14 prefix/word counts with a separate symbolic enumeration.
- Narrower V112: 1,701 of those 4,617 using ten-step reverse words.
- V113: compressed the 1,701 into three parametric exact congruence laws, rather than new coverage. Parallel V113 branch `collatz-v112-three-word-quotient-v113` independently records the same compression. Avoid duplicate promotion.
- V114: nine additional length-12 congruence laws, another 1,296 of the same **4,617** (not additive to that wider count). Branch `collatz-v113-nine-congruence-laws-v114`.
- The **remaining 1,620** of those 4,617 split into exact templates `(j=5, EEOOOOEOOOO):837` and `(j=6, EEOOOOOEOOOO):783`. Both share the same source transformation as the earlier `(j=4, EEOOOEOOOO):837`.

## Stronger structural compression

For the shortcut map `T(n)=n/2` if even, `T(n)=(3n+1)/2` if odd, define `F(n)=3n+2`.

**Law 1 — universal source-attached six-step predecessor (simple exact arithmetic):**

For every natural `q`, `n=81q+60`, `p=64q+47` satisfy `0<p<n` and

`T^6(p)=3n+2=F(n)`.

The full arithmetic sequence is

`64q+47 → 96q+71 → 144q+107 → 216q+161 → 324q+242 → 162q+121 → 243q+182`.

**Law 2 — parity transport and critical-pair collision:**

- If `x` is odd, `T(F(x))=F(T(x))`.
- If `x` is even and `T(x)` is odd, then `T^2(F(x))=T^2(x)`.
- Hence if `n` starts with `k` odd shortcut steps, followed by an even step and then an odd step (symbolic word `1^k 0 1`), `T^(k+2)(F(n))=T^(k+2)(n)`.

Combining both yields, for every `q,k` satisfying that exact initial parity-word hypothesis,

`T^(k+2)(81q+60)=T^(k+8)(64q+47)`, with `64q+47<81q+60`.

This is a **variable-depth** source-merger rule, not merely fixed j=4,5,6 examples. Regression checks with independently constructed exact dyadic/CRT cylinders covered k=0..40, including q-offsets 0,1,7; symbolic affine traces matched for all offsets in those finite families. The universal Lean theorem is candidate, not yet qualified.

## Durable source and formal boundary

Repository `heathsanchez/test`, branch `collatz-v114-parity-collision-bridge-v115`.

- [Lean universal theorem candidate](https://github.com/heathsanchez/test/blob/collatz-v114-parity-collision-bridge-v115/formal/Collatz/ParityCollisionBridge.lean)
- [Independent bounded regression](https://github.com/heathsanchez/test/blob/collatz-v114-parity-collision-bridge-v115/research/collatz_v115_parity_collision_probe.py)
- [Two-job Actions workflow](https://github.com/heathsanchez/test/actions/workflows/collatz-v115-parity-collision.yml)

A green hosted kernel/axiom check must be separately observed before promotion to WARRANTED_FORMAL. Likewise the 4,617 individual V112 witnesses remain bounded executable rather than individually kernel-reified.

## What the theorem does *not* supply

It does **not** establish that every `n≡60 mod81` has an initial `1^k 0 1` parity pattern. Sources with a longer first even run, or other source congruence classes, remain outside this rule. It does not prove every natural source has a coalescent, exclude nonterminal cycles, or transform an unbounded 2-adic parity branch into a positive-natural counterexample.

## Highest-leverage genuine residual

Use the V95 source-attached affine pullback and V103 three-way actual stream classification to attempt a **fixed-original-source** finite-centre precision theorem on a hypothetical least positive bad source, or derive an explicit source-attached coalescence certificate. The existing ROS finite-centre synthesis emphasizes the essential distinction: arbitrarily high endpoint divisibility is not a bounded finite family of congruences on the original source. If the finite-centre hypothesis fails on a genuine changing-centre / high-order-cancellation example, reject it rather than claiming global closure.

This new F-transport law is a reusable merger-generation capability, not a universal source bar.
