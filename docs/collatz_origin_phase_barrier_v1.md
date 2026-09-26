# Origin phase barrier V1

Parent: `heathsanchez/test:collatz-universal-source-product-v1@52175c9239cf63c806fc4f1ad4ff76a4f691508e` (V11).

Global Collatz: **UNKNOWN**. The V11 bounded canonical exclusion through depth 271782 is unchanged. This cycle tests the unbounded origin-count proof mechanism, not a larger finite source range.

Qualified implementation: `8c50a6cf6dc5e564b2bc92d536dba00b8a5e259a`; run `36229491205`, job `108369809394`, SUCCESS. Artifact `10901613257`, SHA-256 `e5952f42f9c1607bc427b327968021d66028f24634ec952ec7390a66272145eb`. Source-product regression run `36229491168` also passed. The four printed theorem dependencies contain only `propext` and `Quot.sound`.

## Result and exact scope

**Rejected:** closing the origin window by a translation-uniform upper bound obtained by discarding all Fourier phases. Even exact Fourier magnitudes cannot make such a valid bound smaller than one for a nonempty support and nonempty window.

**Not rejected:** the actual fixed-origin inequality, a phase-sensitive Fourier proof, an origin-sensitive carry argument, or any genuinely residual-preserving induction. Shifted supports below are controls, not alleged Collatz-legal supports.

The distinction matters to the revived P4--P8 lineage. The polynomial cap on a hypothetical bad source makes an origin estimate sufficient, but does not make a translation-uniform discrepancy/absolute-value majorant sufficient. The positive Fourier majorant can remain auxiliary; it cannot by itself supply this subunit count bound.

## 1. Elementary no-go theorem

Let A be a nonempty subset of Z/NZ and I a nonempty cyclic interval of width W. Put

    C_A(a) = |A intersect (a+I)|.

Any number U satisfying C_A(a)<=U for every translation a must satisfy U>=1. Choose one support point and translate I to contain it.

The Lean theorem `OriginPhaseBarrier.uniform_envelope_not_subunit` proves the integer-rational version: if Q*C_A(a)<=P at every a, then Q<=P. It holds for arbitrary list supports, so multiplicities do not cause an exception. `no_translation_uniform_subunit_bound` records the direct contradiction when P<Q.

This is not a claim that an origin window cannot be empty. It is a claim that a location-independent upper bound cannot certify its emptiness by becoming smaller than one.

## 2. Why this applies to phase-blind Fourier inversion

Use unnormalized transforms on Z/NZ:

    fhat(xi) = sum_x f(x) exp(-2*pi*i*xi*x/N).

Fourier inversion expresses each translated window count as the DC term plus the phase-dependent sum of nonzero frequencies. Taking absolute values term by term yields

    C_A(a) <= |A|*W/N + (1/N) sum_(xi!=0) |1_A_hat(xi)| |1_I_hat(xi)| = U.

The right side is independent of a. Therefore U>=1 by section 1. Replacing exact magnitudes by upper majorants can only increase U. Increasing numerical precision, frequency coverage, or the strength of a positive magnitude majorant does not remove this obstruction.

Equivalently, translation A->A+t multiplies each Fourier coefficient by a unit complex phase and preserves every magnitude. The target count in a fixed origin interval is not translation invariant. The full circular autocorrelation, and therefore all Fourier power coefficients, retain the same ambiguity.

This Fourier formula and its application are an elementary written argument. Complex Fourier analysis has not been newly formalized in Lean here; the generic combinatorial obstruction and the actual nonempty-source family have been.

## 3. Actual live Collatz supports are nonempty at every positive depth

For n_j=2^j-1 and 0<=k<=j,

    T^k(n_j) = 3^k * 2^(j-k) - 1,
    oddCount(n_j,k) = k.

Consequently 3^oddCount>=2^k at every such prefix: the source has no coefficient crossing through depth j.

`iter_odd_block` proves the more general exact formula

    T^k(2^k*a-1) = 3^k*a-1,  a>0.

`all_ones_no_coefficient_crossing` then proves the all-depth prefix statement. This is a different positive source at each positive depth. It is **not** a positive integer with an infinite all-odd trajectory and is **not** a counterexample to Collatz.

It supplies the nonempty-support hypothesis needed for the phase-blind no-go at every depth, including all depths beyond the analytic cutoff. The obstruction is therefore not merely a finite failed test.

## 4. Exact coefficient-sized witness for the proposed dyadic envelope

At j=333 and X=512, independent forward and backward exact dynamic programs agree on

    F_333 = 260078867390036221398561220601054468654692164639803459182799561454442032878319722731506262999.

The candidate expression is

    U_goal = 2 * 2^(6*j/125) * F_j * X / 2^j.

Its value is strictly below one. The script does not use floating-point logarithms; it checks

    2^(125*j) > 2^(125+6*j) * (F_j*X)^125.

All 256 odd positive sources below 512 cross by depth 59, so the actual origin count at depth333 is zero. Yet the actual support contains 2^333-1. Translating the support by 2 modulo 2^333 places a support point at 1, so the translated control has count at least one in the same origin window and has identical Fourier magnitudes.

Thus U_goal cannot be a translation-uniform bound at these parameters. The shifted control is not asserted to be the Collatz support. This is not a counterexample to the fixed-origin estimate or to its eventual polynomial-window version.

For every depth4..16, a second exact control enumerates the complete actual live support by source-product lifting and independently by forward trajectories. Its origin window [1,4) is empty, while the shift-by-two control contains one point there. Full integer circular autocorrelations agree in all 13 controls. Odd-count label multiplicities also agree. No numerical Fourier transform is used.

## 5. Verification and lineage

Reproduce with:

    python -S experiments/collatz_origin_phase_barrier_v1.py

The parent live-language helper is hash-locked. The experiment records all finite controls and its own SHA-256 `fceb547cc781492df5f7f962ab1f028b9bdcb0ee7cb23e7338058075a0540850`. The hosted workflow explicitly compiles SourceProduct, SourceProductAffine and OriginPhaseBarrier against the repository's pinned Lean toolchain, prints theorem axiom dependencies, and rejects proof placeholders and native-reduction trust extensions.

Boundary: exact Python finite counts and correlations; Lean all-depth combinatorial no-go and all-odd trajectory family; written Fourier application. The large depth333 language count is not a Lean-computed proof term. No new canonical M exclusion at unbounded depths, no universal origin estimate, and no global Collatz proof is claimed.

Failed run `36229413984` is retained: exact Python tests passed, but the first Lean script left the elementary goal `0 < 1 + windowCount ...` open. The qualified head discharges this explicitly with `omega`; no theorem statement was weakened.

This result constrains proof search rather than closing an additional source interval. Preserve all previous warranted and rejected results. In particular, it does not resurrect finite residue SCCs, static source admission, off-type P37 bookkeeping ranks, or an all-odd-prefix termination argument.
