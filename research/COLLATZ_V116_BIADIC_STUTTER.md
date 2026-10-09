# Collatz V116 — a parametric obstruction to bounded finite-biadic ranks

## Verdict
**Elementary exact theorem (mathematical proof below), executable regressions; Lean kernel status UNKNOWN. Global Collatz UNKNOWN.** This is a rigorous negative separator, not a proof of Collatz.

## The one finish-line bar, and why it is not yet a proof

For shortcut Collatz T, the universal source-capped ternary return statement is

> For each positive natural n>1, some actual forward iterate y=T^k(n)
> obeys y mod 3=2 and 2y-1<3n.

This is equivalent to Collatz, not a derived implication: if it holds, p=(2y-1)/3 is a positive odd integer less than n with T(p)=y, and strong induction finishes. Conversely, if Collatz holds, y=2 occurs and supplies the return.

The **missing ingredient** is a source-attached universal forcing principle, not merely a finite quotient rank or a reformulation of this quantified bar.

## Parametric no-go theorem

**Theorem.** For every d,q,L>=1 set M=2^d*3^q, K=d+q+L+1, and n=2^K-1>1. On the *actual* shortcut trajectory of this fixed positive source n, all L+1 consecutive endpoints T^j(n), q<=j<=q+L, have the same residue M-1 modulo M; throughout the entire initial interval 0<=j<=q+L, no source-capped ternary return occurs.

**Proof.** For each 0<=j<=K, the actual shortcut trace is exactly

`T^j(n)=3^j*2^(K-j)-1.`

Indeed the j-th value is odd when j<K, and its shortcut successor is the next displayed term. This proves the formula by induction, with no surrogate 2-adic orbit.

At j=0, `n=2^K-1` is not 2 mod 3 (it is 0 or 1). At each j>=1, the displayed term is 2 mod 3, but its values strictly increase from `T(n)=(3n+1)/2` while j<=K; therefore `2*T^j(n)-1>=3n`. So no source-capped ternary return occurs at any j<=K.

Finally for q<=j<=q+L, both j>=q and K-j>=d+1. Hence `T^j(n)+1=3^j*2^(K-j)` is divisible by 3^q and by 2^d. Those powers are coprime, so the endpoint is congruent to -1 mod M. The original source n is unchanged. There are L+1 such actual endpoints, hence L consecutive transitions inside the single observed source/endpoint residue pair. QED.

**Counterexample to any proposed rank:** if a proposed source/endpoint residue rank `rho(n mod M, endpoint mod M)` must strictly decrease on every actual transition not already certified by a source-capped return, it fails even between j=q and q+1. If it permits at most H successive nonprogress steps, choose L>H; this source contradicts that bounded-delay assertion. No fixed finite rank over just these residue coordinates can certify the universal bar via such a stepwise/bounded-delay rule.

**Scope.** This does NOT refute an unbounded-precision state (the 2-adic valuation of endpoint+1 decreases by one at each step of this corridor), a genuinely source-attached event with unbounded wait, a more expressive exact affine/source history, or the V82–V85 *conditional* macros. It refutes extrapolating their bounded finite ranks from a residue-only bounded-delay interface to all natural sources.

## Independently testable boundary

The standalone exact compiler `research/collatz_v116_biadic_stutter.py` replays the actual positive shortcut trace, each divisibility/congruence, the unchanged original-source cap, and `v2(endpoint+1)=K-j`. It includes representative tests at (d,q,L)=(12,7,100), the same biadic modulus M=8,957,952 used in V110/V112. This checks instances, not the universal theorem, whose symbolic mathematical proof is above.

## Evidence and lineage

- V83 rank 5 / 0 residual SCCs: warranted on a finite frozen old+fresh authority, *not* a universal macro-simulation theorem.
- V103 actual cycle/nonzero admitted return/unbounded anchor: warranted formal necessary alternatives, no exit proof.
- V106: both signs of actual admitted returns; rejects unrestricted monotone sign ranks.
- V111: no source-relative merger from 2,028,672 endpoint-only q7 presentations; quotient membership is not progress.
- V112: 4,617 additional source-guarded mixed CRT candidate mergers, still 164,439 unknown, not universally qualified.
- V115: arbitrary high endpoint +1 valuation does not imply a fixed finite integer source centre; no-exit-specific finite-centre bridge remains unknown.

**Highest-leverage next genuine experiment:** attempt an *unbounded* source-attached potential on the actual least-bad coherent stream (V103), with an independently checkable progress event. State the exact event-production lemma and test adverse changing-centre returns, sign reversals, and this all-ones corridor. Reject any candidate assuming a uniform finite waiting bound or a rank solely on M-residues.

No QED; global Collatz UNKNOWN.
