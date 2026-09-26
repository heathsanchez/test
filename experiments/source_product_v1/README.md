# Universal source-product normalization V1

## Current qualification

The all-depth source-product representation is Lean-checked, but it does **not**
prove Collatz. The decisive follow-up theorem is now also checked:

    KernelEmpty ZeroTailLive Next
      ↔ (forall n, 0 < n -> CollatzGood n).

So zero-tail kernel emptiness is not a smaller missing lemma. It is exactly the
positive Collatz termination theorem in the normalized presentation.

The red/green regression was explicit: run 36209985829 failed because the
equivalence theorem did not exist; commit 88f1e1e76747c05faa247352ad2c9869d05032af
then supplied the converse and run 36210081232 passed. The green run used pinned
Lean 4.35.0-rc2, checked the full existing kernel, SourceProduct,
SourceProductAffine, SourceProductZeroTail, the positive-domain regression and
the new equivalence regression, and passed all 8 independent Python replay
families. Artifact 10895670426 has GitHub-reported digest
sha256:fe6a5757b2f5442ede47b7fb53b191abab6c06a91cc7483a1f85bd0dfa8767ca.

## Exact product

For every positive source n, every finite depth k, actual odd-step count q and
endpoint y=T^k(n), the canonical state satisfies

    D = 2^k, A = 3^q,
    n = r + D*u, 0 <= r < D,
    y = d + A*u, 0 <= d < A,
    D*d = A*r + B_k.

Hence floor(n/2^k) = floor(y/3^q) = u. The source is fixed throughout.
The endpoint successor reconstructed from the product is exactly T(y), and the
odd count and affine intercept agree with independently accumulated orbit data.
These are arbitrary-depth Lean inductions, not finite-horizon extrapolations.

## Minimal-positive-bad bridge

PositiveBad(n) means n>0 and n does not reach {1,2}. A hypothetical minimal
positive bad source gives a nonempty post-fixed Live path at all depths, with no
terminal exit, no positive endpoint below the ORIGINAL source, and no merge
with a smaller positive source. Minimality is never transferred to a later
endpoint. The positive guard is necessary because zero is not CollatzGood.

## Why tail exhaustion does not finish the proof

The common tail strictly decreases while positive and remains zero afterward.
At zero tail, r=n and d=y, but y continues under the original Collatz map.
Source 27, for example, has tail zero at depths 5 and 6 while the endpoints are
71 and 107. These numerical states are not asserted to satisfy the full Live
predicate; they demonstrate only that tail exhaustion is not termination.

SourceProductZeroTail now proves both directions. Zero-tail kernel emptiness
implies Collatz through the minimal-bad bridge; conversely, assuming all
positive sources are CollatzGood rules out every post-fixed zero-tail Live set
because successor closure would eventually contain a terminal state, contrary
to Live. Therefore this residual is an exact reformulation, not a new rank.

## Remaining research obligation

The only potentially consequential route retained here is
COMPACT_FAREY_ADMISSION_AND_RANK: prove an all-depth protected projection of
the actual source-product/Farey continuation system, including source-relative
exit semantics, and independently prove its post-fixed kernel empty (for
example with an earned well-founded rank).

The existing Farey evidence is still bounded to the first two certified rungs
and Q2 depth <=14, with the second rung conditional on lower closure. It cannot
be promoted to universal quotient coverage. See residual.json.

## Reproduction

    lake build CollatzFinal
    lake env lean -DautoImplicit=false -o .lake/build/lib/lean/Collatz/SourceProduct.olean formal/Collatz/SourceProduct.lean
    lake env lean -DautoImplicit=false formal/Collatz/NormalizationRegression.lean
    lake env lean -DautoImplicit=false formal/Collatz/SourceProductAffine.lean
    lake env lean -DautoImplicit=false -o .lake/build/lib/lean/Collatz/SourceProductZeroTail.olean formal/Collatz/SourceProductZeroTail.lean
    lake env lean -DautoImplicit=false formal/Collatz/ZeroTailEquivalenceRegression.lean
    python -m unittest discover -s experiments/source_product_v1 -v

No default branch is changed by this development.
