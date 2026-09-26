# Universal source-product normalization V1

## Scope

This work proves unrestricted, all-depth source-product normalization for the
shortcut Collatz map. It does **not** prove Collatz, a finite quotient, or
universal admission into the compact Farey survivor quotient previously tested
only on the first two certified rungs through Q2 depth 14.

The initial full qualification of SourceProduct, SourceProductAffine, the
positive-domain regression, and all eight Python test families passed at commit
`edea156efebd8e24e25e52037f9a860124abcf39`, run
https://github.com/heathsanchez/test/actions/runs/36209045391 .
The additional zero-tail reduction is included in the same branch's proof gate.
Inspect the workflow for the exact revision being used.

## Exact product and all-depth induction

For positive source n, depth k, actual odd-step count q, and y=T^k(n), the
canonical state has

    D = 2^k, A = 3^q,
    n = r + D*u, 0 <= r < D,
    y = d + A*u, 0 <= d < A,
    D*d = A*r + B_k.

Therefore floor(n/2^k) = floor(y/3^q) = u. The source is fixed throughout.
B_k is independently accumulated along the original orbit: an even step leaves
B unchanged, while an odd step replaces B by 3*B + 2^k.

To continue, let b=u mod 2 and v=d+A*b. Replace u by floor(u/2), r by r+D*b,
and D by 2*D. For even v, replace d by v/2 and keep A and B. For odd v, replace
d by (3*v+1)/2, A by 3*A, and B by 3*B+D. Since 0 <= v < 2*A, both cases
preserve the canonical residue bounds. The endpoint changes by exactly T.

These are arbitrary-depth inductions, not tests over a larger finite horizon.
The Python replay suite is an independent implementation check, not the
justification for the universal theorem.

## Counterexample and progress bridge

PositiveBad(n) means n>0 and n does not reach {1,2}. If n is a minimal positive
bad source, its full normalized trajectory is a nonempty post-fixed subset of
Live: every state is reachable, every successor exists, and no state has a
terminal exit, a positive endpoint below the ORIGINAL n, or a merge with a
positive source below the ORIGINAL n.

The positive guard matters: zero is not CollatzGood, so the old unguarded
minimal-bad predicate makes zero the least bad natural irrespective of the
positive Collatz question. NormalizationRegression proves this and checks the
correct positive-source bridge. The old generic definitions are preserved for
compatibility; the new Collatz bridge uses PositiveBad.

## Exact remaining subkernel

The common tail strictly decreases whenever it is positive and stays zero once
zero. Consequently, emptiness of the zero-tail live kernel implies emptiness
of the whole live kernel. SourceProductZeroTail proves this reduction using
post-fixed subsets and the existing natural-number rank theorem.

At tail zero, r=n and d=y. The next endpoint residue is exactly T(d). Thus the
zero tail does not remove the endpoint's remaining dynamics. For example, the
source 27 has tail zero at depths 5 and 6, while its endpoints are 71 and 107.
Those numerical states are NOT asserted to be fully Live: arbitrary lower
merge witnesses are excluded only under the hypothetical minimal-bad premise.

The conditional theorem `collatz_of_zero_tail_kernel_empty` deliberately keeps
`KernelEmpty ZeroTailLive Next` as a premise. No term proving that premise is
provided. Likewise, `collatz_of_ranked_simulation` is a checked interface, not
a supplied quotient or rank certificate. See residual.json for the open goals.

## Formal files

- formal/Collatz/SourceProduct.lean: canonical normalization, exact successor,
  common tail, positive minimal-source path, conditional kernel/rank closure.
- formal/Collatz/SourceProductAffine.lean: independent odd count, full affine
  orbit identity, and exact residue coupling.
- formal/Collatz/SourceProductZeroTail.lean: localization to the zero-tail live
  subkernel; global closure remains conditional on its emptiness.
- formal/Collatz/NormalizationRegression.lean: zero-domain regression and
  corrected positive-source lower-merge bridge.

The pinned toolchain is leanprover/lean4:v4.35.0-rc2, with Std and the existing
Collatz modules. The workflow prints theorem dependencies and rejects proof
placeholders. The checked normalizations use propext and Quot.sound; the
classical minimality/kernel bridge also uses Classical.choice.

## Reproduction

From the repository root at the intended immutable commit:

```sh
lake build CollatzFinal
lake env lean -DautoImplicit=false -o .lake/build/lib/lean/Collatz/SourceProduct.olean formal/Collatz/SourceProduct.lean
lake env lean -DautoImplicit=false formal/Collatz/NormalizationRegression.lean
lake env lean -DautoImplicit=false formal/Collatz/SourceProductAffine.lean
lake env lean -DautoImplicit=false formal/Collatz/SourceProductZeroTail.lean
python -m unittest discover -s experiments/source_product_v1 -v
python experiments/source_product_v1/source_product.py
```

The replay suite covers sources 1..1024 through 40 steps, every binary cylinder
through depth 10 with two positive translates, 32 seeded 72/128/256/512-bit
sources through 600 steps, and explicit negative controls for tail-only ranks
and unearned fixed near-return bounds. It includes exact all-odd prefixes.
No default branch was changed by this development.
